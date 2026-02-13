import httpx
import sys
import os

# Adición de la ruta del proyecto al PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from lucy_c.config import LucyConfig

# Cargar configuración real
try:
    config_path = "/home/lucy-ubuntu/Lucy-C/config/config.yaml"
    cfg = LucyConfig.load(config_path)
    url = f"{cfg.ollama.host.rstrip('/')}/api/tags"
    print(f"Intentando conectar a: {url}")
    
    with httpx.Client(timeout=5.0) as client:
        r = client.get(url)
        print(f"Status Code: {r.status_code}")
        if r.status_code == 200:
            print("¡ÉXITO! Modelos encontrados:")
            tags = r.json()
            names = [m['name'] for m in tags.get('models', [])]
            print(names)
        else:
            print(f"ERROR: Ollama respondió con error: {r.text}")
except Exception as e:
    print(f"FALLO CRÍTICO DE CONEXIÓN: {e}")
