from __future__ import annotations

import logging
from dataclasses import dataclass

from lucy_c.asr import FasterWhisperASR
from lucy_c.clawdbot_llm import ClawdbotLLM
from lucy_c.config import LucyConfig
from lucy_c.mimic3_tts import Mimic3TTS
from lucy_c.ollama_llm import OllamaLLM
from lucy_c.history_store import HistoryStore
from lucy_c.facts_store import FactsStore
from lucy_c.text_normalizer import normalize_for_tts
from lucy_c.prompts import SYSTEM_PROMPT, PROMPT_VERSION
from lucy_c.tool_router import ToolRouter, ToolResult
from lucy_c.tools.file_tools import tool_read_file, tool_write_file


@dataclass
class TurnResult:
    transcript: str
    reply: str
    reply_wav: bytes
    reply_sr: int


# The canonical composition
DEFAULT_SYSTEM_PROMPT = SYSTEM_PROMPT

MAX_CONTEXT_CHARS = 4000  # Reserve space for system prompt + current message


class Moltbot:
    def __init__(self, cfg: LucyConfig, history: HistoryStore | None = None, facts: FactsStore | None = None, status_callback: Callable[[str, str], None] | None = None):
        self.cfg = cfg
        self.log = logging.getLogger("Moltbot")
        self.log.info("LUCY CORE (Prompt v%s) initializing...", PROMPT_VERSION)
        self.asr = FasterWhisperASR(cfg.asr)

        self.ollama = OllamaLLM(cfg.ollama)
        self.clawdbot = ClawdbotLLM(cfg.clawdbot)

        self.tts = Mimic3TTS(cfg.tts)
        self.history = history
        self.facts = facts
        self.status_callback = status_callback
        
        # Tool Orchestration
        self.tool_router = ToolRouter()
        self._register_default_tools()
        
        # Phase 4/5: Sensors and Actuators (The "Body")
        # These are lazy-loaded to ensure Core stability even if dependencies are missing.
        self._eyes = None
        self._hands = None
        self._body_available = True

    @property
    def eyes(self):
        if self._eyes is None:
            try:
                from lucy_c.tools.vision_tool import SystemEyes
                self._eyes = SystemEyes(self.ollama)
            except Exception as e:
                self.log.warning("Lucy Body: Eyes (Vision) not available: %s", e)
                self._body_available = False
        return self._eyes

    @property
    def hands(self):
        if self._hands is None:
            try:
                from lucy_c.tools.automation_tool import SystemHands
                self._hands = SystemHands()
            except Exception as e:
                self.log.warning("Lucy Body: Hands (Automation) not available: %s", e)
                self._body_available = False
        return self._hands

    def _register_default_tools(self):
        """Register core tools with the ToolRouter."""
        def _safe_guard(args: list[str], action: str) -> str | None:
            """Check if safe mode is on and we need confirmation."""
            if self.cfg.safe_mode:
                # Basic confirmation check: if 'confirm' or 'si' is not in the text
                # this is handled by the reflection loop asking for it.
                # For now, just return a warning if safe_mode is hard-on.
                return f"Acción '{action}' bloqueada por Modo Seguro. Por favor, confirmá explícitamente."
            return None

        def tool_remember(args, ctx):
            session_user = ctx.get("session_user")
            if not self.facts or not session_user:
                return ToolResult(False, "Almacén de hechos no disponible.", "⚠️ ERROR CORE")
            if len(args) < 2:
                return ToolResult(False, "Faltan argumentos para remember(clave, valor).", "⚠️ ERROR CORE")
            
            # Sensitivity check (example key)
            if self.cfg.safe_mode and args[0] in ["password", "token", "secreto"]:
                return ToolResult(False, f"Seguridad: No puedo guardar '{args[0]}' en Modo Seguro.", "🛡️ SEGURIDAD")

            self.facts.set_fact(session_user, args[0], args[1])
            return ToolResult(True, f"Recordado: {args[0]} = {args[1]}", "🧠 MEMORIA")

        def tool_forget(args, ctx):
            if self.cfg.safe_mode:
                return ToolResult(False, "Olvidar está bloqueado en Modo Seguro por precaución.", "🛡️ SEGURIDAD")
            
            session_user = ctx.get("session_user")
            if not self.facts or not session_user:
                return ToolResult(False, "Almacén de hechos no disponible.", "⚠️ ERROR CORE")
            if not args:
                return ToolResult(False, "Falta argumento para forget(clave).", "⚠️ ERROR CORE")
            self.facts.remove_fact(session_user, args[0])
            return ToolResult(True, f"Olvidado: {args[0]}", "🧠 MEMORIA")

        def tool_screenshot(args, ctx):
            if not self.eyes:
                return ToolResult(False, "Sensores de visión no disponibles.", "⚠️ ERROR CORE")
            return ToolResult(True, self.eyes.describe_screen(), "👁️ OJOS")

        def tool_type(args, ctx):
            if not self.hands or not args:
                return ToolResult(False, "Actuadores no disponibles o faltan argumentos.", "🖐️ MANOS")
            return ToolResult(True, self.hands.type_text(args[0]), "🖐️ MANOS")

        def tool_press(args, ctx):
            if not self.hands or not args:
                return ToolResult(False, "Actuadores no disponibles o faltan argumentos.", "🖐️ MANOS")
            return ToolResult(True, self.hands.press_key(args[0]), "🖐️ MANOS")

        def tool_click(args, ctx):
            if not self.hands:
                return ToolResult(False, "Actuadores no disponibles.", "🖐️ MANOS")
            
            # click(x, y, button, clicks)
            x = int(args[0]) if len(args) > 0 and args[0].isdigit() else None
            y = int(args[1]) if len(args) > 1 and args[1].isdigit() else None
            button = args[2] if len(args) > 2 else 'left'
            clicks = int(args[3]) if len(args) > 3 and args[3].isdigit() else 1
            
            return ToolResult(True, self.hands.click(x, y, button, clicks), "🖐️ MANOS")

        def tool_hotkey(args, ctx):
            if not self.hands or not args:
                return ToolResult(False, "Actuadores no disponibles o faltan argumentos.", "🖐️ MANOS")
            return ToolResult(True, self.hands.hotkey(*args), "🖐️ MANOS")

        def tool_wait(args, ctx):
            if not args or not self.hands:
                return ToolResult(False, "Falta argumento para wait(segundos).", "🖐️ MANOS")
            try:
                seconds = float(args[0])
                return ToolResult(True, self.hands.wait(seconds), "🖐️ MANOS")
            except:
                return ToolResult(False, "Argumento de wait debe ser un número.", "🖐️ MANOS")

        def tool_move(args, ctx):
            if len(args) < 2 or not self.hands:
                return ToolResult(False, "Faltan coordenadas para move(x, y).", "🖐️ MANOS")
            try:
                x, y = int(args[0]), int(args[1])
                return ToolResult(True, self.hands.move_to(x, y), "🖐️ MANOS")
            except Exception as e:
                return ToolResult(False, f"Error en move: {e}", "🖐️ MANOS")

        self.tool_router.register_tool("remember", tool_remember)
        self.tool_router.register_tool("forget", tool_forget)
        self.tool_router.register_tool("screenshot", tool_screenshot)
        self.tool_router.register_tool("type", tool_type)
        self.tool_router.register_tool("press", tool_press)
        self.tool_router.register_tool("click", tool_click)
        self.tool_router.register_tool("hotkey", tool_hotkey)
        self.tool_router.register_tool("wait", tool_wait)
        self.tool_router.register_tool("move", tool_move)
        self.tool_router.register_tool("read_file", tool_read_file)
        self.tool_router.register_tool("write_file", tool_write_file)

    async def _execute_tools(self, text: str, context: Dict[str, Any]) -> str:
        """Execute tools found in text and return text with results appended."""
        import re
        tool_pattern = re.compile(r'\[\[\s*(\w+)\s*\((.*?)\)\s*\]\]')
        matches = tool_pattern.findall(text)
        
        if matches and self.status_callback:
            # Map tools to user-friendly messages
            messages = {
                "screenshot": "Mirando pantalla...",
                "click": "Haciendo clic...",
                "type": "Escribiendo...",
                "hotkey": "Usando atajo de teclado...",
                "move": "Moviendo el mouse...",
                "read_file": "Leyendo archivo...",
                "write_file": "Escribiendo archivo...",
                "remember": "Guardando en memoria...",
                "forget": "Olvidando...",
            }
            # Pick first tool's message as general status
            first_tool = matches[0][0]
            msg = messages.get(first_tool, "Ejecutando herramientas...")
            self.status_callback(msg, "warning")

        return self.tool_router.parse_and_execute(text, context)

    def switch_brain(self, model_name: str, provider: str = "ollama", session_user: str | None = None):
        """Perform a formal brain exchange. If session_user is provided, persist the choice."""
        old_model = self.cfg.ollama.model
        old_provider = self.cfg.llm.provider
        
        provider = provider.lower()
        self.cfg.llm.provider = provider
        if provider == "ollama":
            self.cfg.ollama.model = model_name
            self.ollama.cfg.model = model_name
        
        if self.facts and session_user:
            self.facts.set_fact(session_user, "selected_model", model_name)
            self.facts.set_fact(session_user, "selected_provider", provider)
            self.log.info("Persisted brain choice for %s: %s (%s)", session_user, model_name, provider)
        
        self.log.info("BRAIN EXCHANGE: %s (%s) -> %s (%s)", 
                     old_provider, old_model, provider, model_name)

    def _apply_persisted_brain(self, session_user: str | None = None):
        """Load and apply persisted brain choice from FactsStore."""
        if not self.facts or not session_user:
            return
        
        facts = self.facts.get_facts(session_user)
        persisted_model = facts.get("selected_model")
        persisted_provider = facts.get("selected_provider")
        
        if persisted_model and (persisted_model != self.cfg.ollama.model or persisted_provider != self.cfg.llm.provider):
            self.log.info("Applying persisted brain for %s: %s (%s)", 
                         session_user, persisted_model, persisted_provider)
            # Use internal direct update to avoid re-persisting the same data
            self.cfg.llm.provider = persisted_provider
            if persisted_provider == "ollama":
                self.cfg.ollama.model = persisted_model
                self.ollama.cfg.model = persisted_model

    def _get_chat_messages(self, text: str, session_user: str | None = None) -> list[dict]:
        """Build the message list for the LLM, including history with context window management."""
        import time
        start_time = time.time()
        
        # Phase 5: Facts Enrichment
        system_content = DEFAULT_SYSTEM_PROMPT
        if self.facts and session_user:
            fact_summary = self.facts.get_facts_summary(session_user)
            if fact_summary:
                system_content += f"\n\n{fact_summary}"
        
        messages = [{"role": "system", "content": system_content}]
        current_msg = {"role": "user", "content": text}
        
        # Calculate base size (system + current message)
        base_size = len(system_content) + len(text)
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
        
        # Phase 1: Force ollama for now, though we keep the config flexibility
        session_user = session_user or "lucy-c:anonymous"
        self._apply_persisted_brain(session_user)
        
        provider = (self.cfg.llm.provider or "ollama").lower()
        model = self.cfg.ollama.model
        messages = self._get_chat_messages(text, session_user=session_user)
        
        self.log.info("Moltbot processing prompt using %s (%s)", provider, model)
        
        # Retry logic for transient failures
        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                # Hint on final attempt
                current_messages = messages
                if attempt == max_retries and attempt > 0:
                    self.log.info("Moltbot applying final-retry hint to messages.")
                    hint = "Por favor, respondé de forma clara y completa. Si vas a usar una herramienta, recordá usar el formato [[tool()]]."
                    current_messages = messages + [{"role": "user", "content": hint}]

                if provider == "clawdbot":
                    result = self.clawdbot.chat(current_messages, model=model, user=session_user).text
                else:
                    result = self.ollama.chat(current_messages, model=model).text
                
                # Refined error detection: empty OR suspiciously short
                stripped_res = (result or "").strip()
                if not stripped_res or len(stripped_res) < 3:
                    self.log.warning("Moltbot brain returned invalid response: '%s' (attempt %d/%d)", 
                                   stripped_res, attempt + 1, max_retries + 1)
                    raise ValueError("Respuesta inválida o vacía del cerebro")

                # Phase 4: Trigger tool execution if tool calls are present
                processed_result = self._execute_tools(result, session_user=session_user)
                
                # Phase 5: Reflection Loop
                # If tools were executed (result != processed_result), ask the brain to reflect.
                if processed_result != result:
                    self.log.info("Moltbot entering reflection loop...")
                    reflection_messages = messages + [
                        {"role": "assistant", "content": processed_result},
                        {"role": "user", "content": "Mirá los resultados de las herramientas arriba y dame una respuesta final natural condensada para el usuario. No repitas los bloques [TAG]."}
                    ]
                    
                    if provider == "clawdbot":
                        reflection_res = self.clawdbot.chat(reflection_messages, model=model, user=session_user).text
                    else:
                        reflection_res = self.ollama.chat(reflection_messages, model=model).text
                    
                    if reflection_res and len(reflection_res.strip()) > 2:
                        result = reflection_res.strip()
                    else:
                        result = processed_result
                else:
                    result = processed_result
                
                elapsed = (time.time() - start_time) * 1000
                self.log.info("Moltbot response received in %.0fms: %s", 
                            elapsed, result[:100] + "..." if len(result) > 100 else result)
                return result
                
            except Exception as e:
                self.log.warning("Moltbot brain attempt %d/%d failed: %s", 
                               attempt + 1, max_retries + 1, e)
                
                if attempt < max_retries:
                    import time as time_module
                    wait_time = (2 ** attempt) * 0.5  # Exponential backoff
                    time_module.sleep(wait_time)
                    continue
                
                # Final attempt failed
                self.log.exception("All Moltbot retries exhausted")
                
                # Semantic fallbacks
                err_str = str(e).lower()
                if "connection" in err_str or "timeout" in err_str or "unreachable" in err_str:
                    return "Perdón, che, parece que tengo un problema de conexión con mi cerebro local. ¿Te fijás si Ollama está corriendo? Intentá de nuevo en un ratito."
                elif "venerable" in err_str or "empty" in err_str or "inválida" in err_str:
                    return "Che, mi cerebro se quedó en blanco. ¿Podrías preguntarme de otra forma o repetirme lo último?"
                else:
                    return "Ups, algo no salió bien procesando eso. ¿Probamos de nuevo con otra frase?"

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
