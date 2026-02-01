from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List, Optional

import httpx

from lucy_c.config import OllamaConfig
from lucy_c.models_registry import ModelMetadata, get_enriched_models_list


@dataclass
class LLMResult:
    text: str


class OllamaChatError(Exception):
    def __init__(self, message: str, original_exc: Exception | None = None):
        super().__init__(message)
        self.original_exc = original_exc


class OllamaLLM:
    def __init__(self, cfg: OllamaConfig):
        self.cfg = cfg
        self.log = logging.getLogger("LucyC.Ollama")

    def list_models(self) -> List[str]:
        """List available local Ollama models via /api/tags."""
        tags = self._get_raw_tags()
        models = []
        for m in tags.get("models", []) or []:
            name = m.get("name")
            if name:
                models.append(name)
        return models

    def list_models_detailed(self) -> List[ModelMetadata]:
        """Returns a list of ModelMetadata objects for all local models."""
        tags = self._get_raw_tags()
        raw_models = tags.get("models", []) or []
        return get_enriched_models_list(raw_models)

    def _get_raw_tags(self) -> dict:
        """Helper to fetch raw tags from Ollama API."""
        url = f"{self.cfg.host.rstrip('/')}/api/tags"
        try:
            with httpx.Client(timeout=10.0) as client:
                r = client.get(url)
                r.raise_for_status()
                return r.json() or {}
        except Exception as e:
            self.log.error("Failed to fetch Ollama tags: %s", e)
            return {}

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
            raise OllamaChatError(f"Error generando con Ollama: {e}", e)

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
            raise OllamaChatError(f"No pude conectar con Ollama o el modelo falló: {e}", e)
