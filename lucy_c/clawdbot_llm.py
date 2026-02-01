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
        """Single-turn generation, but uses user as session_id for continuity."""
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

        # Use the session_user as session-id for memory
        if user:
            cmd.extend(["--session-id", user])

        if model:
            # Note: Current clawdbot agent CLI doesn't support easy --model override.
            pass

        self.log.info("Running: %s", " ".join(cmd))
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if res.returncode != 0:
                self.log.error("Clawdbot CLI failed (exit %d): %s", res.returncode, res.stderr)
                return LLMResult(text=f"Error (Clawdbot CLI): {res.stderr.strip()}")

            try:
                data = json.loads(res.stdout)
            except json.JSONDecodeError as je:
                self.log.error("Clawdbot CLI returned invalid JSON: %s", res.stdout)
                return LLMResult(text=f"Error (Clawdbot JSON): {je}")

            # Extract content from result payloads
            try:
                payloads = data.get("result", {}).get("payloads", [])
                if payloads:
                    content = payloads[0].get("text") or ""
                else:
                    content = data.get("reply") or data.get("message") or ""
            except Exception:
                content = data.get("reply") or data.get("message") or ""
            
            if not content:
                self.log.warning("Clawdbot CLI returned empty content: %s", data)
                content = "Error: Respuesta vacía de Clawdbot."

            return LLMResult(text=str(content).strip())
        except subprocess.TimeoutExpired:
            self.log.error("Clawdbot CLI timed out")
            return LLMResult(text="Error: Clawdbot excedió el tiempo de espera.")
        except Exception as e:
            self.log.exception("Clawdbot CLI exception")
            return LLMResult(text=f"Error (Clawdbot Exception): {e}")

    def chat(self, messages: list[dict], *, model: Optional[str] = None, user: Optional[str] = None) -> LLMResult:
        """Chat wrapper. Since CLI handles session internally via --session-id, 
        we just send the last message here."""
        if not messages:
            return LLMResult(text="")
        
        last_msg = messages[-1].get("content", "")
        return self.generate(last_msg, model=model, user=user)
