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
class LLMConfig:
    # "ollama" or "clawdbot"
    provider: str = "ollama"


@dataclass
class OllamaConfig:
    host: str = "http://127.0.0.1:11434"
    model: str = "gpt-oss:20b"


@dataclass
class ClawdbotConfig:
    host: str = "http://127.0.0.1:18789"
    agent_id: str = "main"
    token: str = ""  # prefer env CLAWDBOT_GATEWAY_TOKEN
    timeout_s: float = 120.0


@dataclass
class TTSConfig:
    voice: str = "es_ES/m-ailabs_low#karen_savage"


@dataclass
class AudioConfig:
    sample_rate: int = 16000


@dataclass
class LucyConfig:
    asr: ASRConfig = field(default_factory=ASRConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    ollama: OllamaConfig = field(default_factory=OllamaConfig)
    clawdbot: ClawdbotConfig = field(default_factory=ClawdbotConfig)
    tts: TTSConfig = field(default_factory=TTSConfig)
    audio: AudioConfig = field(default_factory=AudioConfig)

    @staticmethod
    def load(path: str | Path) -> "LucyConfig":
        p = Path(path)
        if not p.exists():
            return LucyConfig()
            
        try:
            data: Dict[str, Any] = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        except Exception:
            # Fallback to defaults if YAML is corrupted
            return LucyConfig()

        asr = data.get("asr", {}) or {}
        llm = data.get("llm", {}) or {}
        ollama = data.get("ollama", {}) or {}
        clawdbot = data.get("clawdbot", {}) or {}
        tts = data.get("tts", {}) or {}
        audio = data.get("audio", {}) or {}

        # Merge with defaults
        return LucyConfig(
            asr=ASRConfig(**{**ASRConfig().__dict__, **asr}),
            llm=LLMConfig(**{**LLMConfig().__dict__, **llm}),
            ollama=OllamaConfig(**{**OllamaConfig().__dict__, **ollama}),
            clawdbot=ClawdbotConfig(**{**ClawdbotConfig().__dict__, **clawdbot}),
            tts=TTSConfig(**{**TTSConfig().__dict__, **tts}),
            audio=AudioConfig(**{**AudioConfig().__dict__, **audio}),
        )
