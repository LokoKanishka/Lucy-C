import logging
import json
from lucy_c.tool_router import ToolResult

log = logging.getLogger("LucyC.N8nTools")

def create_n8n_tools(n8n_config):
    """Factory function to create n8n tools with config injected."""
    
    def tool_trigger_workflow(args, ctx):
        """Trigger an n8n workflow via webhook.
        
        Args:
            args[0]: workflow_id (str) - The workflow identifier/slug
            args[1]: payload (str) - JSON string of data to send
        """
        if len(args) < 1:
            return ToolResult(False, "Falta el ID del workflow.", "🔗 N8N")
        
        workflow_id = args[0]
        payload = {}
        
        # Parse payload if provided
        if len(args) > 1:
            try:
                payload = json.loads(args[1]) if isinstance(args[1], str) else args[1]
            except json.JSONDecodeError as e:
                return ToolResult(False, f"Payload JSON inválido: {e}", "🔗 N8N")
        
        # Construct webhook URL
        url = f"{n8n_config.base_url.rstrip('/')}/webhook/{n8n_config.webhook_prefix}{workflow_id}"
        log.info("Triggering n8n workflow: %s", url)
        
        try:
            import httpx
            with httpx.Client(timeout=n8n_config.timeout) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
                
                # Try to parse JSON response
                try:
                    result = response.json()
                    result_str = json.dumps(result, ensure_ascii=False, indent=2)
                    return ToolResult(True, f"Workflow '{workflow_id}' ejecutado. Respuesta:\n{result_str}", "🔗 N8N")
                except json.JSONDecodeError:
                    # Plain text response
                    return ToolResult(True, f"Workflow '{workflow_id}' ejecutado. Respuesta: {response.text}", "🔗 N8N")
                    
        except httpx.TimeoutException:
            log.error("Timeout triggering workflow %s", workflow_id)
            return ToolResult(False, f"Timeout al ejecutar workflow '{workflow_id}' (>{n8n_config.timeout}s).", "🔗 N8N")
        except httpx.HTTPStatusError as e:
            log.error("HTTP error triggering workflow %s: %s", workflow_id, e)
            if e.response.status_code == 404:
                return ToolResult(False, f"Workflow '{workflow_id}' no encontrado (404). Verificá que el webhook exista en n8n.", "🔗 N8N")
            else:
                return ToolResult(False, f"Error HTTP {e.response.status_code} al ejecutar '{workflow_id}'.", "🔗 N8N")
        except Exception as e:
            log.error("Failed to trigger workflow %s: %s", workflow_id, e, exc_info=True)
            return ToolResult(False, f"Error al conectar con n8n: {e}", "🔗 N8N")
    
    return {
        "trigger_workflow": tool_trigger_workflow
    }
