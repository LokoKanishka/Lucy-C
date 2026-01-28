from __future__ import annotations

import io
import logging
import subprocess
from dataclasses import dataclass

import numpy as np
import soundfile as sf

from lucy_c.config import TTSConfig


@dataclass
class TTSResult:
    audio_f32: np.ndarray
    sample_rate: int


class Mimic3TTS:
    def __init__(self, cfg: TTSConfig):
        self.cfg = cfg
        self.log = logging.getLogger("LucyC.Mimic3")

    def synthesize(self, text: str) -> TTSResult:
        proc = subprocess.run(
            ["mimic3", "--voice", self.cfg.voice, "--stdout"],
            input=text.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"mimic3 failed: {proc.stderr.decode('utf-8', 'ignore')}")

        with io.BytesIO(proc.stdout) as bio:
            data, sr = sf.read(bio, dtype="float32")

        if data.ndim == 2:
            data = data[:, 0]
        return TTSResult(audio_f32=np.asarray(data, dtype=np.float32).reshape(-1), sample_rate=sr)
