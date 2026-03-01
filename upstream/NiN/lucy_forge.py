import os
import sys
import json
import requests
import re

OLLAMA_URL = "http://localhost:11434/api/chat"
N8N_URL = "http://localhost:5678/api/v1/workflows"
MODEL = "huihui_ai/qwq-abliterated:32b-Q6_K"

# Leer Llave del Bunker
API_KEY = ""
if os.path.exists(".env"):
    with open(".env", "r") as f:
        for line in f:
            if line.startswith("N8N_API_KEY="):
                API_KEY = line.strip().split("=")[1]

if not API_KEY:
    print("[FATAL] N8N_API_KEY no encontrada en .env")
    sys.exit(1)

def extirpar_json(texto):
    # 1. Ignorar los pensamientos de QwQ
    texto_limpio = re.sub(r'<think>.*?</think>', '', texto, flags=re.DOTALL)
    
    # 2. Cazar bloques de markdown si existen
    match = re.search(r'```(?:json)?(.*?)```', texto_limpio, flags=re.DOTALL)
    if match:
        texto_limpio = match.group(1)
        
    # 3. Forzar el inicio y fin estructural
    inicio = texto_limpio.find('{')
    fin = texto_limpio.rfind('}')
    
    if inicio != -1 and fin != -1:
        return texto_limpio[inicio:fin+1]
    return texto_limpio

def forjar(prompt_usuario):
    # Cargar prompt externo
    try:
        with open("prompts/architect_v2_prompt.md", "r") as f:
            sys_prompt = f.read().strip()
    except Exception as e:
        print(f"[FATAL] No se pudo leer architect_v2_prompt.md: {e}")
        sys_prompt = "Eres el Arquitecto del Proyecto LUCY. Responde UNICAMENTE con código JSON válido. Tu estructura DEBE contener 'name', 'nodes' y 'connections'. Cero texto conversacional."
        
    
    for intento in range(1, 4):
        print(f"\n[SYSTEM] Forging neural pathway... (Attempt {intento}/3)")
        try:
            res = requests.post(OLLAMA_URL, json={
                "model": MODEL,
                "stream": False,
                "messages": [
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": prompt_usuario}
                ]
            })
            res.raise_for_status()
            texto_crudo = res.json()["message"]["content"]
            
            print("[SYSTEM] Scanning core logic and extracting JSON...")
            json_puro = extirpar_json(texto_crudo)
            
            try:
                flujo_validado = json.loads(json_puro)
                print("[SUCCESS] JSON Compilation flawless.")
                return flujo_validado
            except json.JSONDecodeError as e:
                print(f"[WARN] Corrupted schema detected: {e}. Triggering auto-correction...")
                prompt_usuario = f"Tu salida anterior fallo en el parseo por un error de sintaxis: {e}. Re-evalua y escupe SOLO el JSON corregido."
                
        except Exception as e:
            print(f"[FATAL] Cognitive interface down: {e}")
            sys.exit(1)
            
    print("[FATAL] Max auto-retries exhausted. Neural compilation failed.")
    sys.exit(1)

def inyectar(datos_flujo):
    print("[SYSTEM] Injecting payload into n8n matrix...")
    if "settings" not in datos_flujo:
        datos_flujo["settings"] = {"executionOrder": "v1"}
        
    with open("debug_forge.json", "w") as f:
        json.dump(datos_flujo, f, indent=2)

    headers = {
        "X-N8N-API-KEY": API_KEY,
        "Content-Type": "application/json"
    }
    res = requests.post(N8N_URL, headers=headers, json=datos_flujo)
    
    if res.status_code == 200:
        print(f"\n✅ [MATRIX UPDATED] Flow inyectado exitosamente con ID: {res.json().get('id', 'Unknown')}")
        print(">>> VUELVE A n8n Y PRESIONA F5 <<<")
    else:
        print(f"\n❌ [FATAL] Injection rejected by n8n. Code {res.status_code}: {res.text}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 lucy_forge.py '<tu instruccion>'")
        sys.exit(1)
    
    inyectar(forjar(sys.argv[1]))
