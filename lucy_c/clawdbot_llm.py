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
        """Single-turn generation using the 'clawdbot agent' CLI."""
        # Use the session_user as session-id for Clawdbot's internal memory
        # to ensure the CLI itself can manage context if needed.
        session_id = user or "lucy-c:anonymous"
        
        cmd = [
            "clawdbot",
            "agent",
            "--agent", self.cfg.agent_id or "lucy",
            "--session-id", session_id,
            "--message", prompt,
            "--json",
            "--timeout", "120"
        ]

        if model:
            # If the user provides a specific model, we can try passing it as the agent
            # if the agent_id is generic, but the ticket says "by flag CLI".
            # We'll stick to the agent_id from config or let model override it if it looks like an agent id.
            if ":" not in model: # Crude check to see if it's a clawdbot agent ID vs ollama model
                 cmd[3] = model 

        self.log.info("Clawdbot CLI Execution: %s", " ".join(cmd))
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=130)
            if res.returncode != 0:
                self.log.error("Clawdbot CLI failed (exit %d): %s", res.returncode, res.stderr)
                return LLMResult(text=f"Error (Clawdbot CLI): {res.stderr.strip() or 'Unknown error'}")

            stdout_clean = res.stdout.strip()
            if not stdout_clean:
                return LLMResult(text="Error: Clawdbot CLI returned no output.")

            try:
                data = json.loads(stdout_clean)
            except json.JSONDecodeError as je:
                self.log.error("Clawdbot CLI returned invalid JSON: %s", stdout_clean)
                # Fallback to raw text if it's not JSON but might be the answer
                return LLMResult(text=stdout_clean)

            # Robust extraction: 
            # 1. Look for result.payloads[0].text (Clawdbot standard)
            # 2. Look for 'reply' or 'message' keys
            content = ""
            if isinstance(data, dict):
                result_obj = data.get("result", {})
                payloads = result_obj.get("payloads", []) if isinstance(result_obj, dict) else []
                if payloads and isinstance(payloads, list):
                    content = payloads[0].get("text") or ""
                
                if not content:
                    content = data.get("reply") or data.get("message") or data.get("content") or ""
            
            if not content:
                self.log.warning("Clawdbot CLI returned empty content: %s", data)
                return LLMResult(text="Error: No se pudo extraer la respuesta de Clawdbot.")

            return LLMResult(text=str(content).strip())
        except subprocess.TimeoutExpired:
            self.log.error("Clawdbot CLI timed out")
            return LLMResult(text="Error: La operación de Clawdbot excedió el tiempo límite.")
        except Exception as e:
            self.log.exception("Clawdbot CLI exception")
            return LLMResult(text=f"Error inesperado al llamar a Clawdbot: {e}")

    def chat(self, messages: list[dict], *, model: Optional[str] = None, user: Optional[str] = None) -> LLMResult:
        """Chat wrapper. Since CLI handles session internally via --session-id, 
        we just send the last message here."""
        if not messages:
            return LLMResult(text="")
        
        last_msg = messages[-1].get("content", "")
        return self.generate(last_msg, model=model, user=user)
