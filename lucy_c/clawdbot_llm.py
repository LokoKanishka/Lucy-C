from __future__ import annotations

import json
import logging
import subprocess
from dataclasses import dataclass
from typing import Optional

from lucy_c.config import ClawdbotConfig


@dataclass
class LLMResult:
    text: str


class ClawdbotLLM:
    """LLM provider backed by the local Clawdbot Gateway OpenAI-compatible endpoint."""

    def __init__(self, cfg: ClawdbotConfig):
        self.cfg = cfg
        self.log = logging.getLogger("LucyC.Clawdbot")

    def generate(self, prompt: str, *, model: Optional[str] = None, user: Optional[str] = None) -> LLMResult:
        # Use Clawdbot CLI (Opción B del handoff)
        # clawdbot agent --agent <id> --message "<prompt>" --json
        cmd = [
            "clawdbot",
            "agent",
            "--agent",
            self.cfg.agent_id or "lucy",
            "--message",
            prompt,
            "--json",
        ]

        if model:
            # Note: Current clawdbot agent CLI turn doesn't support --model override flag.
            # It will use the agent's configured model or the global default.
            pass

        if user:
            # Optionally pass session-id if needed or user context
            pass

        self.log.info("Running: %s", " ".join(cmd))
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if res.returncode != 0:
                self.log.error("Clawdbot CLI failed (exit %d): %s", res.returncode, res.stderr)
                return LLMResult(text=f"Error Clawdbot: {res.stderr.strip()}")

            data = json.loads(res.stdout)
            # Response format for 'clawdbot agent' CLI (non-OpenAI)
            # Result is usually in data["result"]["payloads"][0]["text"]
            try:
                payloads = data.get("result", {}).get("payloads", [])
                if payloads:
                    content = payloads[0].get("text") or ""
                else:
                    content = data.get("reply") or data.get("message") or ""
            except Exception:
                content = data.get("reply") or data.get("message") or ""
            
            return LLMResult(text=str(content).strip())
        except Exception as e:
            self.log.exception("Clawdbot CLI exception")
            return LLMResult(text=f"Error exception: {e}")
