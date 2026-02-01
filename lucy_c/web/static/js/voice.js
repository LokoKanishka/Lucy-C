// Voice input controls
// - Push-to-talk: hold 🎤 (MediaRecorder)
// - Hands-free: VAD on RMS + preroll using a PCM ring buffer (WebAudio)

const voiceBtn = document.getElementById('voice-btn');
const handsfreeToggle = document.getElementById('handsfree-toggle');
const rawMicToggle = document.getElementById('raw-mic-toggle');

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

// Hands-free PCM capture
let hfCaptureNode = null;
let hfPcm = null; // Float32Array ring
let hfPcmWrite = 0;
let hfPcmRate = 48000;
let hfUtterStartSample = 0;

const HF = {
  // VAD thresholds
  rmsThreshold: 0.025,
  rmsThresholdRaw: 0.010,

  // Timing
  minSpeechMs: 800,
  endSilenceMs: 1600,
  maxUtteranceMs: 18000,
  postTtsCooldownMs: 500,

  // Preroll (avoid clipped starts)
  prerollMs: 600,

  // PCM ring buffer
  ringSeconds: 20,

  // Barge-in
  bargeInMs: 0,
  bargeInThreshold: 0.008,
};

async function initMicrophone() {
  try {
    const raw = !!(rawMicToggle && rawMicToggle.checked);
    return await navigator.mediaDevices.getUserMedia({
      audio: raw
        ? { echoCancellation: false, noiseSuppression: false, autoGainControl: false }
        : { echoCancellation: true, noiseSuppression: true, autoGainControl: true },
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
  if (window.showTypingIndicator) window.showTypingIndicator();
  updateStatus('Procesando voz...', 'info');
}

// ===== WAV encoding helpers =====
function encodeWavPCM16(samples, sampleRate) {
  // samples: Float32Array [-1..1]
  const buffer = new ArrayBuffer(44 + samples.length * 2);
  const view = new DataView(buffer);

  function writeString(offset, str) {
    for (let i = 0; i < str.length; i++) view.setUint8(offset + i, str.charCodeAt(i));
  }

  let offset = 0;
  writeString(offset, 'RIFF'); offset += 4;
  view.setUint32(offset, 36 + samples.length * 2, true); offset += 4;
  writeString(offset, 'WAVE'); offset += 4;
  writeString(offset, 'fmt '); offset += 4;
  view.setUint32(offset, 16, true); offset += 4; // PCM
  view.setUint16(offset, 1, true); offset += 2;  // format
  view.setUint16(offset, 1, true); offset += 2;  // channels
  view.setUint32(offset, sampleRate, true); offset += 4;
  view.setUint32(offset, sampleRate * 2, true); offset += 4; // byte rate
  view.setUint16(offset, 2, true); offset += 2; // block align
  view.setUint16(offset, 16, true); offset += 2; // bits
  writeString(offset, 'data'); offset += 4;
  view.setUint32(offset, samples.length * 2, true); offset += 4;

  // PCM16
  for (let i = 0; i < samples.length; i++, offset += 2) {
    let s = Math.max(-1, Math.min(1, samples[i]));
    view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7fff, true);
  }

  return new Uint8Array(buffer);
}

function downsampleLinear(input, inRate, outRate) {
  if (outRate === inRate) return input;
  const ratio = inRate / outRate;
  const outLen = Math.max(1, Math.floor(input.length / ratio));
  const out = new Float32Array(outLen);
  for (let i = 0; i < outLen; i++) {
    const t = i * ratio;
    const i0 = Math.floor(t);
    const i1 = Math.min(input.length - 1, i0 + 1);
    const a = t - i0;
    out[i] = (1 - a) * input[i0] + a * input[i1];
  }
  return out;
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

async function toggleRecording() {
  if (hfEnabled) return;

  if (isRecording) {
    stopRecording();
    updateStatus('Procesando...', 'info');
  } else {
    const a = window.__lucy_lastAudio;
    if (a && !a.paused) {
      try { a.pause(); a.currentTime = 0; } catch { }
      window.__lucy_lastAudio = null;
    }
    updateStatus('Escuchando... (clic para enviar)', 'warning');
    await startRecording();
  }
}

voiceBtn.addEventListener('click', (e) => {
  e.preventDefault();
  toggleRecording();
});

// Remove global mouseup/touchend listeners that forced stopRecording
// window.addEventListener('mouseup', () => { if (!hfEnabled) stopRecording(); });
// window.addEventListener('touchend', () => { if (!hfEnabled) stopRecording(); });

// ===== Hands-free =====
function computeRMS(timeDomainFloat32) {
  let sum = 0;
  for (let i = 0; i < timeDomainFloat32.length; i++) {
    const v = timeDomainFloat32[i];
    sum += v * v;
  }
  return Math.sqrt(sum / timeDomainFloat32.length);
}

function ringWriteSamples(samples) {
  if (!hfPcm) return;
  for (let i = 0; i < samples.length; i++) {
    hfPcm[hfPcmWrite] = samples[i];
    hfPcmWrite = (hfPcmWrite + 1) % hfPcm.length;
  }
}

function ringReadRange(startSampleAbs, endSampleAbs) {
  // start/end are absolute sample indices in the running stream timeline.
  // We map them into the ring relative to current write pointer.
  const len = hfPcm.length;
  const nowAbs = hfPcmWriteAbs();
  const maxBack = len;
  const start = Math.max(nowAbs - maxBack, startSampleAbs);
  const end = Math.min(nowAbs, endSampleAbs);
  const count = Math.max(0, end - start);
  const out = new Float32Array(count);

  // absolute -> ring index
  for (let i = 0; i < count; i++) {
    const abs = start + i;
    const idx = abs % len;
    out[i] = hfPcm[idx];
  }
  return out;
}

let __hfAbsCounter = 0; // increments with each sample written
function hfPcmWriteAbs() { return __hfAbsCounter; }

async function startPcmCapture(stream) {
  hfPcmRate = 48000;
  hfPcmWrite = 0;
  __hfAbsCounter = 0;

  hfCtx = new (window.AudioContext || window.webkitAudioContext)();
  hfPcmRate = hfCtx.sampleRate;

  hfPcm = new Float32Array(Math.floor(HF.ringSeconds * hfPcmRate));

  hfSource = hfCtx.createMediaStreamSource(stream);
  hfAnalyser = hfCtx.createAnalyser();
  hfAnalyser.fftSize = 2048;

  // ScriptProcessor is widely supported; good enough here.
  hfCaptureNode = hfCtx.createScriptProcessor(2048, 1, 1);
  hfCaptureNode.onaudioprocess = (ev) => {
    const input = ev.inputBuffer.getChannelData(0);
    ringWriteSamples(input);
    __hfAbsCounter += input.length;
  };

  hfSource.connect(hfAnalyser);
  hfSource.connect(hfCaptureNode);
  hfCaptureNode.connect(hfCtx.destination);
}

const VState = {
  IDLE: 'IDLE',
  LISTENING: 'LISTENING',
  RECORDING: 'RECORDING',
  SENDING: 'SENDING',
  SPEAK_WAIT: 'SPEAK_WAIT'
};

let currentState = VState.IDLE;

async function handsfreeStart() {
  if (hfEnabled) return;

  const stream = await initMicrophone();
  if (!stream) return;

  hfEnabled = true;
  currentStream = stream;
  currentState = VState.LISTENING;

  hfSpeechActive = false;
  hfSpeechStartMs = 0;
  hfLastLoudMs = 0;

  if (!window.__lucy_ttsEndedAt) window.__lucy_ttsEndedAt = 0;
  if (!window.__lucy_lastRmsTs) window.__lucy_lastRmsTs = 0;

  await startPcmCapture(stream);

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
    const pending = !!HF.responsePending;

    hfAnalyser.getFloatTimeDomainData(buf);
    const rms = computeRMS(buf);

    const rawOn = !!(rawMicToggle && rawMicToggle.checked);
    const thr = rawOn ? HF.rmsThresholdRaw : HF.rmsThreshold;
    const loud = rms >= thr;
    const loudBarge = rms >= HF.bargeInThreshold;

    // Mic meter update (kept same)
    try {
      const bar = document.getElementById('mic-meter-bar');
      const thrEl = document.getElementById('mic-meter-thr');
      if (bar && thrEl) {
        const pct = Math.max(0, Math.min(100, (rms / 0.08) * 100));
        bar.style.width = pct.toFixed(1) + '%';
        const thrPct = Math.max(0, Math.min(100, (thr / 0.08) * 100));
        thrEl.style.left = thrPct.toFixed(1) + '%';
      }
    } catch { }

    // State machine transitions
    if (isPlaying || pending || inCooldown) {
      if (currentState !== VState.SPEAK_WAIT) {
        currentState = VState.SPEAK_WAIT;
        hfSpeechActive = false;
        if (isPlaying) updateStatus('Lucy hablando...', 'info');
        else if (pending) updateStatus('Pensando...', 'info');
      }

      // Barge-in Logic
      if (isPlaying && loudBarge) {
        if (!bargeInStart) bargeInStart = now;
        if (HF.bargeInMs === 0 || (now - bargeInStart) >= HF.bargeInMs) {
          try { a.pause(); a.currentTime = 0; } catch { }
          window.__lucy_lastAudio = null;
          bargeInStart = 0;
          currentState = VState.LISTENING; // Break out of SPEAK_WAIT
          updateStatus('Interrumpido. Te escucho…', 'success');
        }
      } else {
        bargeInStart = 0;
      }
    } else {
      // Not playing, not pending, not in cooldown
      if (currentState === VState.SPEAK_WAIT) {
        currentState = VState.LISTENING;
        updateStatus('Te escucho...', 'success');
      }
    }

    // Process states if we are not locked in SPEAK_WAIT (unless we just barged in)
    if (currentState !== VState.SPEAK_WAIT) {
      switch (currentState) {
        case VState.LISTENING:
          if (loud) {
            currentState = VState.RECORDING;
            hfSpeechStartMs = now;
            hfLastLoudMs = now;
            const nowAbs = hfPcmWriteAbs();
            const prerollSamples = Math.floor((HF.prerollMs / 1000) * hfPcmRate);
            hfUtterStartSample = Math.max(0, nowAbs - prerollSamples);
            updateStatus('Escuchando...', 'warning');
          }
          break;

        case VState.RECORDING:
          if (loud) hfLastLoudMs = now;
          const speechDur = now - hfSpeechStartMs;
          const silenceDur = now - hfLastLoudMs;
          const enoughSpeech = speechDur >= HF.minSpeechMs;

          if (enoughSpeech && silenceDur >= HF.endSilenceMs) {
            currentState = VState.SENDING;
            processAndSend();
          } else if (speechDur >= HF.maxUtteranceMs) {
            currentState = VState.SENDING;
            processAndSend();
          }
          break;

        case VState.SENDING:
          // Locking until backend acknowledges something
          break;
      }
    }

    function processAndSend() {
      if (window.showTypingIndicator) window.showTypingIndicator();
      updateStatus('Enviando...', 'info');
      const endAbs = hfPcmWriteAbs();
      const pcm = ringReadRange(hfUtterStartSample, endAbs);
      const pcm16k = downsampleLinear(pcm, hfPcmRate, 16000);
      const wav = encodeWavPCM16(pcm16k, 16000);
      HF.responsePending = true;
      void sendAudioBytes(wav);
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

  try { if (hfSource) hfSource.disconnect(); } catch { }
  try { if (hfCaptureNode) hfCaptureNode.disconnect(); } catch { }
  hfSource = null;
  hfAnalyser = null;
  hfCaptureNode = null;

  if (hfCtx) {
    hfCtx.close().catch(() => { });
    hfCtx = null;
  }

  if (currentStream) {
    currentStream.getTracks().forEach(t => t.stop());
    currentStream = null;
  }

  hfPcm = null;
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

window.addEventListener('load', () => {
  // Init hands-free default (true unless explicitly disabled)
  const saved = localStorage.getItem('lucy_handsfree');
  // Default to TRUE if null, otherwise parse string
  const shouldEnable = saved === null ? true : (saved === 'true');

  if (shouldEnable && handsfreeToggle) {
    if (!handsfreeToggle.checked) {
      handsfreeToggle.checked = true;
      // Small delay to let page stabilize before asking for mic
      setTimeout(() => handsfreeToggle.dispatchEvent(new Event('change')), 500);
    }
  }
});

// Turn-taking Lifecycle
let fallbackTimer = null;

window.addEventListener('lucy:response_start', () => {
  HF.responsePending = true;
  // If we were recording, stop it
  if (currentState === VState.RECORDING) {
    currentState = VState.SPEAK_WAIT;
  }
  updateStatus('Lucy está pensando...', 'info');

  // Fallback: if no TTS starts within 2s, assume text-only and resume
  if (fallbackTimer) clearTimeout(fallbackTimer);
  fallbackTimer = setTimeout(() => {
    if (HF.responsePending) {
      console.log('Voice: No TTS detected, resuming loop...');
      HF.responsePending = false;
      fallbackTimer = null;
    }
  }, 2000);
});

window.addEventListener('lucy:tts_start', () => {
  if (fallbackTimer) {
    clearTimeout(fallbackTimer);
    fallbackTimer = null;
  }
  HF.responsePending = true;
  currentState = VState.SPEAK_WAIT;
  updateStatus('Lucy está hablando...', 'info');
});

window.addEventListener('lucy:response_end', () => {
  HF.responsePending = false;
  if (fallbackTimer) clearTimeout(fallbackTimer);
  // States will be updated in the loop to LISTENING after cooldown
});

window.LUCY_HANDSFREE = { HF, handsfreeStart, handsfreeStop, VState };
