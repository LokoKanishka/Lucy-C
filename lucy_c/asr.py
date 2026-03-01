from __future__ import annotations

import logging
import os
import threading
from typing import Tuple

import numpy as np
from faster_whisper import WhisperModel

from lucy_c.config import ASRConfig
from lucy_c.interfaces.audio import ASRProvider, ASRResult


class FasterWhisperASR(ASRProvider):
    def __init__(self, cfg: ASRConfig):
        self.cfg = cfg
        self.log = logging.getLogger("LucyC.ASR")

        # Lazy-load: NO cargar el modelo en __init__.
        self._lock = threading.Lock()
        self.model: WhisperModel | None = None

    def _ensure_model(self) -> None:
        if self.model is not None:
            return

        with self._lock:
            if self.model is not None:
                return

            # En modo local-only, forzamos offline para evitar requests a HuggingFace.
            if os.environ.get("LUCY_LOCAL_ONLY", "").strip() == "1":
                os.environ.setdefault("HF_HUB_OFFLINE", "1")
                os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

            self.log.info(
                "Loading Whisper model %r (device=%s compute=%s) [lazy]",
                self.cfg.model,
                self.cfg.device,
                self.cfg.compute_type,
            )

            try:
                self.model = WhisperModel(self.cfg.model, device=self.cfg.device, compute_type=self.cfg.compute_type)
            except Exception as e:
                # Common on fresh Linux installs: CUDA runtime libs (e.g. libcublas) not present.
                # Fall back to CPU so the app remains usable.
                if str(self.cfg.device).lower() == "cuda":
                    self.log.warning(
                        "Failed to init Whisper on CUDA (%s). Falling back to CPU.\n"
                        "Tip: install CUDA 12 runtime (libcublas.so.12) to re-enable GPU.",
                        e,
                    )
                    self.cfg.device = "cpu"
                    # int8 is the typical fast/compatible CPU compute type
                    self.cfg.compute_type = "int8"
                    self.model = WhisperModel(self.cfg.model, device="cpu", compute_type="int8")
                else:
                    raise

    def transcribe(self, audio_f32: np.ndarray) -> ASRResult:
        self._ensure_model()

        audio_f32 = np.asarray(audio_f32, dtype=np.float32)
        language = self.cfg.language if self.cfg.force_language else None
        task = self.cfg.task or "transcribe"

        try:
            segments, info = self.model.transcribe(
                audio_f32,
                beam_size=4,  # Increased for accuracy
                best_of=5,
                vad_filter=True,
                language=language,
                task=task,
                initial_prompt=self.cfg.initial_prompt if hasattr(self.cfg, "initial_prompt") else None,
            )
        except RuntimeError as e:
            # Some CUDA lib problems only show up at first encode.
            msg = str(e)
            if "libcublas" in msg and str(self.cfg.device).lower() == "cuda":
                self.log.warning(
                    "CUDA runtime missing at transcribe-time (%s). Switching ASR to CPU.",
                    e,
                )
                self.cfg.device = "cpu"
                self.cfg.compute_type = "int8"
                self.model = WhisperModel(self.cfg.model, device="cpu", compute_type="int8")
                segments, info = self.model.transcribe(
                    audio_f32,
                    beam_size=2,
                    best_of=5,
                    vad_filter=False,
                    language=language,
                    task=task,
                )
            else:
                raise

        chunks = [seg.text.strip() for seg in segments if seg.text and seg.text.strip()]
        text = " ".join(chunks).strip()
        lang = (info.language or "unknown")
        return ASRResult(text=text, language=lang)
