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
        self.model = WhisperModel(cfg.model, device=cfg.device, compute_type=cfg.compute_type)

    def transcribe(self, audio_f32: np.ndarray) -> ASRResult:
        audio_f32 = np.asarray(audio_f32, dtype=np.float32)
        language = self.cfg.language if self.cfg.force_language else None
        task = self.cfg.task or "transcribe"

        segments, info = self.model.transcribe(
            audio_f32,
            beam_size=1,
            vad_filter=False,
            language=language,
            task=task,
        )

        chunks = [seg.text.strip() for seg in segments if seg.text and seg.text.strip()]
        text = " ".join(chunks).strip()
        lang = (info.language or "unknown")
        return ASRResult(text=text, language=lang)
