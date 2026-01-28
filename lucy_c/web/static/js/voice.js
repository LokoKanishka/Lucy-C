// Voice input controls (push-to-talk)
const voiceBtn = document.getElementById('voice-btn');

let isRecording = false;
let mediaRecorder = null;
let audioChunks = [];
let currentStream = null;

async function initMicrophone() {
  try {
    return await navigator.mediaDevices.getUserMedia({ audio: true });
  } catch (error) {
    console.error('Microphone access denied:', error);
    updateStatus('Microphone access denied', 'error');
    return null;
  }
}

function pickMimeType() {
  const candidates = [
    'audio/webm;codecs=opus',
    'audio/webm',
    'audio/ogg;codecs=opus',
    'audio/ogg',
  ];
  for (const t of candidates) {
    if (MediaRecorder.isTypeSupported(t)) return t;
  }
  return '';
}

async function startRecording() {
  if (isRecording) return;

  const stream = await initMicrophone();
  if (!stream) return;

  currentStream = stream;
  isRecording = true;
  audioChunks = [];

  const mimeType = pickMimeType();
  mediaRecorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);

  mediaRecorder.ondataavailable = (event) => {
    if (event.data && event.data.size > 0) audioChunks.push(event.data);
  };

  mediaRecorder.onstop = async () => {
    try {
      const blob = new Blob(audioChunks, { type: mimeType || 'audio/webm' });
      const buf = await blob.arrayBuffer();
      const uint8 = new Uint8Array(buf);
      lucySocket.emit('voice_input', { audio: Array.from(uint8) });
      updateStatus('Procesando voz...', 'info');
    } finally {
      if (currentStream) currentStream.getTracks().forEach(track => track.stop());
      currentStream = null;
    }
  };

  mediaRecorder.start();

  voiceBtn.classList.add('recording');
  voiceBtn.querySelector('span').textContent = '⏺️';
  updateStatus('Grabando (mantené apretado)...', 'warning');
}

function stopRecording() {
  if (!mediaRecorder || !isRecording) return;
  isRecording = false;
  mediaRecorder.stop();

  voiceBtn.classList.remove('recording');
  voiceBtn.querySelector('span').textContent = '🎤';
}

voiceBtn.addEventListener('mousedown', startRecording);
voiceBtn.addEventListener('touchstart', (e) => { e.preventDefault(); startRecording(); });
window.addEventListener('mouseup', stopRecording);
window.addEventListener('touchend', stopRecording);
