from __future__ import annotations

import io
import subprocess
from dataclasses import dataclass

import numpy as np
import soundfile as sf


@dataclass
class DecodedAudio:
    audio: np.ndarray  # float32 mono
    sample_rate: int


def decode_audio_bytes_to_f32_mono(blob_bytes: bytes, target_sr: int = 16000) -> DecodedAudio:
    """Decode browser-recorded audio bytes (webm/ogg/wav/...) to float32 mono.

    Uses ffmpeg for robust decoding.
    """
    proc = subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            "pipe:0",
            "-ac",
            "1",
            "-ar",
            str(target_sr),
            "-f",
            "wav",
            "pipe:1",
        ],
        input=blob_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg decode failed: {proc.stderr.decode('utf-8', 'ignore')}")

    with io.BytesIO(proc.stdout) as bio:
        data, sr = sf.read(bio, dtype="float32")

    if data.ndim == 2:
        data = data[:, 0]

    return DecodedAudio(audio=np.asarray(data, dtype=np.float32).reshape(-1), sample_rate=sr)


def encode_wav_bytes(audio_f32: np.ndarray, sample_rate: int) -> bytes:
    audio_f32 = np.asarray(audio_f32, dtype=np.float32)
    with io.BytesIO() as bio:
        sf.write(bio, audio_f32, sample_rate, format="WAV", subtype="FLOAT")
        return bio.getvalue()
