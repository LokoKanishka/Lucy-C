import requests

# Configuración del Endpoint (Webhook de NiN)
# Apunta al puerto 5678 de n8n
WEBHOOK_URL = "http://127.0.0.1:5678/webhook/tesis"

print("🦷 SYSTEM: NiN Protocol Initiated...")
print("📡 Conectando con el Arquitecto (LUCY 120B)...")

try:
    # Payload vacío (Gatillo simple)
    response = requests.post(WEBHOOK_URL, json={})
    
    if response.status_code == 200:
        print("\n✅ [ÉXITO] Señal recibida por n8n.")
        print("🧠 El flujo de análisis ha comenzado.")
    else:
        print(f"\n❌ [ERROR] Respuesta del servidor: {response.status_code}")
        print(response.text)

except Exception as e:
    print(f"\n💀 [FATAL] No se pudo conectar con NiN: {e}")
