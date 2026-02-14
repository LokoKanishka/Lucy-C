from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List, Optional

import requests

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
            r = requests.get(url, timeout=10.0)
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
            r = requests.post(url, json=payload, timeout=120.0)
            r.raise_for_status()
            data = r.json()
            return LLMResult(text=(data.get("response") or "").strip())
        except Exception as e:
            self.log.error("Ollama generate failed: %s", e)
            raise OllamaChatError(f"Error generando con Ollama: {e}", e)

    def chat(self, messages: List[dict], *, model: Optional[str] = None, enable_tools: bool = False) -> LLMResult:
        """Multi-turn chat completion using /api/chat."""
        url = f"{self.cfg.host.rstrip('/')}/api/chat"
        target_model = model or self.cfg.model
        payload = {"model": target_model, "messages": messages, "stream": False}
        
        # Enable native tool calling if requested
        if enable_tools:
            try:
                from lucy_c.ollama_tools import OLLAMA_TOOLS
                payload["tools"] = OLLAMA_TOOLS
                self.log.debug("Ollama tools enabled: %d tools registered", len(OLLAMA_TOOLS))
            except ImportError:
                self.log.warning("ollama_tools module not found, tools disabled")
        
        try:
            r = requests.post(url, json=payload, timeout=120.0)
            r.raise_for_status()
            data = r.json()
            # Response in data["message"]["content"] for /api/chat
            msg = data.get("message", {})
            content = msg.get("content") or ""
            tool_calls = msg.get("tool_calls") or []
            thinking = msg.get("thinking") or ""

            self.log.debug("RAW content: %s", content)
            if tool_calls:
                self.log.info("NATIVE tool_calls detected: %s", tool_calls)

            # Bridge: Convert native tool calls to Moltbot's [[tool(args)]] format
            if tool_calls:
                tool_lines = []
                for call in tool_calls:
                    fn = call.get("function", {})
                    name = fn.get("name")
                    # Strip 'tool.' prefix if Ollama adds it
                    if name and name.startswith("tool."):
                        name = name[5:]
                    args = fn.get("arguments", {})
                    if name:
                        # Convert dict args to positional string args for smart_split
                        if isinstance(args, dict):
                            arg_strs = [f'"{v}"' if isinstance(v, str) else str(v) for v in args.values()]
                        else:
                            arg_strs = [str(args)]
                        tool_lines.append(f"[[{name}({', '.join(arg_strs)})]]")
                
                if tool_lines:
                    bridge_text = " ".join(tool_lines)
                    if content:
                        content = f"{content}\n\n{bridge_text}"
                    else:
                        content = bridge_text
            
            final_content = content.strip()
            self.log.debug("FINAL content after bridge: %s", final_content)
            return LLMResult(text=final_content)
        except Exception as e:
            self.log.error("Ollama chat failed: %s", e)
            raise OllamaChatError(f"No pude conectar con Ollama o el modelo falló: {e}", e)
