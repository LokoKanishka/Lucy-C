import sys
import os

# Añadimos el directorio actual al path para poder importar n8n_mcp_server
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))

try:
    import n8n_mcp_server
    print("Iniciando Mapeo de Contexto vía Agente Secreto (MCP)...")
    print("Esperando respuesta del modelo QwQ de 32B...\n")
    
    result = n8n_mcp_server.invoke_secret_agent("Analiza brevemente el repositorio. MÁXIMO una oración.")
    
    print("========================================")
    print("RESPUESTA RECIBIDA:")
    print(result)
    print("========================================")
except Exception as e:
    print(f"Error: {e}")
