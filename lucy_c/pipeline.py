from __future__ import annotations

import logging
import time
import traceback
import platform
import uuid
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass

from lucy_c.asr import FasterWhisperASR
from lucy_c.clawdbot_llm import ClawdbotLLM
from lucy_c.config import LucyConfig
from lucy_c.mimic3_tts import Mimic3TTS

# Try to import XTTS (optional)
try:
    from lucy_c.services.xtts_service import XTTSService
    XTTS_AVAILABLE = True
except ImportError:
    XTTS_AVAILABLE = False
from lucy_c.ollama_llm import OllamaLLM
from lucy_c.history_store import HistoryStore, default_history_dir
from lucy_c.facts_store import FactsStore, default_facts_dir
from lucy_c.text_normalizer import normalize_for_tts
from lucy_c.prompts import SYSTEM_PROMPT, PROMPT_VERSION
from lucy_c.tool_router import ToolRouter, ToolResult
from lucy_c.tools.file_tools import tool_read_file, tool_write_file
from lucy_c.tools.business_tools import tool_check_shipping, tool_process_payment, tool_generate_budget_pdf
from lucy_c.tools.web_tools import tool_web_search, tool_open_url, tool_read_url
from lucy_c.tools.os_tools import tool_os_run, tool_window_manager
from lucy_c.tools.vision_ui_tools import tool_scan_ui, tool_click_text, tool_peek_desktop
from lucy_c.tools.n8n_tools import create_n8n_tools
from lucy_c.tools.cognitive_tools import create_cognitive_tools
from lucy_c.rag_engine import MemoryEngine
from lucy_c.tools.knowledge_tools import create_knowledge_tools


@dataclass
class TurnResult:
    transcript: str
    reply: str
    reply_wav: bytes
    reply_sr: int


import os

# The canonical composition
DEFAULT_SYSTEM_PROMPT = SYSTEM_PROMPT

MAX_CONTEXT_CHARS = 4000  # Reserve space for system prompt + current message
LOCAL_ONLY = os.environ.get("LUCY_LOCAL_ONLY", "1") == "1"


class Moltbot:
    def __init__(self, cfg: LucyConfig, history: HistoryStore | None = None, facts: FactsStore | None = None, status_callback: Callable[[str, str], None] | None = None):
        self._init_time = time.time()
        self.cfg = cfg
        self.log = logging.getLogger("Moltbot")
        self.log.info("LUCY CORE (Prompt v%s) initializing...", PROMPT_VERSION)
        
        if LOCAL_ONLY and self.cfg.llm.provider not in ["ollama", "clawdbot"]:
            self.log.info("LUCY_LOCAL_ONLY=1 active. Cloud providers disabled. Falling back to ollama.")
            self.cfg.llm.provider = "ollama"

        self.asr = FasterWhisperASR(cfg.asr)
        self.ollama = OllamaLLM(cfg.ollama)
        
        # Model Fallback: Ensure the configured model exists in Ollama
        if LOCAL_ONLY:
            self._validate_model_fallback()

        # Clawdbot is treated as local (CLI wrapper)
        self.clawdbot = ClawdbotLLM(cfg.clawdbot)

        self.tts = self._initialize_tts(cfg)
        self.history = history or HistoryStore(default_history_dir())
        self.facts = facts or FactsStore(default_facts_dir())
        self.status_callback = status_callback
        
        # Tool Orchestration
        self.tool_router = ToolRouter()
        
        # Initialize RAG Memory Engine
        try:
            self.memory = MemoryEngine(persist_directory="data/chroma_db")
            self.log.info("RAG Memory Engine initialized.")
        except Exception as e:
            self.log.warning("Failed to initialize RAG memory: %s. Memory features disabled.", e)
            self.memory = None
        
        # Virtual Display (optional, for autonomous non-intrusive operation)
        self.virtual_display = None
        enable_virtual = os.environ.get("LUCY_VIRTUAL_DISPLAY", "0") == "1"
        if enable_virtual:
            try:
                from lucy_c.services.virtual_display import VirtualDisplay
                self.virtual_display = VirtualDisplay()
                if self.virtual_display.start():
                    self.log.info("Virtual Display started on :99 for non-intrusive operation")
                else:
                    self.virtual_display = None
            except Exception as e:
                self.log.warning("Virtual Display not available: %s", e)
                self.virtual_display = None
        
        # Phase 4/5: Sensors and Actuators (The "Body")
        self._eyes = None
        self._hands = None
        self._body_available = True

        self._register_default_tools()
    
    def _initialize_tts(self, cfg):
        """Initialize TTS service with fallback."""
        provider = getattr(cfg.tts, 'provider', 'mimic3')
        
        # Try XTTS if requested
        if provider == "xtts" and XTTS_AVAILABLE:
            try:
                tts = XTTSService(cfg.tts)
                if tts._enabled:
                    self.log.info("✅ Using XTTS neural voice (GPU-accelerated)")
                    return tts
                else:
                    self.log.warning("XTTS initialization failed, falling back to Mimic3")
            except Exception as e:
                self.log.warning(f"XTTS failed ({e}), falling back to Mimic3")
        elif provider == "xtts" and not XTTS_AVAILABLE:
            self.log.warning("XTTS requested but not installed. Install with: pip install TTS torch")
        
        # Fallback to Mimic3
        self.log.info("Using Mimic3 TTS")
        return Mimic3TTS(cfg.tts)

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

        def tool_get_info(args, ctx):
            import datetime
            import platform
            tipo = args[0].lower() if args else "time"
            if tipo == "time":
                now = datetime.datetime.now().strftime("%H:%M:%S")
                return ToolResult(True, f"La hora actual es: {now}", "⚙️ SISTEMA")
            elif tipo == "date":
                today = datetime.datetime.now().strftime("%d/%m/%Y")
                return ToolResult(True, f"La fecha de hoy es: {today}", "⚙️ SISTEMA")
            elif tipo == "os":
                info = f"{platform.system()} {platform.release()}"
                return ToolResult(True, f"Información del sistema: {info}", "⚙️ SISTEMA")
            else:
                return ToolResult(False, f"Tipo de información '{tipo}' no soportado.", "⚠️ ERROR CORE")

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
        self.tool_router.register_tool("get_info", tool_get_info)
        self.tool_router.register_tool("check_shipping", tool_check_shipping)
        self.tool_router.register_tool("process_payment", tool_process_payment)
        self.tool_router.register_tool("generate_budget_pdf", tool_generate_budget_pdf)
        self.tool_router.register_tool("search_web", tool_web_search)
        self.tool_router.register_tool("open_url", tool_open_url)
        self.tool_router.register_tool("read_url", tool_read_url)
        self.tool_router.register_tool("os_run", tool_os_run)
        self.tool_router.register_tool("window_manager", tool_window_manager)
        self.tool_router.register_tool("windows", tool_window_manager)
        
        # Aliases for common model hallucinations
        self.tool_router.register_tool("browser.open_url", tool_open_url)
        self.tool_router.register_tool("google_search", tool_web_search)
        self.tool_router.register_tool("web_search", tool_web_search)
        self.tool_router.register_tool("browser.run", tool_os_run)
        self.tool_router.register_tool("browser.screenshot", tool_screenshot)
        
        # n8n orchestration tools
        n8n_tools = create_n8n_tools(self.cfg.n8n)
        self.tool_router.register_tool("trigger_workflow", n8n_tools["trigger_workflow"])
        
        # Cognitive delegation tools (require n8n)
        cognitive_tools = create_cognitive_tools(n8n_tools)
        self.tool_router.register_tool("ask_sota", cognitive_tools["ask_sota"])
        
        # Knowledge/Memory tools (require RAG memory engine)
        if self.memory:
            knowledge_tools = create_knowledge_tools(self.memory)
            self.tool_router.register_tool("memorize_file", knowledge_tools["memorize_file"])
            self.tool_router.register_tool("recall", knowledge_tools["recall"])
            self.tool_router.register_tool("memory_stats", knowledge_tools["memory_stats"])
        
        # We handle 'assistant' specially if it's used as a generic wrapper
        def tool_assistant(args, ctx):
            if not args: return ToolResult(False, "No args for assistant wrapper", "⚠️")
            
            inner_tool = args[0]
            inner_args = args[1:]
            
            # Robustness: sometimes models put the tool name in quotes or as a key
            if not inner_tool and inner_args:
                # Handle case where first arg is empty but more follow
                inner_tool = inner_args[0]
                inner_args = inner_args[1:]

            if inner_tool in self.tool_router.tools:
                return self.tool_router.tools[inner_tool](inner_args, ctx)
                
            return ToolResult(False, f"Inner tool '{inner_tool}' not found or invalid.", "⚠️")
            
        self.tool_router.register_tool("assistant", tool_assistant)
        
        # Vision UI tools (OCR-based intelligent interaction)
        self.tool_router.register_tool("scan_ui", tool_scan_ui)
        self.tool_router.register_tool("click_text", tool_click_text)
        self.tool_router.register_tool("peek", tool_peek_desktop)
        self.tool_router.register_tool("peek_desktop", tool_peek_desktop)
        
        # Scroll tool
        def tool_scroll(args, ctx):
            if not self.hands or not args:
                return ToolResult(False, "Falta argumento para scroll(clicks).", "🖐️ MANOS")
            try:
                clicks = int(args[0])
                return ToolResult(True, self.hands.scroll(clicks), "🖐️ MANOS")
            except:
                return ToolResult(False, "Argumento de scroll debe ser un número.", "🖐️ MANOS")
        
        self.tool_router.register_tool("scroll", tool_scroll)

    def _execute_tools(self, text: str, *, session_user: str | None = None, context: dict | None = None) -> str:
        """Execute tools found in text and return text with results appended."""
        import re
        # Updated pattern to support dotted names like browser.open_url
        tool_pattern = re.compile(r'\[\[\s*([\w.]+)\s*\((.*?)\)\s*\]\]')
        matches = tool_pattern.findall(text)
        
        if matches:
            self.log.info("TOOLS DETECTED in response: %s", matches)
        
        if matches and self.status_callback:
            # Map tools to user-friendly messages with better specificity
            messages = {
                "screenshot": "Mirando pantalla",
                "click": "Haciendo clic",
                "type": "Escribiendo",
                "hotkey": "Usando atajo de teclado",
                "move": "Moviendo el mouse",
                "read_file": "Leyendo archivo",
                "write_file": "Escribiendo archivo",
                "remember": "Guardando en memoria",
                "forget": "Olvidando",
                "memorize_file": "Guardando en memoria",
                "recall": "Buscando en memoria",
                "search_web": "Buscando en internet",
                "web_search": "Buscando en internet",
                "read_url": "Leyendo página web",
                "os_run": "Abriendo aplicación",
                "browser.run": "Abriendo navegador",
                "window_manager": "Gestionando ventanas",
                "windows": "Gestionando ventanas",
            }
            # Pick first tool's message as general status
            first_tool = matches[0][0]
            msg = messages.get(first_tool, "Ejecutando herramientas")
            self.status_callback(msg, "warning")

        # Prepare context
        exec_context = context.copy() if context else {}
        if session_user:
            exec_context["session_user"] = session_user

        try:
            return self.tool_router.parse_and_execute(text, exec_context)
        except Exception as e:
            self.log.error("Tool execution failed: %s", e, exc_info=True)
            return text + f"\n\n[⚠️ ERROR CORE]: Error al ejecutar herramientas: {e}"

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
        
        # Release 1.1 Policy: ENFORCE LOCAL-ONLY
        # If persisted choice is 'clawdbot' or missing, we fallback to 'ollama'
        # to prevent cloud leaks/Anthropic fallbacks.
        if persisted_provider and persisted_provider != "ollama":
            self.log.warning("Ignoring persisted cloud provider '%s' for %s. Enforcing local-only policy.", 
                            persisted_provider, session_user)
            persisted_provider = "ollama"
            persisted_model = self.cfg.ollama.model

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
        
        # Phase 5: Facts Enrichment & Dynamic Context
        import datetime
        now = datetime.datetime.now()
        dynamic_context = f"\n\n[SISTEMA - {now.strftime('%d/%m/%Y %H:%M:%S')}]\n"
        dynamic_context += f"- Hora actual: {now.strftime('%H:%M')}\n"
        dynamic_context += f"- SO: {platform.system()} {platform.release()}\n"
        
        system_content = DEFAULT_SYSTEM_PROMPT + dynamic_context
        
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
                
                if assistant_content:
                    history_messages.insert(0, {"role": "assistant", "content": assistant_content})
                if user_content:
                    history_messages.insert(0, {"role": "user", "content": user_content})
                
                total_chars += pair_size
            
            messages.extend(history_messages)
            self.log.info("Loaded %d history messages (%d chars)", 
                         len(history_messages), total_chars)
        
        messages.append(current_msg)
        
        # --- FIX: INYECCIÓN DE VOLUNTAD (Anti-Alucinación) ---
        # Fuerza al LLM a usar las herramientas en lugar de solo conversar.
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
        # -----------------------------------------------------
        
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
        if LOCAL_ONLY and provider not in ["ollama", "clawdbot"]:
            provider = "ollama"
            
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
                    hint = "FALLO DEL SISTEMA: El usuario pidió una acción pero no usaste ninguna herramienta. DEBES responder usando EXACTAMENTE el formato [[herramienta(argumentos)]]. No des explicaciones, solo emite el comando."
                    current_messages = messages + [{"role": "user", "content": hint}]

                if provider == "clawdbot" and self.clawdbot:
                    result = self.clawdbot.chat(current_messages, model=model, user=session_user).text
                else:
                    # Fallback to ollama if provider is unknown or clawdbot disabled
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
                    
                    if provider == "clawdbot" and self.clawdbot:
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
                # Capture specific Ollama errors if available
                from lucy_c.ollama_llm import OllamaChatError
                is_ollama_error = isinstance(e, OllamaChatError)

                self.log.warning("Moltbot brain attempt %d/%d failed: %s", 
                               attempt + 1, max_retries + 1, e)
                
                if attempt < max_retries:
                    import time as time_module
                    wait_time = (2 ** attempt) * 0.5  # Exponential backoff
                    time_module.sleep(wait_time)
                    continue
                
                # Final attempt failed
                error_id = str(uuid.uuid4())[:8]
                self.log.exception("All Moltbot retries exhausted [ErrorID: %s]", error_id)
                
                # Semantic fallbacks
                err_str = str(e).lower()
                
                if is_ollama_error:
                    # Provide clearer feedback for Ollama specific issues
                    if "connect" in err_str or "refused" in err_str:
                         return f"No pude conectar con Ollama. ¿Podrías fijarte si el servidor está corriendo en 127.0.0.1:11434? (ID: {error_id})"
                    if "not found" in err_str or "model" in err_str:
                         return f"Parece que el modelo '{model}' no está instalado o no se encuentra. ¿Probamos con otro? (ID: {error_id})"
                    return f"Tuve un problema técnico con mi cerebro local: {e} (ID: {error_id})"

                if "connection" in err_str or "timeout" in err_str or "unreachable" in err_str:
                    return f"Perdón, che, parece que tengo un problema de conexión con mi cerebro local. ¿Te fijás si Ollama está corriendo? Intentá de nuevo en un ratito. (ID: {error_id})"
                elif "venerable" in err_str or "empty" in err_str or "invalida" in err_str or "inválida" in err_str:
                    return f"Che, mi cerebro se quedó en blanco. ¿Podrías preguntarme de otra forma o repetirme lo último? (ID: {error_id})"
                else:
                    return f"Ups, algo no salió bien procesando eso. ¿Probamos de nuevo con otra frase? (ID: {error_id})"

    def _validate_model_fallback(self):
        """If configured model missing, fallback to first available."""
        try:
            models = self.ollama.list_models()
            if not models:
                self.log.error("No local models found in Ollama!")
                return

            current_model = self.cfg.ollama.model
            if current_model not in models:
                fallback = models[0]
                self.log.warning("Configured model '%s' not found. Falling back to '%s'.", 
                               current_model, fallback)
                self.cfg.ollama.model = fallback
        except Exception as e:
            self.log.error("Failed to validate model fallback: %s", e)

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
