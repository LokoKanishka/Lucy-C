import logging
from lucy_c.tool_router import ToolResult

log = logging.getLogger("LucyC.CognitiveTools")

def create_cognitive_tools(n8n_tools):
    """Factory function to create cognitive delegation tools."""
    
    def tool_ask_sota(args, ctx):
        """Delegate a complex question to a SOTA model via n8n.
        
        This tool is used when Lucy's local model isn't sufficient for:
        - Complex reasoning tasks
        - Knowledge beyond her training cutoff
        - Creative tasks requiring SOTA capabilities
        
        Args:
            args[0]: prompt (str) - The question to ask the SOTA model
        """
        if not args:
            return ToolResult(False, "Falta la pregunta para el modelo SOTA.", "🧠 SOTA")
        
        prompt = args[0]
        log.info("Delegating to SOTA model: %s", prompt[:100])
        
        # Use the trigger_workflow tool from n8n_tools
        trigger_workflow = n8n_tools.get("trigger_workflow")
        if not trigger_workflow:
            return ToolResult(False, "n8n no está configurado. No puedo acceder a modelos SOTA.", "🧠 SOTA")
        
        # Prepare payload with the prompt
        import json
        payload_json = json.dumps({"prompt": prompt, "source": "lucy-local"})
        
        # Trigger the SOTA workflow
        result = trigger_workflow(["ask-sota", payload_json], ctx)
        
        if result.success:
            # Extract the SOTA response from the result
            return ToolResult(True, f"Respuesta del modelo SOTA:\n{result.message}", "🧠 SOTA")
        else:
            return ToolResult(False, f"Error al consultar SOTA: {result.message}", "🧠 SOTA")
    
    return {
        "ask_sota": tool_ask_sota
    }
