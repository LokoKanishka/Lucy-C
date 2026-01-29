from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Tuple

import numpy as np
from faster_whisper import WhisperModel

from lucy_c.config import ASRConfig


@dataclass
class ASRResult:
    text: str
    language: str


class FasterWhisperASR:
    def __init__(self, cfg: ASRConfig):
        self.cfg = cfg
        self.log = logging.getLogger("LucyC.ASR")
        self.log.info(
            "Loading Whisper model %r (device=%s compute=%s)",
            cfg.model,
            cfg.device,
            cfg.compute_type,
        )
        try:
            self.model = WhisperModel(cfg.model, device=cfg.device, compute_type=cfg.compute_type)
        except Exception as e:
            # Common on fresh Linux installs: CUDA runtime libs (e.g. libcublas) not present.
            # Fall back to CPU so the app remains usable.
            if str(cfg.device).lower() == "cuda":
                self.log.warning(
                    "Failed to init Whisper on CUDA (%s). Falling back to CPU.\n"
                    "Tip: install CUDA 12 runtime (libcublas.so.12) to re-enable GPU.",
                    e,
                )
                self.cfg.device = "cpu"
                # int8 is the typical fast/compatible CPU compute type
                self.cfg.compute_type = "int8"
                self.model = WhisperModel(cfg.model, device="cpu", compute_type="int8")
            else:
                raise

    def transcribe(self, audio_f32: np.ndarray) -> ASRResult:
        audio_f32 = np.asarray(audio_f32, dtype=np.float32)
        language = self.cfg.language if self.cfg.force_language else None
        task = self.cfg.task or "transcribe"

        try:
            segments, info = self.model.transcribe(
                audio_f32,
                beam_size=5,
                vad_filter=False,
                language=language,
                task=task,
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
                    beam_size=5,
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
