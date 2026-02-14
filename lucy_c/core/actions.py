from __future__ import annotations
import logging
import os
from typing import Any, Dict, List, Optional

from lucy_c.tool_router import ToolRouter, ToolResult
from lucy_c.interfaces.llm import LLMProvider
from lucy_c.config import LucyConfig

class ActionController:
    """
    Manages the execution of tools and actions (The 'Body' acting on the world).
    Owns the Hands (Automation), Eyes (Vision), and the ToolRouter.
    """
    def __init__(self, cfg: LucyConfig, tool_router: ToolRouter, llm_provider: LLMProvider):
        self.cfg = cfg
        self.tool_router = tool_router
        self.llm_provider = llm_provider
        self.log = logging.getLogger("LucyC.Actions")
        
        self._check_safe_mode()
        
        # Body Parts (Lazy loaded)
        self._eyes = None
        self._hands = None
        
        # Register core tools immediately
        self.register_default_tools()

    def _check_safe_mode(self):
        if self.cfg.safe_mode:
            self.log.info("ActionController initialized in SAFE MODE.")

    @property
    def eyes(self):
        if self._eyes is None:
            try:
                from lucy_c.tools.vision_tool import SystemEyes
                # SystemEyes expects an LLM provider.
                self._eyes = SystemEyes(self.llm_provider)
            except Exception as e:
                self.log.warning("Lucy Body: Eyes (Vision) not available: %s", e)
        return self._eyes

    @property
    def hands(self):
        if self._hands is None:
            try:
                from lucy_c.tools.automation_tool import SystemHands
                self._hands = SystemHands()
            except Exception as e:
                self.log.warning("Lucy Body: Hands (Automation) not available: %s", e)
        return self._hands

    def execute(self, text_with_tools: str, context: Dict[str, Any] | None = None) -> str:
        """
        Parses and executes tools found in the text.
        Returns the original text with tool results appended.
        """
        import re
        tool_pattern = re.compile(r'\[\[\s*([\w.]+)\s*\((.*?)\)\s*\]\]')
        matches = tool_pattern.findall(text_with_tools)
        
        if matches:
            self.log.info("ActionController detected tools: %s", matches)
        else:
            return text_with_tools

        try:
            result_text = self.tool_router.parse_and_execute(text_with_tools, context or {})
            return result_text
        except Exception as e:
            self.log.error("Action execution failed: %s", e, exc_info=True)
            return text_with_tools + f"\n\n[⚠️ ERROR MOTOR]: Fallo al ejecutar acción: {e}"

    def register_default_tools(self):
        """Register all available tools with the router."""
        from lucy_c.tools.file_tools import tool_read_file, tool_write_file
        from lucy_c.tools.business_tools import tool_check_shipping, tool_process_payment, tool_generate_budget_pdf
        from lucy_c.tools.web_tools import tool_web_search, tool_open_url, tool_read_url
        from lucy_c.tools.os_tools_secure import tool_os_run_secure
        from lucy_c.tools.os_tools import tool_window_manager 
        from lucy_c.tools.vision_ui_tools import tool_scan_ui, tool_click_text, tool_peek_desktop
        from lucy_c.tools.n8n_tools import create_n8n_tools
        from lucy_c.tools.cognitive_tools import create_cognitive_tools
        
        # --- Internal Helper Tools using Body ---
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
            x = int(args[0]) if len(args) > 0 and str(args[0]).isdigit() else None
            y = int(args[1]) if len(args) > 1 and str(args[1]).isdigit() else None
            button = args[2] if len(args) > 2 else 'left'
            clicks = int(args[3]) if len(args) > 3 and str(args[3]).isdigit() else 1
            return ToolResult(True, self.hands.click(x, y, button, clicks), "🖐️ MANOS")

        def tool_scroll(args, ctx):
            if not self.hands or not args:
                return ToolResult(False, "Falta argumento para scroll.", "🖐️ MANOS")
            try:
                clicks = int(args[0])
                return ToolResult(True, self.hands.scroll(clicks), "🖐️ MANOS")
            except:
                return ToolResult(False, "Argumento invalido.", "🖐️ MANOS")

        def tool_hotkey(args, ctx):
            if not self.hands or not args:
                return ToolResult(False, "Actuadores no disponibles", "🖐️ MANOS")
            return ToolResult(True, self.hands.hotkey(*args), "🖐️ MANOS")
            
        def tool_wait(args, ctx):
            if not args or not self.hands:
                return ToolResult(False, "Falta argumento.", "🖐️ MANOS")
            try:
                seconds = float(args[0])
                return ToolResult(True, self.hands.wait(seconds), "🖐️ MANOS")
            except:
                return ToolResult(False, "Invalido.", "🖐️ MANOS")
                
        def tool_move(args, ctx):
             if len(args) < 2 or not self.hands:
                 return ToolResult(False, "Faltan coordenadas.", "🖐️ MANOS")
             try:
                 x, y = int(args[0]), int(args[1])
                 return ToolResult(True, self.hands.move_to(x, y), "🖐️ MANOS")
             except Exception as e:
                 return ToolResult(False, f"Error move: {e}", "🖐️ MANOS")

        def tool_remember(args, ctx):
            facts = ctx.get("facts_store")
            session_user = ctx.get("session_user")
            if not facts or not session_user:
                return ToolResult(False, "Memoria no disponible en contexto.", "⚠️")
            
            if len(args) < 2:
                return ToolResult(False, "Faltan args: remember(key, value)", "⚠️")
            
            facts.set_fact(session_user, args[0], args[1])
            return ToolResult(True, f"Recordado: {args[0]}", "🧠")

        def tool_forget(args, ctx):
            facts = ctx.get("facts_store")
            session_user = ctx.get("session_user")
            if not facts or not session_user: return ToolResult(False, "Error memoria", "⚠️")
            if not args: return ToolResult(False, "Falta arg", "⚠️")
            facts.remove_fact(session_user, args[0])
            return ToolResult(True, f"Olvidado: {args[0]}", "🧠")
            
        def tool_get_info(args, ctx):
            import datetime
            import platform
            tipo = args[0].lower() if args else "time"
            if tipo == "time":
                now = datetime.datetime.now().strftime("%H:%M:%S")
                return ToolResult(True, f"Hora: {now}", "⚙️")
            elif tipo == "date":
                today = datetime.datetime.now().strftime("%d/%m/%Y")
                return ToolResult(True, f"Fecha: {today}", "⚙️")
            elif tipo == "os":
                return ToolResult(True, f"Sistema: {platform.system()} {platform.release()}", "⚙️")
            return ToolResult(False, "Tipo desconocido", "⚠️")

        # Registering
        tr = self.tool_router
        tr.register_tool("screenshot", tool_screenshot)
        tr.register_tool("click", tool_click)
        tr.register_tool("type", tool_type)
        tr.register_tool("press", tool_press)
        tr.register_tool("hotkey", tool_hotkey)
        tr.register_tool("wait", tool_wait)
        tr.register_tool("move", tool_move)
        tr.register_tool("scroll", tool_scroll)
        
        tr.register_tool("remember", tool_remember)
        tr.register_tool("forget", tool_forget)
        tr.register_tool("get_info", tool_get_info)
        
        tr.register_tool("read_file", tool_read_file)
        tr.register_tool("write_file", tool_write_file)
        
        tr.register_tool("check_shipping", tool_check_shipping)
        tr.register_tool("process_payment", tool_process_payment)
        tr.register_tool("generate_budget_pdf", tool_generate_budget_pdf)
        
        tr.register_tool("search_web", tool_web_search)
        tr.register_tool("web_search", tool_web_search)
        tr.register_tool("google_search", tool_web_search) # Alias
        tr.register_tool("open_url", tool_open_url)
        tr.register_tool("read_url", tool_read_url)
        
        # SECURE OS RUN
        tr.register_tool("os_run", tool_os_run_secure)
        tr.register_tool("browser.run", tool_os_run_secure)
        
        tr.register_tool("window_manager", tool_window_manager)
        tr.register_tool("windows", tool_window_manager)
        
        tr.register_tool("scan_ui", tool_scan_ui)
        tr.register_tool("click_text", tool_click_text)
        tr.register_tool("peek", tool_peek_desktop)
        tr.register_tool("peek_desktop", tool_peek_desktop)
        
        if self.cfg.n8n and self.cfg.n8n.base_url:
             n8n_tools = create_n8n_tools(self.cfg.n8n)
             tr.register_tool("trigger_workflow", n8n_tools["trigger_workflow"])
             
             cog_tools = create_cognitive_tools(n8n_tools)
             tr.register_tool("ask_sota", cog_tools["ask_sota"])
