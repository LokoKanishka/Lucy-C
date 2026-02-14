from __future__ import annotations
import logging
import re
from dataclasses import dataclass
from typing import Callable, Any, Dict, List, Optional

@dataclass
class ToolResult:
    success: bool
    output: str
    tag: str = "⚙️ TOOLS"

class ToolRouter:
    def __init__(self):
        self.log = logging.getLogger("LucyC.ToolRouter")
        self.tools: Dict[str, Callable] = {}
        # tool_name -> list of forbidden strings in args (basic security)
        self.security_rules: Dict[str, List[str]] = {
            "all": [";", "&&", "||", ">", "<", "$(", "system("]
        }

    def register_tool(self, name: str, func: Callable):
        self.tools[name] = func
        self.log.info("Tool registered: %s", name)

    def _validate_security(self, name: str, args_str: str) -> Optional[str]:
        """Check for forbidden patterns in arguments."""
        # Generic rules
        for rule in self.security_rules.get("all", []):
            if rule in args_str:
                return f"Seguridad: Argumento prohibido '{rule}' detectado."
        
        # Specific rules
        for rule in self.security_rules.get(name, []):
            if rule in args_str:
                return f"Seguridad: Argumento prohibido para {name}: '{rule}'."
        
        return None

    def parse_and_execute(self, text: str, context: Dict[str, Any]) -> str:
        """
        Parses [[tool_name(args)]] from text and executes them.
        Returns the original text with tool results appended.
        """
        import ast
        # Matches [[ name ( args ) ]] - allowing dots in names just in case
        tool_pattern = re.compile(r'\[\[\s*([\w\.]+)\s*\((.*?)\)\s*\]\]')
        matches = tool_pattern.findall(text)
        
        if not matches:
            self.log.debug("No tool matches found in text.")
            return text
            
        self.log.info("Parsed %d tool calls: %s", len(matches), matches)
        final_response = text
        for tool_name, args_str in matches:
            self.log.info("Activating tool: %s(%s)", tool_name, args_str)
            
            # 1. Security Check
            sec_error = self._validate_security(tool_name, args_str)
            if sec_error:
                self.log.warning("Security trigger: %s", sec_error)
                final_response += f"\n\n[⚠️ SEGURIDAD]: {sec_error}"
                continue

            # 2. Find Tool
            if tool_name not in self.tools:
                self.log.warning("Tool not found: %s", tool_name)
                final_response += f"\n\n[⚠️ BASE CORE]: Herramienta '{tool_name}' no disponible."
                continue

            # 3. Parse Args (Secure AST parsing)
            try:
                # Wrap args in tuple to make it a valid python literal expression
                # e.g. "arg1, arg2" -> "('arg1', 'arg2')"
                # If args_str is empty, ast.literal_eval("()") returns ()
                literal_expr = f"({args_str})" if args_str.strip() else "()"
                
                parsed_args = ast.literal_eval(literal_expr)
                
                # Ensure it's a tuple or list, converting to list for tool call
                if not isinstance(parsed_args, (list, tuple)):
                    parsed_args = [parsed_args]
                
                args = list(parsed_args)
                
                # 4. Execute
                result: ToolResult = self.tools[tool_name](args, context)
                
                self.log.info("%s result: %s", result.tag, result.output)
                final_response += f"\n\n[{result.tag}]: {result.output}"
                
            except (ValueError, SyntaxError) as e:
                self.log.error("Tool argument parsing failed for '%s': %s", args_str, e)
                final_response += f"\n\n[⚠️ ERROR SINTAXIS]: No pude entender los argumentos de {tool_name}: {e}"
            except Exception as e:
                self.log.error("Tool execution failed: %s", e)
                final_response += f"\n\n[Moltbot Error]: Hubo un fallo inesperadamente ejecutando {tool_name}."
                
        return final_response
