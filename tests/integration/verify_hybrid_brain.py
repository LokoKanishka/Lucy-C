#!/usr/bin/env python3
"""Verification script for Hybrid Brain (SOTA delegation)."""
import sys
import json
import logging
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
import time

root = Path(__file__).resolve().parents[2]
sys.path.append(str(root))

from lucy_c.config import LucyConfig
from lucy_c.pipeline import Moltbot

logging.basicConfig(level=logging.INFO, format="%(name)s - %(levelname)s - %(message)s")

received_requests = []

class MockSOTAHandler(BaseHTTPRequestHandler):
    """Mock n8n SOTA webhook handler."""
    
    def log_message(self, format, *args):
        pass
    
    def do_POST(self):
        """Handle POST requests to SOTA webhook."""
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        
        try:
            payload = json.loads(body) if body else {}
        except json.JSONDecodeError:
            payload = {"raw": body.decode('utf-8')}
        
        received_requests.append({
            "path": self.path,
            "payload": payload,
            "timestamp": time.time()
        })
        
        print(f"[MOCK SOTA] Received request: {self.path}")
        print(f"[MOCK SOTA] Prompt: {payload.get('prompt', 'N/A')[:100]}...")
        
        # Simulate SOTA response based on prompt
        prompt = payload.get("prompt", "")
        
        # Generate intelligent mock response
        if "cuántica" in prompt.lower() or "quantum" in prompt.lower():
            sota_response = """La física cuántica es fascinante. Los principios fundamentales incluyen:

1. **Superposición**: Las partículas pueden existir en múltiples estados simultáneamente hasta que se miden.
2. **Entrelazamiento Cuántico**: Partículas pueden estar correlacionadas de forma instantánea sin importar la distancia.
3. **Principio de Incertidumbre de Heisenberg**: No podemos conocer simultáneamente con precisión la posición y el momento de una partícula.

Estos fenómenos desafían nuestra intuición clásica pero son fundamentales para entender el universo a escalas subatómicas."""
        elif "2025" in prompt or "2026" in prompt or "actual" in prompt.lower():
            sota_response = """Basándome en mi conocimiento actualizado (2026), puedo decir que:

- La IA generativa ha alcanzado capacidades multimodales avanzadas
- Los modelos de lenguaje ahora superan los 1T de parámetros en configuraciones SOTA
- La computación cuántica está en una etapa de "ventaja cuántica práctica" para problemas específicos
- Las regulaciones de IA en Europa (AI Act) están en plena implementación

Esta información está actualizada hasta febrero de 2026."""
        else:
            sota_response = f"""He procesado tu consulta con capacidades SOTA. Aquí está mi respuesta detallada:

{prompt}

Esta es una respuesta generada por un modelo de última generación con acceso a conocimiento actualizado y capacidades de razonamiento avanzadas."""

        response = {
            "success": True,
            "response": sota_response,
            "model": "gemini-2.0-flash-001 (mock)",
            "tokens": len(sota_response.split())
        }
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())

def start_mock_server(port=0):
    """Start mock SOTA server."""
    server = HTTPServer(('localhost', port), MockSOTAHandler)
    actual_port = server.server_address[1]
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    print(f"[MOCK SOTA] Server started on port {actual_port}")
    return server, actual_port

def test_hybrid_brain():
    """Test hybrid brain functionality."""
    print("--- INICIANDO TEST DE CEREBRO HÍBRIDO ---\n")
    
    # Start mock server
    mock_server, mock_port = start_mock_server(0)
    time.sleep(0.5)
    
    # Load config and override n8n URL
    cfg = LucyConfig.load(root / "config" / "config.yaml")
    cfg.n8n.base_url = f"http://localhost:{mock_port}"
    
    moltbot = Moltbot(cfg)
    
    print(f"n8n config: {cfg.n8n.base_url}")
    print(f"Tools registradas: {list(moltbot.tool_router.tools.keys())}\n")
    
    # Test cases
    test_cases = [
        {
            "name": "Delegación por Complejidad (Física Cuántica)",
            "prompt": "Explicame en detalle los principios fundamentales de la física cuántica",
            "expect_delegation": True,
            "check_response": "superposición"
        },
        {
            "name": "Delegación por Conocimiento Actual",
            "prompt": "Contame sobre los avances en IA durante 2025 y 2026",
            "expect_delegation": True,
            "check_response": "2026"
        },
        {
            "name": "Pregunta Simple (Sin Delegación)",
            "prompt": "¿Cuál es la capital de Argentina?",
            "expect_delegation": False,
            "check_response": "Buenos Aires"
        }
    ]
    
    for i, case in enumerate(test_cases):
        print(f"\n[TEST {i+1}]: {case['name']}")
        print(f"User: {case['prompt']}")
        
        received_requests.clear()
        
        result = moltbot.run_turn_from_text(case['prompt'], session_user="tester")
        print(f"Lucy: {result.reply[:300]}...")
        
        # Check if delegation occurred
        if case.get("expect_delegation"):
            if received_requests:
                print(f"✅ SOTA delegation triggered")
                if case.get("check_response") and case["check_response"].lower() in result.reply.lower():
                    print(f"RESULTADO: ✅ EXITO - Respuesta SOTA integrada")
                else:
                    print(f"RESULTADO: ⚠️ Delegación OK pero respuesta incompleta")
            else:
                print(f"RESULTADO: ❌ FALLO - No se delegó a SOTA")
        else:
            if not received_requests:
                if case.get("check_response") and case["check_response"].lower() in result.reply.lower():
                    print(f"RESULTADO: ✅ EXITO - Respondió localmente")
                else:
                    print(f"RESULTADO: ⚠️ Respuesta local pero incompleta")
            else:
                print(f"RESULTADO: ⚠️ Delegó innecesariamente")
    
    mock_server.shutdown()
    print("\n[MOCK SOTA] Server stopped")

if __name__ == "__main__":
    test_hybrid_brain()
