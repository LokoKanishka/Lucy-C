from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import httpx

from lucy_c.config import ClawdbotConfig


@dataclass
class LLMResult:
    text: str


class ClawdbotLLM:
    """LLM provider backed by the local Clawdbot Gateway OpenAI-compatible endpoint."""

    def __init__(self, cfg: ClawdbotConfig):
        self.cfg = cfg
        self.log = logging.getLogger("LucyC.Clawdbot")

    def generate(self, prompt: str, *, user: Optional[str] = None) -> LLMResult:
        url = f"{self.cfg.host.rstrip('/')}/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.cfg.token}",
            "Content-Type": "application/json",
            "x-clawdbot-agent-id": self.cfg.agent_id,
        }
        payload = {
            "model": "clawdbot",
            "messages": [{"role": "user", "content": prompt}],
        }
        if user:
            payload["user"] = user

        with httpx.Client(timeout=self.cfg.timeout_s) as client:
            r = client.post(url, headers=headers, json=payload)
            r.raise_for_status()
            data = r.json() or {}

        try:
            content = data["choices"][0]["message"]["content"]
        except Exception:
            content = ""
        return LLMResult(text=(content or "").strip())
