from __future__ import annotations
import typing
from typing import List, Dict, Any, Callable
from lucy_c.tool_router import ToolResult

if typing.TYPE_CHECKING:
    from lucy_c.pipeline import Moltbot

def create_core_tools(bot: 'Moltbot') -> Dict[str, Callable]:
    """
    Creates and returns a dictionary of core tools, bound to the provided Moltbot instance.
    """
    
    def tool_remember(args: List[str], ctx: Dict[str, Any]) -> ToolResult:
        session_user = ctx.get("session_user")
        if not bot.facts or not session_user:
            return ToolResult(False, "Almacén de hechos no disponible.", "⚠️ ERROR CORE")
        if len(args) < 2:
            return ToolResult(False, "Faltan argumentos para remember(clave, valor).", "⚠️ ERROR CORE")
        
        # Sensitivity check (example key)
        if bot.cfg.safe_mode and args[0] in ["password", "token", "secreto"]:
            return ToolResult(False, f"Seguridad: No puedo guardar '{args[0]}' en Modo Seguro.", "🛡️ SEGURIDAD")

        bot.facts.set_fact(session_user, args[0], args[1])
        return ToolResult(True, f"Recordado: {args[0]} = {args[1]}", "🧠 MEMORIA")

    def tool_forget(args: List[str], ctx: Dict[str, Any]) -> ToolResult:
        if bot.cfg.safe_mode:
            return ToolResult(False, "Olvidar está bloqueado en Modo Seguro por precaución.", "🛡️ SEGURIDAD")
        
        session_user = ctx.get("session_user")
        if not bot.facts or not session_user:
            return ToolResult(False, "Almacén de hechos no disponible.", "⚠️ ERROR CORE")
        if not args:
            return ToolResult(False, "Falta argumento para forget(clave).", "⚠️ ERROR CORE")
        bot.facts.remove_fact(session_user, args[0])
        return ToolResult(True, f"Olvidado: {args[0]}", "🧠 MEMORIA")

    def tool_screenshot(args: List[str], ctx: Dict[str, Any]) -> ToolResult:
        if not bot.eyes:
            return ToolResult(False, "Sensores de visión no disponibles.", "⚠️ ERROR CORE")
        return ToolResult(True, bot.eyes.describe_screen(), "👁️ OJOS")

    def tool_type(args: List[str], ctx: Dict[str, Any]) -> ToolResult:
        if not bot.hands or not args:
            return ToolResult(False, "Actuadores no disponibles o faltan argumentos.", "🖐️ MANOS")
        return ToolResult(True, bot.hands.type_text(args[0]), "🖐️ MANOS")

    def tool_press(args: List[str], ctx: Dict[str, Any]) -> ToolResult:
        if not bot.hands or not args:
            return ToolResult(False, "Actuadores no disponibles o faltan argumentos.", "🖐️ MANOS")
        return ToolResult(True, bot.hands.press_key(args[0]), "🖐️ MANOS")

    def tool_click(args: List[str], ctx: Dict[str, Any]) -> ToolResult:
        if not bot.hands:
            return ToolResult(False, "Actuadores no disponibles.", "🖐️ MANOS")
        
        # click(x, y, button, clicks)
        x = int(args[0]) if len(args) > 0 and args[0].isdigit() else None
        y = int(args[1]) if len(args) > 1 and args[1].isdigit() else None
        button = args[2] if len(args) > 2 else 'left'
        clicks = int(args[3]) if len(args) > 3 and args[3].isdigit() else 1
        
        return ToolResult(True, bot.hands.click(x, y, button, clicks), "🖐️ MANOS")

    def tool_hotkey(args: List[str], ctx: Dict[str, Any]) -> ToolResult:
        if not bot.hands or not args:
            return ToolResult(False, "Actuadores no disponibles o faltan argumentos.", "🖐️ MANOS")
        return ToolResult(True, bot.hands.hotkey(*args), "🖐️ MANOS")

    def tool_wait(args: List[str], ctx: Dict[str, Any]) -> ToolResult:
        if not args or not bot.hands:
            return ToolResult(False, "Falta argumento para wait(segundos).", "🖐️ MANOS")
        try:
            seconds = float(args[0])
            return ToolResult(True, bot.hands.wait(seconds), "🖐️ MANOS")
        except:
            return ToolResult(False, "Argumento de wait debe ser un número.", "🖐️ MANOS")

    def tool_move(args: List[str], ctx: Dict[str, Any]) -> ToolResult:
        if len(args) < 2 or not bot.hands:
            return ToolResult(False, "Faltan coordenadas para move(x, y).", "🖐️ MANOS")
        try:
            x, y = int(args[0]), int(args[1])
            return ToolResult(True, bot.hands.move_to(x, y), "🖐️ MANOS")
        except Exception as e:
            return ToolResult(False, f"Error en move: {e}", "🖐️ MANOS")
            
    def tool_scroll(args: List[str], ctx: Dict[str, Any]) -> ToolResult:
        if not bot.hands or not args:
            return ToolResult(False, "Falta argumento para scroll(clicks).", "🖐️ MANOS")
        try:
            clicks = int(args[0])
            return ToolResult(True, bot.hands.scroll(clicks), "🖐️ MANOS")
        except:
            return ToolResult(False, "Argumento de scroll debe ser un número.", "🖐️ MANOS")

    def tool_get_info(args: List[str], ctx: Dict[str, Any]) -> ToolResult:
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

    def tool_assistant(args: List[str], ctx: Dict[str, Any]) -> ToolResult:
        if not args: return ToolResult(False, "No args for assistant wrapper", "⚠️")
        
        inner_tool = args[0]
        inner_args = args[1:]
        
        # Robustness: sometimes models put the tool name in quotes or as a key
        if not inner_tool and inner_args:
            # Handle case where first arg is empty but more follow
            inner_tool = inner_args[0]
            inner_args = inner_args[1:]

        if inner_tool in bot.tool_router.tools:
            return bot.tool_router.tools[inner_tool](inner_args, ctx)
            
        return ToolResult(False, f"Inner tool '{inner_tool}' not found or invalid.", "⚠️")

    return {
        "remember": tool_remember,
        "forget": tool_forget,
        "screenshot": tool_screenshot,
        "type": tool_type,
        "press": tool_press,
        "click": tool_click,
        "hotkey": tool_hotkey,
        "wait": tool_wait,
        "move": tool_move,
        "scroll": tool_scroll,
        "get_info": tool_get_info,
        "assistant": tool_assistant
    }
