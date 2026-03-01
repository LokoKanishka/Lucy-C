import requests, json, os
from dotenv import load_dotenv

load_dotenv('/home/lucy-ubuntu/Escritorio/NIN/.env')
N8N_API_KEY = os.getenv('N8N_API_KEY')
N8N_HOST = "http://172.24.0.4:5678"

# Headers for API
api_headers = {"X-N8N-API-KEY": N8N_API_KEY}

def get_active_tools():
    url = f"{N8N_HOST}/api/v1/workflows"
    resp = requests.get(url, headers=api_headers)
    workflows = resp.json().get('data', [])
    tools = []
    
    for wf in workflows:
        if ('Tool:' in wf.get('name', '') or 'Agente' in wf.get('name', '')) and wf.get('active'):
            # Fetch full workflow details to get nodes
            detail_resp = requests.get(f"{url}/{wf['id']}", headers=api_headers)
            detail = detail_resp.json()
            nodes = detail.get('nodes', [])
            webhook_path = None
            for node in nodes:
                if node.get('type') == 'n8n-nodes-base.webhook':
                    webhook_path = node.get('parameters', {}).get('path')
                    break
            
            if webhook_path:
                tools.append({
                    'name': wf['name'],
                    'id': wf['id'],
                    'path': webhook_path
                })
    return tools

def test_tool(tool):
    webhook_url = f"{N8N_HOST}/webhook/{tool['path']}"
    
    # Generic safe payload that most tools can either ignore or respond to without crashing
    payload = {
        "query": "Test",
        "text": "Test",
        "model_id": "distilbert-base-uncased-finetuned-sst-2-english",
        "payload": {"inputs": "Test"},
        "to": "test@example.com",
        "subject": "Test",
        "html": "Test",
        "kwargs": "{}"
    }
    
    try:
        res = requests.post(webhook_url, json=payload, headers={"Content-Type": "application/json"}, timeout=15)
        status = res.status_code
        try:
            response_data = res.json()
            response_str = str(response_data)[:100]
        except:
            response_str = res.text[:100]
            
        if status == 200:
            print(f"✅ {tool['name']} (/{tool['path']}) -> OK")
        else:
            print(f"❌ {tool['name']} (/{tool['path']}) -> ERROR {status}: {response_str}")
    except Exception as e:
        print(f"🔥 {tool['name']} (/{tool['path']}) -> EXCEPTION: {str(e)}")

if __name__ == '__main__':
    print("Iniciando auditoría 1x1 de Skills Activos...")
    tools = get_active_tools()
    print(f"Detectados {len(tools)} Webhooks activos. Testeando...")
    for t in tools:
        test_tool(t)
    print("Auditoría finalizada.")
