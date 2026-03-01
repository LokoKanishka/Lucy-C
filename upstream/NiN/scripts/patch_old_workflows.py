import json, os, requests

def fix_agente(data):
    for node in data.get('nodes', []):
        if node.get('name') == 'Formatear Consulta':
            params = node.get('parameters', {}).get('values', {}).get('string', [])
            for p in params:
                if p.get('name') == 'chatInput':
                    p['value'] = '={{ $json.body && $json.body.consulta ? $json.body.consulta : ($json.consulta || "Prueba del agente secreto") }}'
    return data

def fix_research(data):
    for node in data.get('nodes', []):
        if node.get('name') == 'Fetch Source':
            code = node.get('parameters', {}).get('jsCode', '')
            if 'if (!url)' not in code:
                new_code = 'let url = items[0].json.url;\nif (!url && items[0].json.body && items[0].json.body.url) url = items[0].json.body.url;\nif (!url) return [{ json: { url: "N/A", transcript: "No URL provided for research." } }];\n' + code.replace('const url = items[0].json.url;', '')
                node['parameters']['jsCode'] = new_code
    return data

def fix_colmena(data):
    for node in data.get('nodes', []):
        if node.get('name') == 'Google Gemini (Raw API)':
            params = node.get('parameters', {}).get('bodyParameters', {}).get('parameters', [])
            for p in params:
                if p.get('name') == 'contents':
                    p['value'] = "={{[{ 'parts': [{ 'text': ($json.body && $json.body.query) ? $json.body.query : 'Por favor responde SOLO con la palabra PING.' }] }]}}"
    return data

def fix_telegram(data):
    for node in data.get('nodes', []):
        if node.get('name') == 'Telegram HTTP':
            params = node.get('parameters', {}).get('bodyParameters', {}).get('parameters', [])
            for p in params:
                if p.get('name') == 'text':
                    p['value'] = '={{ $json.body && $json.body.message ? $json.body.message : "Prueba de conexión exitosa desde NiN." }}'
    return data

fixes = {
    'dump_8RwngQmsa4ObRh2I.json': fix_agente,
    'dump_JtGILLT7wIAzBrVs.json': fix_research,
    'dump_VFzrIjk5iJW0yueV.json': fix_colmena,
    'dump_WrslsGzYsDP8hJZT.json': fix_telegram
}

env_path = '/home/lucy-ubuntu/Escritorio/NIN/.env'
api_key = ''
with open(env_path, 'r') as env:
    for line in env:
        if line.startswith('N8N_API_KEY='):
            api_key = line.strip().split('=', 1)[1]

headers = {'X-N8N-API-KEY': api_key, 'Content-Type': 'application/json'}

for file, fixer in fixes.items():
    path = f'/home/lucy-ubuntu/Escritorio/NIN/docs/{file}'
    with open(path, 'r') as f:
        data = json.load(f)
    
    data = fixer(data)
    wid = data.get('id')
    
    # Payload valid for PUT
    payload = {
        "name": data.get("name"),
        "nodes": data.get("nodes"),
        "connections": data.get("connections"),
        "settings": data.get("settings", {})
    }
    
    r = requests.put(f'http://172.24.0.4:5678/api/v1/workflows/{wid}', headers=headers, json=payload, timeout=10)
    print(f"Upload {wid}: {r.status_code}")
    if r.status_code != 200:
        print(f"Error: {r.text}")
    
    # Activate
    r2 = requests.post(f'http://172.24.0.4:5678/api/v1/workflows/{wid}/activate', headers=headers, timeout=10)
    print(f"Activate {wid}: {r2.status_code}")
