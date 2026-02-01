from __future__ import annotations

import logging
from dataclasses import dataclass

from lucy_c.asr import FasterWhisperASR
from lucy_c.clawdbot_llm import ClawdbotLLM
from lucy_c.config import LucyConfig
from lucy_c.mimic3_tts import Mimic3TTS
from lucy_c.ollama_llm import OllamaLLM
from lucy_c.history_store import HistoryStore
from lucy_c.text_normalizer import normalize_for_tts


@dataclass
class TurnResult:
    transcript: str
    reply: str
    reply_wav: bytes
    reply_sr: int


DEFAULT_SYSTEM_PROMPT = """Sos Lucy, una asistente virtual inteligente y conversacional.

**Personalidad**:
- Amigable, natural y cercana
- Concisa pero completa en tus respuestas
- Hablás en español argentino (vos, decís, tenés, etc.)

**Instrucciones**:
- Recordá el contexto de la conversación para dar respuestas coherentes
- Si no estás segura, decilo abiertamente
- Evitá respuestas muy largas; sé directa y clara
- Usá un tono conversacional, como si estuvieras hablando con un amigo

**Formato**:
- No uses markdown ni formato especial en tus respuestas
- Respondé en texto plano, listo para ser leído en voz alta
"""

MAX_CONTEXT_CHARS = 4000  # Reserve space for system prompt + current message


class LucyPipeline:
    def __init__(self, cfg: LucyConfig, history: HistoryStore | None = None):
        self.cfg = cfg
        self.log = logging.getLogger("LucyC.Pipeline")
        self.asr = FasterWhisperASR(cfg.asr)

        self.ollama = OllamaLLM(cfg.ollama)
        self.clawdbot = ClawdbotLLM(cfg.clawdbot)

        self.tts = Mimic3TTS(cfg.tts)
        self.history = history

    def _get_chat_messages(self, text: str, session_user: str | None = None) -> list[dict]:
        """Build the message list for the LLM, including history with context window management."""
        import time
        start_time = time.time()
        
        messages = [{"role": "system", "content": DEFAULT_SYSTEM_PROMPT}]
        current_msg = {"role": "user", "content": text}
        
        # Calculate base size (system + current message)
        base_size = len(DEFAULT_SYSTEM_PROMPT) + len(text)
        available_chars = MAX_CONTEXT_CHARS - base_size
        
        if self.history and session_user and available_chars > 0:
            # Fetch more history than we need, then truncate
            past_items = self.history.read(session_user, limit=10)
            history_messages = []
            total_chars = 0
            
            # Process in reverse (newest first) to prioritize recent context
            for item in reversed(past_items):
                user_content = item.get("transcript") or item.get("user_text") or ""
                assistant_content = item.get("reply") or ""
                
                pair_size = len(user_content) + len(assistant_content)
                if total_chars + pair_size > available_chars:
                    self.log.debug("Context truncated: %d chars used of %d available", 
                                 total_chars, available_chars)
                    break
                
                if user_content:
                    history_messages.insert(0, {"role": "user", "content": user_content})
                if assistant_content:
                    history_messages.insert(0, {"role": "assistant", "content": assistant_content})
                
                total_chars += pair_size
            
            messages.extend(history_messages)
            self.log.info("Loaded %d history messages (%d chars)", 
                         len(history_messages), total_chars)
        
        messages.append(current_msg)
        
        elapsed = (time.time() - start_time) * 1000
        self.log.debug("_get_chat_messages took %.1fms", elapsed)
        
        return messages

    def _generate_reply(self, text: str, *, session_user: str | None = None) -> str:
        import time
        start_time = time.time()
        
        provider = (self.cfg.llm.provider or "ollama").lower()
        model = self.cfg.ollama.model
        messages = self._get_chat_messages(text, session_user=session_user)
        
        # Retry logic for transient failures
        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                if provider == "clawdbot":
                    result = self.clawdbot.chat(messages, model=model, user=session_user).text
                else:
                    result = self.ollama.chat(messages, model=model).text
                
                elapsed = (time.time() - start_time) * 1000
                self.log.info("LLM %s replied in %.0fms (attempt %d)", 
                            provider, elapsed, attempt + 1)
                return result
                
            except Exception as e:
                self.log.warning("LLM attempt %d/%d failed: %s", 
                               attempt + 1, max_retries + 1, e)
                
                if attempt < max_retries:
                    import time as time_module
                    wait_time = (2 ** attempt) * 0.5  # Exponential backoff
                    time_module.sleep(wait_time)
                    continue
                
                # Final attempt failed
                self.log.exception("All LLM retries exhausted")
                
                # Friendly fallback message
                if "connection" in str(e).lower() or "timeout" in str(e).lower():
                    return "Perdón, parece que tengo problemas para conectarme. ¿Podés intentar de nuevo en un momento?"
                else:
                    return "Ups, tuve un problema procesando eso. ¿Podrías reformular tu pregunta?"

    def _tts_bytes(self, reply_text: str) -> tuple[bytes, int]:
        """Return (wav_bytes, sample_rate). Empty wav if TTS fails."""
        try:
            tts_text = normalize_for_tts(reply_text)
            tts_res = self.tts.synthesize(tts_text)
            from lucy_c.audio_codec import encode_wav_bytes

            wav = encode_wav_bytes(tts_res.audio_f32, tts_res.sample_rate)
            return wav, tts_res.sample_rate
        except Exception as e:
            self.log.warning("TTS failed (%s). Continuing with text-only.", e)
            return b"", 0

    def run_turn_from_text(self, text: str, *, session_user: str | None = None) -> TurnResult:
        transcript = (text or "").strip()
        if not transcript:
            reply = "Decime algo."
        else:
            reply = self._generate_reply(transcript, session_user=session_user)

        wav, sr = self._tts_bytes(reply)
        return TurnResult(transcript=transcript, reply=reply, reply_wav=wav, reply_sr=sr)

    def run_turn_from_audio(self, audio_f32, *, session_user: str | None = None) -> TurnResult:
        asr_res = self.asr.transcribe(audio_f32)
        transcript = asr_res.text.strip()
        if not transcript:
            reply = "No escuché nada."
        else:
            reply = self._generate_reply(transcript, session_user=session_user)

        wav, sr = self._tts_bytes(reply)
        return TurnResult(transcript=transcript, reply=reply, reply_wav=wav, reply_sr=sr)
