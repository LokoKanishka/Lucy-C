from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict

import yaml


@dataclass
class ASRConfig:
    model: str = "Systran/faster-whisper-small"
    device: str = "cpu"
    compute_type: str = "int8"
    language: str = "es"
    task: str = "transcribe"
    force_language: bool = True


@dataclass
class OllamaConfig:
    host: str = "http://127.0.0.1:11434"
    model: str = "gpt-oss:20b"


@dataclass
class TTSConfig:
    voice: str = "es_ES/m-ailabs_low#karen_savage"


@dataclass
class AudioConfig:
    sample_rate: int = 16000


@dataclass
class LucyConfig:
    asr: ASRConfig = field(default_factory=ASRConfig)
    ollama: OllamaConfig = field(default_factory=OllamaConfig)
    tts: TTSConfig = field(default_factory=TTSConfig)
    audio: AudioConfig = field(default_factory=AudioConfig)

    @staticmethod
    def load(path: str | Path) -> "LucyConfig":
        p = Path(path)
        data: Dict[str, Any] = yaml.safe_load(p.read_text(encoding="utf-8")) or {}

        asr = data.get("asr", {}) or {}
        ollama = data.get("ollama", {}) or {}
        tts = data.get("tts", {}) or {}
        audio = data.get("audio", {}) or {}

        return LucyConfig(
            asr=ASRConfig(**{**ASRConfig().__dict__, **asr}),
            ollama=OllamaConfig(**{**OllamaConfig().__dict__, **ollama}),
            tts=TTSConfig(**{**TTSConfig().__dict__, **tts}),
            audio=AudioConfig(**{**AudioConfig().__dict__, **audio}),
        )
