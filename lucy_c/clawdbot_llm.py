from __future__ import annotations

import json
import logging
import subprocess
from typing import List, Optional, Any

from lucy_c.config import ClawdbotConfig
from lucy_c.interfaces.llm import LLMProvider, LLMResponse


class ClawdbotLLM(LLMProvider):
    """LLM provider backed by the local Clawdbot Gateway OpenAI-compatible endpoint."""

    def __init__(self, cfg: ClawdbotConfig):
        self.cfg = cfg
        self.log = logging.getLogger("LucyC.Clawdbot")

    def list_models(self) -> List[str]:
        """List available agents/models. For now returns the configured agent."""
        return [self.cfg.agent_id or "lucy"]

    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Single-turn generation using the 'clawdbot agent' CLI."""
        target_model = kwargs.get("model")
        user = kwargs.get("user")
        
        # Use the session_user as session-id for Clawdbot's internal memory
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

        if target_model:
            if ":" not in target_model: 
                 cmd[3] = target_model 

        self.log.info("Clawdbot CLI Execution: %s", " ".join(cmd))
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=130)
            if res.returncode != 0:
                self.log.error("Clawdbot CLI failed (exit %d): %s", res.returncode, res.stderr)
                return LLMResponse(text=f"Error (Clawdbot CLI): {res.stderr.strip() or 'Unknown error'}")

            stdout_clean = res.stdout.strip()
            if not stdout_clean:
                return LLMResponse(text="Error: Clawdbot CLI returned no output.")

            try:
                data = json.loads(stdout_clean)
            except json.JSONDecodeError as je:
                self.log.error("Clawdbot CLI returned invalid JSON: %s", stdout_clean)
                return LLMResponse(text=stdout_clean)

            # Robust extraction logic
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
                return LLMResponse(text="Error: No se pudo extraer la respuesta de Clawdbot.", raw_response=data)

            return LLMResponse(text=str(content).strip(), raw_response=data)
        except subprocess.TimeoutExpired:
            self.log.error("Clawdbot CLI timed out")
            return LLMResponse(text="Error: La operación de Clawdbot excedió el tiempo límite.")
        except Exception as e:
            self.log.exception("Clawdbot CLI exception")
            return LLMResponse(text=f"Error inesperado al llamar a Clawdbot: {e}")

    def chat(self, messages: List[dict], **kwargs) -> LLMResponse:
        """Chat wrapper with history compression. 
        We pass the messages in a structured way that works best with the CLI.
        """
        if not messages:
            return LLMResponse(text="")
        
        # Identify System Prompt
        system_msg = next((m.get("content", "") for m in messages if m.get("role") == "system"), "")
        
        # Get history (excluding system prompt)
        history_msgs = [m for m in messages if m.get("role") != "system"]
        
        # Take last 5 messages for context
        recent_history = history_msgs[-6:] if len(history_msgs) > 6 else history_msgs
        
        # Use a flatter format to avoid confusion in the local agent
        prompt_parts = []
        if system_msg:
            prompt_parts.append(system_msg)
            prompt_parts.append("---")
        
        for m in recent_history:
            role = m.get("role", "user").upper()
            content = m.get("content", "")
            prompt_parts.append(f"{role}: {content}")
            
        full_prompt = "\n".join(prompt_parts)
        
        return self.generate(full_prompt, **kwargs)
