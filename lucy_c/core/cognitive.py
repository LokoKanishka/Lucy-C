from __future__ import annotations

import logging
import platform
import uuid
import datetime
import os
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
        reflection_messages = original_context + [
            {"role": "assistant", "content": tool_output},
            {"role": "user", "content": (
                "ACTUALIZACIÓN: Los resultados de las herramientas arriba son la VERDAD ACTUAL Y ABSOLUTA. "
                "Si los resultados contradicen tu conocimiento interno, IGNORÁ tu conocimiento interno. "
                "Dáme la respuesta final para el usuario basada estrictamente en los datos obtenidos. "
                "Mantené tu personalidad argentina pero sé precisa con los datos. "
                "No menciones los bloques [TAG] ni que usaste herramientas."
            )}
        ]
        
        response = self.llm.chat(reflection_messages, model=model_name, user=session_user)
        return response

    def build_context(self, user_text: str, session_user: str) -> List[dict]:
        """Constructs the list of messages including dynamic system prompt & history."""
        # 1. System Prompt & Dynamic Info
        now = datetime.datetime.now()
        dynamic_context = f"\n\n[CONTEXTO DEL SISTEMA - {now.strftime('%d/%m/%Y %H:%M:%S')}]\n"
        dynamic_context += f"- Hora actual: {now.strftime('%H:%M')}\n"
        dynamic_context += f"- Directorio: {os.getcwd()}\n"
        dynamic_context += f"- SO: {platform.system()} {platform.release()}\n"
        
        # Action Enforcer Instructions - simplified and direct
        action_instructions = (
            "\n\n[INSTRUCCIONES DE AGENCIA - PRIORIDAD MÁXIMA]\n"
            "- Tenés capacidad técnica REAL. Si el usuario pide una acción (web, archivos, app), "
            "DEBÉS usar [[herramienta(args)]] de inmediato.\n"
            "- IMPORTANTE: No respondas con texto plano si podés usar una herramienta."
        )
        
        system_content = SYSTEM_PROMPT + dynamic_context + action_instructions
        
        # 2. Facts
        if self.facts:
            fact_summary = self.facts.get_facts_summary(session_user)
            if fact_summary:
                system_content += f"\n\n[DATOS DEL USUARIO]\n{fact_summary}"
        
        # 3. History (truncated)
        messages = [{"role": "system", "content": system_content}]
        
        base_size = len(system_content) + len(user_text)
        available_chars = self.max_context_chars - base_size
        
        if self.history and available_chars > 0:
            past_items = self.history.read(session_user, limit=10)
            history_messages = []
            total_chars = 0
            
            for item in reversed(past_items):
                u_text = item.get("transcript") or item.get("user_text") or ""
                a_text = item.get("reply") or ""
                
                pair_size = len(u_text) + len(a_text)
                if total_chars + pair_size > available_chars:
                    break
                
                if a_text:
                    history_messages.insert(0, {"role": "assistant", "content": a_text})
                if u_text:
                    history_messages.insert(0, {"role": "user", "content": u_text})
                
                total_chars += pair_size
            
            messages.extend(history_messages)
            
        messages.append({"role": "user", "content": user_text})
        return messages
