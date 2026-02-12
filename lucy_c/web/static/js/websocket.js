// WebSocket connection handler
const socket = io({
  reconnection: true,
  reconnectionAttempts: Infinity,
  reconnectionDelay: 500,
  reconnectionDelayMax: 3000,
  timeout: 5000,
});

function ensureReconnectBanner() {
  let el = document.getElementById('reconnect-banner');
  if (el) return el;
  el = document.createElement('div');
  el.id = 'reconnect-banner';
  el.style.position = 'fixed';
  el.style.left = '0';
  el.style.right = '0';
  el.style.bottom = '0';
  el.style.padding = '10px 14px';
  el.style.background = 'rgba(17,24,39,0.95)';
  el.style.borderTop = '1px solid #3a3a3a';
  el.style.color = '#e5e5e5';
  el.style.fontSize = '14px';
  el.style.zIndex = '99999';
  el.style.display = 'none';

  const msg = document.createElement('span');
  msg.id = 'reconnect-banner-text';
  msg.textContent = 'Desconectado. Reintentando…';

  const btn = document.createElement('button');
  btn.textContent = 'Recargar';
  btn.style.marginLeft = '12px';
  btn.style.padding = '6px 10px';
  btn.style.borderRadius = '8px';
  btn.style.border = '1px solid #7c3aed';
  btn.style.background = '#111827';
  btn.style.color = '#fff';
  btn.style.cursor = 'pointer';
  btn.onclick = () => window.location.reload();

  el.appendChild(msg);
  el.appendChild(btn);
  document.body.appendChild(el);
  return el;
}

function setBanner(visible, text) {
  const el = ensureReconnectBanner();
  const msg = document.getElementById('reconnect-banner-text');
  if (msg && text) msg.textContent = text;
  el.style.display = visible ? 'block' : 'none';
}

socket.on('connect', () => {
  console.log('Connected to Lucy-C server');
  setBanner(false);
  updateStatus('Connected', 'success');
});

socket.on('disconnect', (reason) => {
  console.log('Disconnected from server', reason);
  setBanner(true, 'Desconectado. Reintentando…');
  updateStatus('Disconnected', 'error');
});

socket.on('reconnect_attempt', (n) => {
  setBanner(true, `Reconectando… intento ${n}`);
});

socket.on('reconnect_failed', () => {
  setBanner(true, 'No se pudo reconectar. Probá recargar.');
});

socket.on('error', (data) => {
  console.error('Socket error:', data);
  setBanner(true, 'Error de conexión. Reintentando…');
  updateStatus((data && data.message) || 'Error', 'error');
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

  audio.play()
    .then(() => {
      window.dispatchEvent(new Event('lucy:tts_start'));
    })
    .catch(err => console.warn('Audio play failed:', err));

  audio.onended = () => {
    if (window.__lucy_lastAudio === audio) window.__lucy_lastAudio = null;
    window.__lucy_ttsEndedAt = performance.now();
    window.dispatchEvent(new Event('lucy:response_end'));
  };
  audio.onpause = () => {
    if (audio.currentTime > 0 && window.__lucy_lastAudio === audio) window.__lucy_lastAudio = null;
    window.__lucy_ttsEndedAt = performance.now();
    // Treat pause as end for generic turn-taking (user can interrupt)
    window.dispatchEvent(new Event('lucy:response_end'));
  };
});

function updateStatus(message, type = 'info') {
  const statusText = document.getElementById('status-text');
  const statusDot = document.getElementById('status-dot');
  if (!statusText || !statusDot) return;
  statusText.textContent = message;

  if (type === 'success') statusDot.style.background = '#10b981';
  else if (type === 'error') statusDot.style.background = '#ef4444';
  else if (type === 'warning') statusDot.style.background = '#f59e0b';
  else statusDot.style.background = '#3b82f6';
}

window.lucySocket = socket;
window.updateStatus = updateStatus;
