from __future__ import annotations
import os
from pathlib import Path
from lucy_c.tool_router import ToolResult

# Restrict operations to the project root
BASE_DIR = Path(__file__).resolve().parents[2]

def safe_path(relative_path: str) -> Path | None:
    """Ensures the path is within the allowed project root."""
    try:
        # Resolve to absolute path, handling potential trickery like ../../
        target = (BASE_DIR / relative_path).resolve()
        if os.path.commonpath([BASE_DIR, target]) == str(BASE_DIR):
            return target
    except Exception:
        pass
    return None

def tool_read_file(args: list[str], ctx: dict) -> ToolResult:
    """Reads a file from the project directory."""
    if not args:
        return ToolResult(False, "Falta el nombre del archivo para leer.", "📁 ARCHIVOS")
    
    path = safe_path(args[0])
    if not path:
        return ToolResult(False, f"Acceso denegado o ruta inválida: {args[0]}", "📁 ARCHIVOS")
    
    if not path.is_file():
        return ToolResult(False, f"El archivo no existe: {args[0]}", "📁 ARCHIVOS")
    
    try:
        content = path.read_text(encoding="utf-8")
        # Truncate if too large for LLM context, but for now just read
        if len(content) > 2000:
            content = content[:2000] + "\n... (contenido truncado por longitud)"
        return ToolResult(True, content, "📁 ARCHIVOS")
    except Exception as e:
        return ToolResult(False, f"Error leyendo archivo: {e}", "📁 ARCHIVOS")

def tool_write_file(args: list[str], ctx: dict) -> ToolResult:
    """Writes content to a file in the project directory."""
    if ctx.get("safe_mode"):
        return ToolResult(False, "Escritura de archivos bloqueada en Modo Seguro por precaución.", "🛡️ SEGURIDAD")
    
    if len(args) < 2:
        return ToolResult(False, "Faltan argumentos: write_file(ruta, contenido).", "📁 ARCHIVOS")
    
    path = safe_path(args[0])
    if not path:
        return ToolResult(False, f"Acceso denegado o ruta inválida: {args[0]}", "📁 ARCHIVOS")
    
    content = args[1]
    try:
        # Ensure parent directories exist
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return ToolResult(True, f"Archivo escrito exitosamente: {args[0]}", "📁 ARCHIVOS")
    except Exception as e:
        return ToolResult(False, f"Error escribiendo archivo: {e}", "📁 ARCHIVOS")
