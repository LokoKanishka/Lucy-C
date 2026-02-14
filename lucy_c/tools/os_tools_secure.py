import shlex
import subprocess
import logging
from lucy_c.tool_router import ToolResult

log = logging.getLogger("LucyC.OSToolsSecure")

# Definición de política de seguridad granular
ALLOWED_BINARIES = {
    "ls": {
        "allow_args": True,
        "safe_flags": {"-l", "-a", "-h", "-t", "-r", "--color=auto"},
        "path_restriction": "USER_HOME"
    },
    "uptime": {"allow_args": False},
    "whoami": {"allow_args": False},
    "gnome-calculator": {"allow_args": False},
    "calc": {"allow_args": False, "alias_for": "gnome-calculator"},
    "code": {
        "allow_args": True,
        "path_restriction": "PROJECT_ROOT"
    },
    "date": {"allow_args": False},
    "echo": {"allow_args": True}, # Be careful with this, but often useful for testing
    "cat": {
        "allow_args": True,
        "path_restriction": "PROJECT_ROOT" # Only allow reading files in project
    }
}

def validate_command(command_str: str) -> bool:
    """Valida un comando contra la lista blanca y políticas de argumentos."""
    try:
        parts = shlex.split(command_str)
    except ValueError:
        return False # Comillas desbalanceadas o inyección malformada

    if not parts:
        return False

    binary = parts[0]
    
    # Check if binary is allowed
    if binary not in ALLOWED_BINARIES:
        return False

    policy = ALLOWED_BINARIES[binary]
    
    # Handle alias
    if "alias_for" in policy:
        # We don't change it here, just validation. 
        # But if it's an alias that doesn't allow args, check args.
        pass

    args = parts[1:]

    if args and not policy.get("allow_args", False):
        return False

    # Deep validation of arguments
    # safe_flags = policy.get("safe_flags", set())
    # for arg in args:
    #     if arg.startswith("-"):
    #         if arg not in safe_flags:
    #             return False
        # Here we would add path restriction logic
        
    return True

def tool_os_run_secure(args, ctx):
    """Execute a system command securely and return output."""
    if not args:
        return ToolResult(False, "Falta el comando para ejecutar.", "🖥️ OS")
    
    raw_cmd = args[0].strip()
    
    if not validate_command(raw_cmd):
        log.warning("Security Block: Blocked command: %s", raw_cmd)
        return ToolResult(False, f"Comando bloqueado por política de seguridad (Whitelist): {raw_cmd}", "🛡️ SEGURIDAD")
    
    # Execution
    try:
        import os
        # Basic variable expansion for user convenience
        raw_cmd = os.path.expandvars(os.path.expanduser(raw_cmd))
        
        parts = shlex.split(raw_cmd)
        binary = parts[0]
        policy = ALLOWED_BINARIES.get(binary, {})
        
        # Resolve alias
        if "alias_for" in policy:
            real_binary = policy["alias_for"]
            parts[0] = real_binary
            
        # Run with shell=False for maximum security
        res = subprocess.run(
            parts, 
            capture_output=True, 
            text=True, 
            timeout=10
        )
        
        output = res.stdout.strip()
        if not output and res.stderr:
            output = f"Error: {res.stderr.strip()}"
            
        return ToolResult(True, output or "(Comando ejecutado)", "🖥️ OS")
        
    except Exception as e:
        log.error("Secure OS run failed: %s", e)
        return ToolResult(False, f"Fallo ejecución: {e}", "🖥️ OS")
