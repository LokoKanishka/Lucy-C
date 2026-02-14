from __future__ import annotations

import logging
import platform
import uuid
import datetime
from typing import List, Optional, Dict, Any

from lucy_c.interfaces.llm import LLMProvider, LLMResponse
from lucy_c.history_store import HistoryStore
from lucy_c.facts_store import FactsStore
from lucy_c.prompts import SYSTEM_PROMPT


class CognitiveEngine:
    """
    Decoupled 'Brain' logic for Lucy-C.
    Handles prompt construction, history management, and decision making (think/reflect).
    Does NOT handle audio, tools, or side effects directly.
    """
    
    def __init__(self, llm: LLMProvider, history: HistoryStore, facts: FactsStore, log: logging.Logger | None = None):
        self.llm = llm
        self.history = history
        self.facts = facts
        self.log = log or logging.getLogger("LucyC.Cognitive")
        self.max_context_chars = 16000

    def think(self, user_text: str, session_user: str, model_name: str | None = None) -> LLMResponse:
        """
        Process user input and generate a response/thought.
        Constructs the full prompt with system instructions, facts, and history.
        """
        messages = self.build_context(user_text, session_user)
        
        self.log.info("CognitiveEngine thinking with model: %s for user: %s", model_name, session_user)
        
        # Retry logic could also live here or be injected via policy
        try:
             response = self.llm.chat(messages, model=model_name, enable_tools=True, user=session_user)
             return response
        except Exception as e:
            self.log.error("CognitiveEngine thinking failed: %s", e)
            raise

    def reflect(self, tool_output: str, original_context: List[dict], model_name: str | None = None, session_user: str | None = None) -> LLMResponse:
        """
        Reflect on tool outputs to generate the final response.
        """
        self.log.info("CognitiveEngine reflecting on tool output...")
        
        # Append tool output to the conversation context
        # We need to reconstruct the messages similar to how they were sent, + the tool result
        reflection_messages = original_context + [
            {"role": "assistant", "content": tool_output},
            {"role": "user", "content": "Mirá los resultados de las herramientas arriba y dame una respuesta final natural condensada para el usuario. No repitas los bloques [TAG]."}
        ]
        
        response = self.llm.chat(reflection_messages, model=model_name, user=session_user)
        return response

    def build_context(self, user_text: str, session_user: str) -> List[dict]:
        """Constructs the list of messages including dynamic system prompt & history."""
        # 1. System Prompt & Dynamic Info
        now = datetime.datetime.now()
        dynamic_context = f"\n\n[SISTEMA - {now.strftime('%d/%m/%Y %H:%M:%S')}]\n"
        dynamic_context += f"- Hora actual: {now.strftime('%H:%M')}\n"
        dynamic_context += f"- SO: {platform.system()} {platform.release()}\n"
        
        system_content = SYSTEM_PROMPT + dynamic_context
        
        # 2. Facts
        if self.facts:
            fact_summary = self.facts.get_facts_summary(session_user)
            if fact_summary:
                system_content += f"\n\n{fact_summary}"
        
        messages = [{"role": "system", "content": system_content}]
        current_msg = {"role": "user", "content": user_text}
        
        # 3. History (truncated)
        base_size = len(system_content) + len(user_text)
        available_chars = self.max_context_chars - base_size
        
        if self.history and available_chars > 0:
            past_items = self.history.read(session_user, limit=10)
            history_messages = []
            total_chars = 0
            
            for item in reversed(past_items):
                user_content = item.get("transcript") or item.get("user_text") or ""
                assistant_content = item.get("reply") or ""
                
                pair_size = len(user_content) + len(assistant_content)
                if total_chars + pair_size > available_chars:
                    break
                
                if assistant_content:
                    history_messages.insert(0, {"role": "assistant", "content": assistant_content})
                if user_content:
                    history_messages.insert(0, {"role": "user", "content": user_content})
                
                total_chars += pair_size
            
            messages.extend(history_messages)
            
        messages.append(current_msg)
        
        # 4. Will Injection (Action enforcer)
        system_reminder = {
            "role": "system", 
            "content": (
                "CRÍTICO: Recordá que TIENES capacidad técnica real de operar este sistema. "
                "Si el usuario pide una acción (ej. abrir app, buscar en web, leer, interactuar), "
                "ESTÁS OBLIGADA a responder EXCLUSIVAMENTE ejecutando la herramienta con el formato [[herramienta(argumentos)]]. "
                "No relates lo que vas a hacer. No te disculpes ni pidas permiso. Ejecuta el comando directamente."
            )
        }
        messages.append(system_reminder)
        
        return messages
