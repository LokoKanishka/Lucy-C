import subprocess
import logging
import shlex
from lucy_c.tool_router import ToolResult

log = logging.getLogger("LucyC.OSTools")

# Command Blacklist
BLACKLIST = [
    "rm ", "sudo ", "mkfs", "dd ", "> /dev/", 
    "mv /*", "chmod -R", "chown -R", ":(){:|:&};:", 
    "mkfifo", "wget ", "curl ", "ssh ", "sftp"
]

# Common App Aliases
APP_MAP = {
    "calculadora": "gnome-calculator",
    "calc": "gnome-calculator",
    "editor": "code",
    "terminal": "gnome-terminal",
    "monitor": "gnome-system-monitor",
    "archivos": "nautilus"
}

def is_safe_command(cmd: str) -> bool:
    """Basic security filter for OS commands."""
    cmd_lower = cmd.lower()
    for bad in BLACKLIST:
        if bad in cmd_lower:
            return False
    return True

def tool_os_run(args, ctx):
    """Execute a system command securely and return output."""
    if not args:
        return ToolResult(False, "Falta el comando para ejecutar.", "🖥️ OS")
    
    raw_cmd = args[0].strip()
    
    # Check for alias
    cmd_parts = shlex.split(raw_cmd)
    executable = cmd_parts[0] if cmd_parts else ""
    if executable.lower() in APP_MAP:
        raw_cmd = raw_cmd.lower().replace(executable.lower(), APP_MAP[executable.lower()], 1)

    if not is_safe_command(raw_cmd):
        log.warning("Security Block: Blocked dangerous command: %s", raw_cmd)
        return ToolResult(False, f"Comando bloqueado por seguridad: {raw_cmd}", "🛡️ SEGURIDAD")

    log.info("Executing OS command: %s", raw_cmd)
    try:
        # For GUI apps or background tasks, using Popen might be better if no output expected immediately
        # But for 'ls' etc, we want results.
        # Check if it looks like a GUI app launch
        is_gui = any(app in raw_cmd for app in APP_MAP.values()) or "firefox" in raw_cmd
        
        if is_gui:
            subprocess.Popen(shlex.split(raw_cmd), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return ToolResult(True, f"Ejecutando '{raw_cmd}' en segundo plano.", "🖥️ OS")
        else:
            res = subprocess.run(
                shlex.split(raw_cmd), 
                capture_output=True, 
                text=True, 
                timeout=15
            )
            output = res.stdout.strip()
            if not output and res.stderr:
                output = f"Error: {res.stderr.strip()}"
            
            return ToolResult(True, output or "(Comando ejecutado sin salida)", "🖥️ OS")
            
    except subprocess.TimeoutExpired:
        return ToolResult(False, "El comando excedió el tiempo límite (15s).", "🖥️ OS")
    except Exception as e:
        log.error("OS command execution failed: %s", e)
        return ToolResult(False, f"Fallo al ejecutar el comando: {e}", "🖥️ OS")

def tool_window_manager(args, ctx):
    """Manage desktop windows using wmctrl (X11 only)."""
    if not args:
        return ToolResult(False, "Falta la acción. Acciones disponibles: list, focus, minimize, close", "🪟 VENTANAS")
    
    action = args[0].strip().lower()
    target = args[1].strip() if len(args) > 1 else None
    
    log.info("Window manager action: %s (target: %s)", action, target)
    
    # Check if wmctrl is available
    try:
        subprocess.run(["wmctrl", "-h"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ToolResult(False, "wmctrl no está instalado. Instalá con: sudo apt install wmctrl", "🪟 VENTANAS")
    
    try:
        if action == "list":
            # List all windows
            result = subprocess.run(
                ["wmctrl", "-l"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                return ToolResult(False, f"Error listando ventanas: {result.stderr}", "🪟 VENTANAS")
            
            windows = result.stdout.strip()
            if not windows:
                return ToolResult(True, "No hay ventanas abiertas.", "🪟 VENTANAS")
            
            # Parse and format
            lines = []
            for line in windows.split("\n"):
                parts = line.split(None, 3)
                if len(parts) >= 4:
                    lines.append(f" - {parts[3]}")
            
            return ToolResult(True, f"Ventanas abiertas:\n" + "\n".join(lines), "🪟 VENTANAS")
        
        elif action == "focus":
            if not target:
                return ToolResult(False, "Falta el nombre de la ventana para enfocar.", "🪟 VENTANAS")
            
            # Focus window by title (partial match)
            result = subprocess.run(
                ["wmctrl", "-a", target],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                return ToolResult(False, f"No encontré una ventana con '{target}'. Usá 'list' para ver las ventanas disponibles.", "🪟 VENTANAS")
            
            return ToolResult(True, f"Ventana '{target}' traída al frente.", "🪟 VENTANAS")
        
        elif action == "minimize":
            if not target:
                return ToolResult(False, "Falta el nombre de la ventana para minimizar.", "🪟 VENTANAS")
            
            # Find window ID first
            list_result = subprocess.run(
                ["wmctrl", "-l"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            window_id = None
            for line in list_result.stdout.split("\n"):
                if target.lower() in line.lower():
                    window_id = line.split()[0]
                    break
            
            if not window_id:
                return ToolResult(False, f"No encontré ventana '{target}'", "🪟 VENTANAS")
            
            # Minimize using wmctrl
            result = subprocess.run(
                ["wmctrl", "-i", "-r", window_id, "-b", "add,hidden"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            return ToolResult(True, f"Ventana '{target}' minimizada.", "🪟 VENTANAS")
        
        elif action == "close":
            if not target:
                return ToolResult(False, "Falta el nombre de la ventana para cerrar.", "🪟 VENTANAS")
            
            # Close window by title
            result = subprocess.run(
                ["wmctrl", "-c", target],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                return ToolResult(False, f"No encontré ventana '{target}' para cerrar.", "🪟 VENTANAS")
            
            return ToolResult(True, f"Ventana '{target}' cerrada.", "🪟 VENTANAS")
        
        else:
            return ToolResult(False, f"Acción desconocida: {action}. Usa: list, focus, minimize, close", "🪟 VENTANAS")
    
    except subprocess.TimeoutExpired:
        return ToolResult(False, "Timeout gestionando ventanas.", "🪟 VENTANAS")
    except Exception as e:
        log.error("Window manager error: %s", e)
        return ToolResult(False, f"Error en window manager: {e}", "🪟 VENTANAS")
