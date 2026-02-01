from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List, Optional

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
        try:
            with httpx.Client(timeout=10.0) as client:
                r = client.get(url)
                r.raise_for_status()
                data = r.json() or {}
            models = []
            for m in data.get("models", []) or []:
                name = m.get("name")
                if name:
                    models.append(name)
            return models
        except Exception as e:
            self.log.error("Failed to list Ollama models: %s", e)
            return []

    def generate(self, prompt: str, *, model: Optional[str] = None) -> LLMResult:
        """Simple single-prompt generation."""
        url = f"{self.cfg.host.rstrip('/')}/api/generate"
        target_model = model or self.cfg.model
        payload = {"model": target_model, "prompt": prompt, "stream": False}
        try:
            with httpx.Client(timeout=120.0) as client:
                r = client.post(url, json=payload, timeout=120.0)
                r.raise_for_status()
                data = r.json()
            return LLMResult(text=(data.get("response") or "").strip())
        except Exception as e:
            self.log.error("Ollama generate failed: %s", e)
            return LLMResult(text=f"Error (Ollama): {e}")

    def chat(self, messages: List[dict], *, model: Optional[str] = None) -> LLMResult:
        """Multi-turn chat completion using /api/chat."""
        url = f"{self.cfg.host.rstrip('/')}/api/chat"
        target_model = model or self.cfg.model
        payload = {"model": target_model, "messages": messages, "stream": False}
        try:
            with httpx.Client(timeout=120.0) as client:
                r = client.post(url, json=payload, timeout=120.0)
                r.raise_for_status()
                data = r.json()
            # Response in data["message"]["content"] for /api/chat
            content = data.get("message", {}).get("content") or ""
            return LLMResult(text=content.strip())
        except Exception as e:
            self.log.error("Ollama chat failed: %s", e)
            return LLMResult(text=f"Error (Ollama Chat): {e}")
