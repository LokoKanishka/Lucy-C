from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List

import httpx

from lucy_c.config import OllamaConfig


@dataclass
class LLMResult:
    text: str


class OllamaLLM:
    def __init__(self, cfg: OllamaConfig):
        self.cfg = cfg
        self.log = logging.getLogger("LucyC.Ollama")

    def list_models(self) -> List[str]:
        """List available local Ollama models via /api/tags."""
        url = f"{self.cfg.host.rstrip('/')}/api/tags"
        with httpx.Client(timeout=20.0) as client:
            r = client.get(url)
            r.raise_for_status()
            data = r.json() or {}
        models = []
        for m in data.get("models", []) or []:
            name = m.get("name")
            if name:
                models.append(name)
        return models

    def generate(self, prompt: str, *, model: Optional[str] = None) -> LLMResult:
        url = f"{self.cfg.host.rstrip('/')}/api/generate"
        # If model is provided, use it, otherwise use the config default
        target_model = model or self.cfg.model
        payload = {"model": target_model, "prompt": prompt, "stream": False}
        with httpx.Client(timeout=120.0) as client:
            r = client.post(url, json=payload)
            r.raise_for_status()
            data = r.json()
        return LLMResult(text=(data.get("response") or "").strip())
