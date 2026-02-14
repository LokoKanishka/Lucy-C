import sys
import os
import requests
import yaml
import traceback

print("=== INICIO DIAGNÓSTICO LUCY ===")

# 1. Verificar entorno y rutas
print(f"\n[1] Entorno:")
print(f"   CWD: {os.getcwd()}")
print(f"   Python: {sys.executable}")
print(f"   Mimic3 en PATH: {'mimic3' in os.environ.get('PATH', '')}")

# 2. Verificar Configuración
print(f"\n[2] Configuración (config/config.yaml):")
try:
    with open("config/config.yaml", "r") as f:
        cfg = yaml.safe_load(f)
    ollama_host = cfg.get('ollama', {}).get('host', 'No definido')
    print(f"   Ollama Host configurado: {ollama_host}")
    print(f"   Provider configurado: {cfg.get('llm', {}).get('provider', 'No definido')}")
    print(f"   Modelo configurado: {cfg.get('ollama', {}).get('model', 'No definido')}")
except Exception as e:
    print(f"   ERROR CRÍTICO LEYENDO CONFIG: {e}")
    sys.exit(1)

# 3. Prueba de conexión RAW a Ollama
print(f"\n[3] Prueba de conexión directa a Ollama ({ollama_host}/api/tags):")
try:
    url = f"{ollama_host.rstrip('/')}/api/tags"
    r = requests.get(url, timeout=5)
    print(f"   Status Code: {r.status_code}")
    if r.status_code == 200:
        models = [m['name'] for m in r.json().get('models', [])]
        print(f"   Modelos detectados (RAW): {models}")
        if "lucy:32b" in models:
            print("   ✅ Modelo lucy:32b ENCONTRADO.")
        else:
            print("   ❌ Modelo lucy:32b NO ENCONTRADO en la lista.")
    else:
        print(f"   ❌ Error en respuesta: {r.text}")
except Exception as e:
    print(f"   ❌ FALLO DE CONEXIÓN: {e}")

# 4. Prueba usando el código de Lucy (Simulación del Backend)
print(f"\n[4] Prueba interna de librerías Lucy:")
try:
    sys.path.append(os.getcwd())
    from lucy_c.config import LucyConfig
    from lucy_c.ollama_llm import OllamaLLM
    
    real_cfg = LucyConfig.load("config/config.yaml")
    llm = OllamaLLM(real_cfg.ollama)
    
    print("   Intentando list_models_detailed()...")
    detailed = llm.list_models_detailed()
    print(f"   ✅ ÉXITO. La librería devolvió {len(detailed)} modelos.")
    for m in detailed:
        print(f"      - {m.name} ({m.size_gb} GB)")
        
except Exception as e:
    print("   ❌ FALLO EN CÓDIGO INTERNO:")
    traceback.print_exc()

print("\n=== FIN DIAGNÓSTICO ===")
