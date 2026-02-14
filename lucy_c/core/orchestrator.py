from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass
from typing import Callable, Optional

from lucy_c.config import LucyConfig
from lucy_c.interfaces.llm import LLMProvider
from lucy_c.interfaces.audio import TTSProvider, ASRProvider

from lucy_c.core.cognitive import CognitiveEngine
from lucy_c.core.senses import SensorySystem
from lucy_c.core.actions import ActionController

from lucy_c.tool_router import ToolRouter
from lucy_c.history_store import HistoryStore, default_history_dir
from lucy_c.facts_store import FactsStore, default_facts_dir

@dataclass
class TurnResult:
    transcript: str
    reply: str
    reply_wav: bytes
    reply_sr: int

class LucyOrchestrator:
    """
    The central nervous system of Lucy-C v2.0.
    Coordinated the Brain (Cognitive), Senses (ASR/TTS), and Body (Action).
    Replaces the legacy 'Moltbot' class.
    """
    def __init__(self, 
                 cfg: LucyConfig, 
                 brain: CognitiveEngine,
                 senses: SensorySystem,
                 body: ActionController,
                 status_callback: Callable[[str, str], None] | None = None):
        
        self.cfg = cfg
        self.brain = brain
        self.senses = senses
        self.body = body
        self.status_callback = status_callback
        self.log = logging.getLogger("LucyC.Orchestrator")
        
        self._init_time = time.time()
        self.log.info("LUCY ORCHESTRATOR ACTIVE.")

    def process_text_input(self, text: str, session_user: str | None = None) -> TurnResult:
        """Run a full turn starting from text."""
        transcript = (text or "").strip()
        if not transcript:
            return TurnResult("", "Decime algo.", b"", 0)
            
        session_user = session_user or "lucy-c:anonymous"
        
        # 1. COGNITION (Think)
        if self.status_callback:
            self.status_callback("Pensando...", "info")
            
        try:
            llm_response = self.brain.think(transcript, session_user=session_user)
            thought_text = llm_response.text
        except Exception as e:
            self.log.error("Cognitive failure: %s", e)
            thought_text = f"Tuve un error cognitivo: {e}"

        # 2. ACTION (Do)
        # Check for tools and execute
        final_text = thought_text
        try:
            # We check if execution changes the text (meaning tools ran and appended output)
            processed_text = self.body.execute(thought_text, context={"session_user": session_user})
            
            if processed_text != thought_text:
                # Tools ran. We need to reflect.
                # Reconstruct context for reflection
                # NOTE: This is slightly redundant with how CognitiveEngine builds context, 
                # but we need the raw messages list for reflection inside brain.
                # To fix this cleanly, `think` should probably return the context used.
                # For now, we re-build context in `reflect` or pass it.
                # Let's rely on `brain.reflect` to handle the chat logic if we pass the context.
                # But `brain.think` didn't return context. 
                # Optimization: `brain` tracks context or we reconstruct it.
                
                # Re-building the message list for reflection:
                original_context = self.brain.build_context(transcript, session_user)
                
                # 3. REFLECTION (Reflect)
                if self.status_callback:
                    self.status_callback("Reflexionando sobre acciones...", "info")
                    
                reflect_resp = self.brain.reflect(processed_text, original_context, session_user=session_user)
                final_text = reflect_resp.text
                
        except Exception as e:
            self.log.error("Action/Reflection failure: %s", e)
            # Fallback to original thought if action failed catastrophically
            final_text = thought_text + f"\n[Error en acción: {e}]"

        # 4. EXPRESSION (Speak)
        if self.status_callback:
            self.status_callback("Sintetizando voz...", "info")
            
        wav, sr = self.senses.speak(final_text)

        return TurnResult(
            transcript=transcript,
            reply=final_text,
            reply_wav=wav,
            reply_sr=sr
        )

    def process_audio_input(self, audio_f32, session_user: str | None = None) -> TurnResult:
        """Run a full turn starting from audio."""
        if self.status_callback:
            self.status_callback("Escuchando...", "info")
            
        transcript = self.senses.listen(audio_f32)
        if not transcript:
             return TurnResult("", "No escuché nada.", b"", 0)
             
        return self.process_text_input(transcript, session_user=session_user)

    # --- Legacy/Helper Accessors for App compatibility ---
    # These effectively expose the internal components so app.py doesn't break immediately
    # or can check status.
    
    @property
    def ollama(self):
        # Bridge to access ollama from brain if needed (e.g. for listing models)
        # Assuming brain.llm is OllamaLLM
        return self.brain.llm 
