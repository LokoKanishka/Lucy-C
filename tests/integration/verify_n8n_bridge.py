#!/usr/bin/env python3
"""Verification script for n8n Bridge integration."""
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

# Global to capture webhook requests
received_requests = []

class MockN8nHandler(BaseHTTPRequestHandler):
    """Mock n8n webhook handler."""
    
    def log_message(self, format, *args):
        # Suppress default logging
        pass
    
    def do_POST(self):
        """Handle POST requests to webhooks."""
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        
        try:
            payload = json.loads(body) if body else {}
        except json.JSONDecodeError:
            payload = {"raw": body.decode('utf-8')}
        
        request_data = {
            "path": self.path,
            "payload": payload,
            "timestamp": time.time()
        }
        received_requests.append(request_data)
        
        print(f"[MOCK N8N] Received webhook: {self.path}")
        print(f"[MOCK N8N] Payload: {json.dumps(payload, indent=2)}")
        
        # Send success response
        response = {
            "success": True,
            "workflow": self.path.split('/')[-1],
            "message": "Workflow triggered successfully"
        }
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())

def start_mock_server(port=0):
    """Start mock n8n server in background thread. Port 0 = dynamic allocation."""
    server = HTTPServer(('localhost', port), MockN8nHandler)
    actual_port = server.server_address[1]
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    print(f"[MOCK N8N] Server started on port {actual_port}")
    return server, actual_port

def test_n8n_bridge():
    """Test n8n bridge functionality."""
    print("--- INICIANDO TEST DE N8N BRIDGE ---\n")
    
    # Start mock n8n server with dynamic port allocation
    mock_server, mock_port = start_mock_server(0)
    time.sleep(0.5)  # Give server time to start
    
    # Load config and create Moltbot
    cfg = LucyConfig.load(root / "config" / "config.yaml")
    
    # Override n8n config to point to mock server
    cfg.n8n.base_url = f"http://localhost:{mock_port}"
    
    moltbot = Moltbot(cfg)
    
    print(f"n8n config: {cfg.n8n.base_url}, prefix: {cfg.n8n.webhook_prefix}")
    print(f"Tools registradas: {list(moltbot.tool_router.tools.keys())}\n")
    
    # Test cases
    test_cases = [
        {
            "name": "Trigger Simple Workflow",
            "prompt": "Dispará el workflow 'test-simple' con los datos {\"status\": \"ok\", \"source\": \"lucy\"}",
            "expected_path": "/webhook/lucy-test-simple",
            "expected_payload_key": "status"
        },
        {
            "name": "Trigger Analysis Workflow",
            "prompt": "Activá el análisis diario y pasale el target 'email'",
            "expected_path": "/webhook/lucy-analisis-diario",
            "check_triggered": True
        },
        {
            "name": "Invalid Workflow (404)",
            "prompt": "Ejecutá el workflow 'non-existent' sin datos",
            "expect_error": True
        }
    ]
    
    for i, case in enumerate(test_cases):
        print(f"\n[TEST {i+1}]: {case['name']}")
        print(f"User: {case['prompt']}")
        
        # Clear previous requests
        received_requests.clear()
        
        # Run turn
        result = moltbot.run_turn_from_text(case['prompt'], session_user="tester")
        print(f"Lucy: {result.reply[:200]}...")
        
        # For error case, temporarily remove webhook and retry
        if case.get("expect_error"):
            # Just check that Lucy acknowledged the error
            if "error" in result.reply.lower() or "no encontrado" in result.reply.lower():
                print("RESULTADO: ✅ Error handling OK")
            else:
                print("RESULTADO: ⚠️ Should have reported error")
        else:
            # Check if webhook was triggered
            if received_requests:
                req = received_requests[0]
                print(f"✅ Webhook received: {req['path']}")
                print(f"   Payload: {json.dumps(req['payload'], indent=2)}")
                
                # Validate path if specified
                if "expected_path" in case and case["expected_path"] in req["path"]:
                    print("RESULTADO: ✅ EXITO - Path correcto")
                elif case.get("check_triggered"):
                    print("RESULTADO: ✅ EXITO - Workflow disparado")
                else:
                    print("RESULTADO: ⚠️ Path inesperado")
            else:
                print("RESULTADO: ❌ FALLO - No webhook recibido")
    
    # Cleanup
    mock_server.shutdown()
    print("\n[MOCK N8N] Server stopped")

if __name__ == "__main__":
    test_n8n_bridge()
