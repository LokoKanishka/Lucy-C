// Voice input controls
// - Push-to-talk: hold 🎤
// - Hands-free: client-side VAD (RMS threshold) + auto-send on silence
//   Includes continuous MediaRecorder with preroll to avoid clipping first syllables.

const voiceBtn = document.getElementById('voice-btn');
const handsfreeToggle = document.getElementById('handsfree-toggle');
const rawMicToggle = document.getElementById('raw-mic-toggle');

let isRecording = false;          // push-to-talk recorder state
let mediaRecorder = null;         // push-to-talk MediaRecorder
let audioChunks = [];             // push-to-talk chunks
let currentStream = null;

// Hands-free state
let hfEnabled = false;
let hfCtx = null;
let hfAnalyser = null;
let hfSource = null;
let hfRaf = null;
let hfSpeechActive = false;
let hfSpeechStartMs = 0;
let hfLastLoudMs = 0;

// Hands-free continuous recorder
let hfRecorder = null;
let hfMimeType = '';
/** @type {Array<{t:number, blob:Blob}>} */
let hfRing = [];
let hfUtterStartT = 0;

const HF = {
  // Higher => less sensitive
  rmsThreshold: 0.025,
  // When Raw mic is ON, RMS is usually lower (no AGC)
  rmsThresholdRaw: 0.010,

  // Don’t trigger on tiny clicks / short bursts
  minSpeechMs: 800,
  // End of utterance after this much silence
  endSilenceMs: 1600,
  // Safety cap
  maxUtteranceMs: 18000,

  // After Lucy finishes speaking, wait a bit before re-arming VAD
  postTtsCooldownMs: 500,

  // Preroll to avoid clipping first syllables
  prerollMs: 500,
  // MediaRecorder chunk size (hands-free)
  chunkMs: 250,
  // Keep at most this much in ring buffer
  ringKeepMs: 20000,

  // Barge-in
  bargeInMs: 0,
  bargeInThreshold: 0.008,
};

async function initMicrophone() {
  try {
    const raw = !!(rawMicToggle && rawMicToggle.checked);
    return await navigator.mediaDevices.getUserMedia({
      audio: raw ? {
        echoCancellation: false,
        noiseSuppression: false,
        autoGainControl: false,
      } : {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
      }
    });
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

async function sendAudioBytes(uint8) {
  const session_user = (window.getSessionUser && window.getSessionUser()) || null;
  lucySocket.emit('voice_input', { audio: Array.from(uint8), session_user, handsfree: hfEnabled });
  updateStatus('Procesando voz...', 'info');
}

// ===== Push-to-talk =====
async function startRecording(streamOverride = null) {
  if (isRecording) return;

  const stream = streamOverride || await initMicrophone();
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
      if (blob.size < 2048) {
        updateStatus('No se capturó audio (muy corto). Probá de nuevo.', 'warning');
        return;
      }
      const buf = await blob.arrayBuffer();
      await sendAudioBytes(new Uint8Array(buf));

    } finally {
      if (!hfEnabled && currentStream) {
        currentStream.getTracks().forEach(track => track.stop());
        currentStream = null;
      }
    }
  };

  mediaRecorder.start();

  voiceBtn.classList.add('recording');
  voiceBtn.querySelector('span').textContent = '⏺️';
}

function stopRecording() {
  if (!mediaRecorder || !isRecording) return;
  isRecording = false;
  mediaRecorder.stop();

  voiceBtn.classList.remove('recording');
  voiceBtn.querySelector('span').textContent = '🎤';
}

voiceBtn.addEventListener('mousedown', () => {
  if (hfEnabled) return;
  const a = window.__lucy_lastAudio;
  if (a && !a.paused) {
    try { a.pause(); a.currentTime = 0; } catch {}
    window.__lucy_lastAudio = null;
  }
  updateStatus('Grabando (mantené apretado)...', 'warning');
  startRecording();
});
voiceBtn.addEventListener('touchstart', (e) => {
  if (hfEnabled) return;
  e.preventDefault();
  updateStatus('Grabando (mantené apretado)...', 'warning');
  startRecording();
});
window.addEventListener('mouseup', () => {
  if (hfEnabled) return;
  stopRecording();
});
window.addEventListener('touchend', () => {
  if (hfEnabled) return;
  stopRecording();
});

// ===== Hands-free =====
function computeRMS(timeDomainFloat32) {
  let sum = 0;
  for (let i = 0; i < timeDomainFloat32.length; i++) {
    const v = timeDomainFloat32[i];
    sum += v * v;
  }
  return Math.sqrt(sum / timeDomainFloat32.length);
}

async function startHandsfreeRecorder(stream) {
  hfRing = [];
  hfUtterStartT = 0;
  hfMimeType = pickMimeType() || 'audio/webm';
  hfRecorder = new MediaRecorder(stream, hfMimeType ? { mimeType: hfMimeType } : undefined);

  hfRecorder.ondataavailable = (event) => {
    if (!event.data || event.data.size === 0) return;
    const t = performance.now();
    hfRing.push({ t, blob: event.data });

    // trim ring
    const cutoff = t - HF.ringKeepMs;
    while (hfRing.length && hfRing[0].t < cutoff) hfRing.shift();
  };

  hfRecorder.start(HF.chunkMs);
}

async function finalizeUtterance(endT) {
  const startT = hfUtterStartT || (endT - HF.prerollMs);

  // collect blobs between startT and endT (+ one chunk)
  const blobs = hfRing
    .filter(x => x.t >= (startT - HF.chunkMs) && x.t <= (endT + HF.chunkMs))
    .map(x => x.blob);

  const blob = new Blob(blobs, { type: hfMimeType || 'audio/webm' });
  if (blob.size < 2048) {
    updateStatus('No se capturó audio (muy corto).', 'warning');
    return;
  }

  const buf = await blob.arrayBuffer();
  await sendAudioBytes(new Uint8Array(buf));
}

async function handsfreeStart() {
  if (hfEnabled) return;

  const stream = await initMicrophone();
  if (!stream) return;

  hfEnabled = true;
  currentStream = stream;

  // analyser
  hfCtx = new (window.AudioContext || window.webkitAudioContext)();
  hfSource = hfCtx.createMediaStreamSource(stream);
  hfAnalyser = hfCtx.createAnalyser();
  hfAnalyser.fftSize = 2048;
  hfSource.connect(hfAnalyser);

  hfSpeechActive = false;
  hfSpeechStartMs = 0;
  hfLastLoudMs = 0;

  if (!window.__lucy_ttsEndedAt) window.__lucy_ttsEndedAt = 0;
  if (!window.__lucy_lastRmsTs) window.__lucy_lastRmsTs = 0;

  await startHandsfreeRecorder(stream);

  updateStatus('Hands‑free: escuchando…', 'success');

  const buf = new Float32Array(hfAnalyser.fftSize);
  let bargeInStart = 0;

  const loop = () => {
    if (!hfEnabled) return;

    const now = performance.now();

    const a = window.__lucy_lastAudio;
    const isPlaying = !!(a && !a.paused);
    const ttsEndedAt = window.__lucy_ttsEndedAt || 0;
    const inCooldown = (!isPlaying) && ttsEndedAt && ((now - ttsEndedAt) < HF.postTtsCooldownMs);

    hfAnalyser.getFloatTimeDomainData(buf);
    const rms = computeRMS(buf);

    const rawOn = !!(rawMicToggle && rawMicToggle.checked);
    const thr = rawOn ? HF.rmsThresholdRaw : HF.rmsThreshold;
    const loud = rms >= thr;
    const loudBarge = rms >= HF.bargeInThreshold;

    // Mic meter
    try {
      const bar = document.getElementById('mic-meter-bar');
      const thrEl = document.getElementById('mic-meter-thr');
      if (bar && thrEl) {
        const pct = Math.max(0, Math.min(100, (rms / 0.08) * 100));
        bar.style.width = pct.toFixed(1) + '%';
        const thrPct = Math.max(0, Math.min(100, (thr / 0.08) * 100));
        thrEl.style.left = thrPct.toFixed(1) + '%';
      }
    } catch {}

    if (!window.__lucy_lastRmsTs || (now - window.__lucy_lastRmsTs) > 1000) {
      window.__lucy_lastRmsTs = now;
      if (!hfSpeechActive && !isPlaying && !inCooldown) {
        updateStatus(`Hands‑free: escuchando… (rms=${rms.toFixed(3)} thr=${thr.toFixed(3)})`, 'success');
      }
    }

    // Barge-in
    if (isPlaying && loudBarge) {
      if (!bargeInStart) bargeInStart = now;
      if (HF.bargeInMs === 0 || (now - bargeInStart) >= HF.bargeInMs) {
        try { a.pause(); a.currentTime = 0; } catch {}
        window.__lucy_lastAudio = null;
        bargeInStart = 0;
        updateStatus('Interrumpido. Te escucho…', 'success');
      }
    } else {
      bargeInStart = 0;
    }

    // While TTS playing or cooldown, don't segment speech
    if (isPlaying || inCooldown) {
      hfSpeechActive = false;
      hfRaf = requestAnimationFrame(loop);
      return;
    }

    if (loud) {
      hfLastLoudMs = now;
      if (!hfSpeechActive) {
        hfSpeechActive = true;
        hfSpeechStartMs = now;
        hfUtterStartT = now - HF.prerollMs;
        updateStatus('Hands‑free: grabando…', 'warning');
      }
    }

    if (hfSpeechActive) {
      const speechDur = now - hfSpeechStartMs;
      const silenceDur = now - hfLastLoudMs;

      const enoughSpeech = speechDur >= HF.minSpeechMs;
      const endBySilence = enoughSpeech && silenceDur >= HF.endSilenceMs;
      const endByMax = speechDur >= HF.maxUtteranceMs;

      if (endBySilence || endByMax) {
        hfSpeechActive = false;
        updateStatus('Pensando…', 'info');
        void finalizeUtterance(now);
      }
    }

    hfRaf = requestAnimationFrame(loop);
  };

  hfRaf = requestAnimationFrame(loop);
}

function handsfreeStop() {
  hfEnabled = false;
  hfSpeechActive = false;

  if (hfRaf) cancelAnimationFrame(hfRaf);
  hfRaf = null;

  try { if (hfSource) hfSource.disconnect(); } catch {}
  hfSource = null;
  hfAnalyser = null;

  if (hfCtx) {
    hfCtx.close().catch(() => {});
    hfCtx = null;
  }

  try {
    if (hfRecorder && hfRecorder.state !== 'inactive') hfRecorder.stop();
  } catch {}
  hfRecorder = null;
  hfRing = [];

  if (currentStream) {
    currentStream.getTracks().forEach(t => t.stop());
    currentStream = null;
  }

  updateStatus('Hands‑free: off', 'info');
}

handsfreeToggle?.addEventListener('change', async (e) => {
  const wantsHandsFree = !!e.target.checked;
  if (wantsHandsFree) await handsfreeStart();
  else handsfreeStop();
});

rawMicToggle?.addEventListener('change', async () => {
  if (!hfEnabled) return;
  updateStatus('Reiniciando mic…', 'info');
  handsfreeStop();
  await new Promise(r => setTimeout(r, 150));
  await handsfreeStart();
});

window.LUCY_HANDSFREE = { HF, handsfreeStart, handsfreeStop };
