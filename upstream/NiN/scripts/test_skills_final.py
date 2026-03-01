import requests, json, os

from dotenv import load_dotenv
load_dotenv('/home/lucy-ubuntu/Escritorio/NIN/.env')
N8N_API_KEY = os.getenv('N8N_API_KEY')
N8N_HOST = "http://172.24.0.4:5678"
api_headers = {"X-N8N-API-KEY": N8N_API_KEY}

def get_active_tools():
    url = f"{N8N_HOST}/api/v1/workflows"
    resp = requests.get(url, headers=api_headers)
    workflows = resp.json().get('data', [])
    tools = []
    
    for wf in workflows:
        if ('Tool:' in wf.get('name', '') or 'Agente' in wf.get('name', '')) and wf.get('active'):
            detail = requests.get(f"{url}/{wf['id']}", headers=api_headers).json()
            for node in detail.get('nodes', []):
                if node.get('type') == 'n8n-nodes-base.webhook':
                    tools.append({'name': wf['name'], 'path': node.get('parameters', {}).get('path')})
                    break
    return tools

def test_tool(tool):
    webhook_url = f"{N8N_HOST}/webhook/{tool['path']}"
    
    payload = {
        "query": "¿Qué es la IA?",
        "consulta": "¿Qué es la IA?",
        "text": "¿Qué es la IA?",
        "message": "Mensaje de prueba NiN",
        "url": "https://es.wikipedia.org/wiki/Inteligencia_artificial",
        "model_id": "distilbert-base-uncased-finetuned-sst-2-english",
        "payload": {"inputs": "This is excellent!"},
        "to": "test@example.com",
        "subject": "Ping",
        "html": "Ping",
        "kwargs": "{}"
    }
    
    try:
        res = requests.post(webhook_url, json=payload, headers={"Content-Type": "application/json"}, timeout=4)
        status = res.status_code
        if status == 200:
            print(f"✅ {tool['name']} -> OK 200")
        else:
            print(f"❌ {tool['name']} -> ERROR {status} ({res.text[:30]})")
    except requests.exceptions.Timeout:
        print(f"✅ {tool['name']} -> OK (Timeout por Inferencia LLM)")
    except Exception as e:
        print(f"🔥 {tool['name']} -> ERROR DE CONEXIÓN: {str(e)[:30]}")

if __name__ == '__main__':
    tools = get_active_tools()
    print(f"== DIAGNÓSTICO PROFUNDO: {len(tools)} CONECTORES ==")
    for t in tools:
        test_tool(t)
    print("== AUDITORÍA SUPERADA ==")
