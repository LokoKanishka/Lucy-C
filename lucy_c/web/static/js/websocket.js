// WebSocket connection handler
const socket = io();

socket.on('connect', () => {
  console.log('Connected to Lucy-C server');
  updateStatus('Connected', 'success');
});

socket.on('disconnect', () => {
  console.log('Disconnected from server');
  updateStatus('Disconnected', 'error');
});

socket.on('error', (data) => {
  console.error('Socket error:', data);
  updateStatus(data.message || 'Error', 'error');
});

socket.on('status', (data) => {
  updateStatus(data.message, data.type || 'info');
});

socket.on('audio', (data) => {
  const autoSpeak = document.getElementById('auto-speak-toggle');
  if (autoSpeak && !autoSpeak.checked) return;

  const b64 = data.wav_base64;
  if (!b64) return;

  const audio = new Audio(`data:${data.mime || 'audio/wav'};base64,${b64}`);

  // Let voice.js coordinate listening/playing (for hands-free)
  window.__lucy_lastAudio = audio;

  audio.onended = () => { if (window.__lucy_lastAudio === audio) window.__lucy_lastAudio = null; };
  audio.onpause = () => { if (audio.currentTime > 0 && window.__lucy_lastAudio === audio) window.__lucy_lastAudio = null; };

  audio.play().catch(err => console.warn('Audio play failed:', err));
});

function updateStatus(message, type = 'info') {
  const statusText = document.getElementById('status-text');
  const statusDot = document.querySelector('.status-dot');
  statusText.textContent = message;

  if (type === 'success') statusDot.style.background = '#10b981';
  else if (type === 'error') statusDot.style.background = '#ef4444';
  else if (type === 'warning') statusDot.style.background = '#f59e0b';
  else statusDot.style.background = '#3b82f6';
}

window.lucySocket = socket;
window.updateStatus = updateStatus;
