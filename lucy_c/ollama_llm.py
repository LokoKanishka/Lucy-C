from __future__ import annotations

import logging
from dataclasses import dataclass

import httpx

from lucy_c.config import OllamaConfig


@dataclass
class LLMResult:
    text: str


class OllamaLLM:
    def __init__(self, cfg: OllamaConfig):
        self.cfg = cfg
        self.log = logging.getLogger("LucyC.Ollama")

    def generate(self, prompt: str) -> LLMResult:
        # Use Ollama /api/generate (non-stream for simplicity)
        url = f"{self.cfg.host.rstrip('/')}/api/generate"
        payload = {
            "model": self.cfg.model,
            "prompt": prompt,
            "stream": False,
        }
        with httpx.Client(timeout=120.0) as client:
            r = client.post(url, json=payload)
            r.raise_for_status()
            data = r.json()
        return LLMResult(text=(data.get("response") or "").strip())
