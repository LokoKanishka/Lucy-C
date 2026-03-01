const socket = io();
const chat = document.getElementById('chat');
const statusEl = document.getElementById('status');
const dot = document.getElementById('dot');

function setStatus(msg, type = 'info') {
  statusEl.textContent = msg;
  dot.style.background = ({ success: '#10b981', error: '#ef4444', warning: '#f59e0b', info: '#3b82f6' })[type] || '#3b82f6';
}

function addMessage(type, content) {
  const wrap = document.createElement('div');
  wrap.className = `msg ${type}`;
  const meta = document.createElement('div');
  meta.className = 'meta';
  meta.textContent = type === 'user' ? 'Diego' : 'lucy';
  const body = document.createElement('div');
  body.textContent = content;
  wrap.appendChild(meta);
  wrap.appendChild(body);
  chat.appendChild(wrap);
  chat.scrollTop = chat.scrollHeight;
}

socket.on('connect', () => setStatus('Connected', 'success'));
socket.on('disconnect', () => setStatus('Disconnected', 'error'));
socket.on('status', (d) => setStatus(d.message, d.type || 'info'));
socket.on('error', (d) => setStatus(d.message || 'Error', 'error'));
socket.on('message', (d) => addMessage(d.type, d.content));

// Tool execution badges
socket.on('tool_event', (d) => {
  const badge = document.createElement('div');
  badge.className = `tool-badge tool-${d.category || 'actuator'}`;
  badge.innerHTML = `<span class="tool-emoji">${d.emoji || '⚙️'}</span> <span class="tool-name">${d.message || d.tool}</span>`;
  chat.appendChild(badge);
  chat.scrollTop = chat.scrollHeight;

  // Auto-remove after message appears (optional)
  setTimeout(() => {
    if (badge.parentNode) {
      badge.style.opacity = '0.6';
    }
  }, 3000);
});

socket.on('audio', (d) => {
  if (!d.wav_base64) return;
  const audio = new Audio(`data:${d.mime || 'audio/wav'};base64,${d.wav_base64}`);
  audio.play().catch((e) => console.warn('audio play failed', e));
});

// Push-to-talk
const ptt = document.getElementById('ptt');
const pttLabel = document.getElementById('pttLabel');
let isRecording = false;
let mediaRecorder = null;
let chunks = [];
let stream = null;

function pickMimeType() {
  const c = ['audio/webm;codecs=opus', 'audio/webm', 'audio/ogg;codecs=opus', 'audio/ogg'];
  for (const t of c) {
    if (MediaRecorder.isTypeSupported(t)) return t;
  }
  return '';
}

async function startRec() {
  if (isRecording) return;
  stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  const mimeType = pickMimeType();
  mediaRecorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
  chunks = [];
  mediaRecorder.ondataavailable = (e) => { if (e.data && e.data.size > 0) chunks.push(e.data); };
  mediaRecorder.onstop = async () => {
    try {
      const blob = new Blob(chunks, { type: mimeType || 'audio/webm' });
      const buf = await blob.arrayBuffer();
      const u8 = new Uint8Array(buf);
      socket.emit('voice_input', { audio: Array.from(u8) });
      setStatus('Procesando…', 'info');
    } finally {
      if (stream) stream.getTracks().forEach(t => t.stop());
      stream = null;
    }
  };
  mediaRecorder.start();
  isRecording = true;
  ptt.classList.add('recording');
  pttLabel.textContent = 'Grabando… soltá para enviar';
  setStatus('Grabando…', 'warning');
}

function stopRec() {
  if (!isRecording) return;
  isRecording = false;
  ptt.classList.remove('recording');
  pttLabel.textContent = 'Mantener para hablar';
  if (mediaRecorder) mediaRecorder.stop();
}

ptt.addEventListener('mousedown', startRec);
ptt.addEventListener('touchstart', (e) => { e.preventDefault(); startRec(); });
window.addEventListener('mouseup', stopRec);
window.addEventListener('touchend', stopRec);
