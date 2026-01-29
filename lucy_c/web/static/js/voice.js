// Voice input controls
// - Push-to-talk: hold 🎤
// - Hands-free: simple client-side VAD (energy threshold) + auto-send on silence

const voiceBtn = document.getElementById('voice-btn');
const handsfreeToggle = document.getElementById('handsfree-toggle');

let isRecording = false;
let mediaRecorder = null;
let audioChunks = [];
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

// Tunables (these are the parameters you asked for)
const HF = {
  // Conservative defaults (reduce false triggers)
  // Higher => less sensitive
  rmsThreshold: 0.04,
  // Don’t trigger on tiny clicks / short bursts
  minSpeechMs: 600,
  // End of utterance after this much silence
  endSilenceMs: 900,
  // Safety cap: stop a too-long utterance
  maxUtteranceMs: 15000,
  // Barge-in: interrupt Lucy TTS if user starts speaking
  // Barge-in: as soon as mic detects speech over threshold, cut TTS.
  bargeInMs: 0,
  // Separate threshold for barge-in (more sensitive than normal VAD)
  bargeInThreshold: 0.008,
};

async function initMicrophone() {
  try {
    return await navigator.mediaDevices.getUserMedia({
      audio: {
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

      // Guardrail: Firefox can produce tiny/empty blobs if stop happens too fast.
      if (blob.size < 2048) {
        updateStatus('No se capturó audio (muy corto). Probá de nuevo.', 'warning');
        return;
      }

      const buf = await blob.arrayBuffer();
      const uint8 = new Uint8Array(buf);

      // Send bytes to server (+ stable session)
      const session_user = (window.getSessionUser && window.getSessionUser()) || null;
      lucySocket.emit('voice_input', { audio: Array.from(uint8), session_user });
      updateStatus('Procesando voz...', 'info');

    } finally {
      // In hands-free we keep the stream open; in push-to-talk we close it.
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

// ===== Push-to-talk =====
voiceBtn.addEventListener('mousedown', () => {
  if (hfEnabled) return; // ignore in hands-free

  // Always allow interrupting TTS when user starts speaking (even without hands-free)
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

// ===== Hands-free (VAD) =====
function computeRMS(timeDomainFloat32) {
  let sum = 0;
  for (let i = 0; i < timeDomainFloat32.length; i++) {
    const v = timeDomainFloat32[i];
    sum += v * v;
  }
  return Math.sqrt(sum / timeDomainFloat32.length);
}

async function handsfreeStart() {
  if (hfEnabled) return;

  const stream = await initMicrophone();
  if (!stream) return;

  hfEnabled = true;
  currentStream = stream;

  // Setup analyser
  hfCtx = new (window.AudioContext || window.webkitAudioContext)();
  hfSource = hfCtx.createMediaStreamSource(stream);
  hfAnalyser = hfCtx.createAnalyser();
  hfAnalyser.fftSize = 2048;
  hfSource.connect(hfAnalyser);

  hfSpeechActive = false;
  hfSpeechStartMs = 0;
  hfLastLoudMs = 0;

  updateStatus('Hands‑free: escuchando…', 'success');

  const buf = new Float32Array(hfAnalyser.fftSize);

  let bargeInStart = 0;

  const loop = () => {
    if (!hfEnabled) return;

    const a = window.__lucy_lastAudio;
    const isPlaying = !!(a && !a.paused);

    hfAnalyser.getFloatTimeDomainData(buf);
    const rms = computeRMS(buf);
    const loud = rms >= HF.rmsThreshold;
    const loudBarge = rms >= HF.bargeInThreshold;

    const now = performance.now();

    // Barge-in: if Lucy is speaking and user starts speaking, cut TTS.
    if (isPlaying && loudBarge) {
      // Cut immediately (or after bargeInMs if configured)
      if (!bargeInStart) bargeInStart = now;
      if (HF.bargeInMs === 0 || (now - bargeInStart) >= HF.bargeInMs) {
        try {
          a.pause();
          a.currentTime = 0;
        } catch {}
        window.__lucy_lastAudio = null;
        bargeInStart = 0;
        updateStatus('Interrumpido. Te escucho…', 'success');
      }
    } else {
      bargeInStart = 0;
    }

    // Avoid feedback loop: while Lucy is speaking, don't start/stop recordings.
    // Only barge-in detection is allowed.
    if (isPlaying) {
      if (hfSpeechActive) hfSpeechActive = false;
      if (isRecording) stopRecording();
      hfRaf = requestAnimationFrame(loop);
      return;
    }

    // Normal hands-free VAD logic
    if (loud) {
      hfLastLoudMs = now;
      if (!hfSpeechActive) {
        hfSpeechActive = true;
        hfSpeechStartMs = now;
        startRecording(stream);
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
        stopRecording();
        updateStatus('Pensando…', 'info');
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

  // stop any in-flight recorder
  try { if (isRecording) stopRecording(); } catch {}

  if (currentStream) {
    currentStream.getTracks().forEach(t => t.stop());
    currentStream = null;
  }

  updateStatus('Hands‑free: off', 'info');
}

handsfreeToggle?.addEventListener('change', (e) => {
  if (e.target.checked) {
    handsfreeStart();
  } else {
    handsfreeStop();
  }
});

// Make it easy to tweak from console
window.LUCY_HANDSFREE = { HF, handsfreeStart, handsfreeStop };
