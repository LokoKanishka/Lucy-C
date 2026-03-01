import json
import os
import subprocess

files = ['groq_processor.json', 'tavily_search.json', 'hf_processor.json', 'resend_mailer.json', 'consultar_cerebro_fixed.json']
base_path = '/home/lucy-ubuntu/Escritorio/NIN/docs'

for f in files:
    path = f"{base_path}/{f}"
    try:
        with open(path, 'r') as file:
            content = file.read()
            # Si el JSON est\u00e1 roto por mi sed anterior, lo trato de limpiar.
            # \u0022\u0022id\u0022: \u0022wh-groq\u0022\u0022 -> \u0022id\u0022: \u0022wh-groq\u0022
            content = content.replace('""id":', '"id":').replace('""', '"')
        
        data = json.loads(content)
        for node in data.get('nodes', []):
            if node.get('type') == 'n8n-nodes-base.webhook':
                node['webhookId'] = f"wh-{node.get('id', 'bypass')}"
        
        with open(path, 'w') as file:
            json.dump(data, file, indent=2)
        print(f"Fixed formatting of {f}")
    except Exception as e:
        print(f"Error parseando {f}: {e}")

# Ahora los subimos
env_path = '/home/lucy-ubuntu/Escritorio/NIN/.env'
api_key = ''
with open(env_path, 'r') as env:
    for line in env:
        if line.startswith('N8N_API_KEY='):
            api_key = line.strip().split('=', 1)[1]

for f in files:
    path = f"{base_path}/{f}"
    cmd_upload = ['curl', '-s', '-X', 'POST', 'http://172.24.0.4:5678/api/v1/workflows', '-H', f'X-N8N-API-KEY: {api_key}', '-H', 'Content-Type: application/json', '-d', f'@{path}']
    res = subprocess.run(cmd_upload, capture_output=True, text=True)
    try:
        wid = json.loads(res.stdout).get('id')
        if wid:
            print(f"Uploaded {f} with ID {wid}")
            cmd_act = ['curl', '-s', '-X', 'POST', f'http://172.24.0.4:5678/api/v1/workflows/{wid}/activate', '-H', f'X-N8N-API-KEY: {api_key}']
            res_act = subprocess.run(cmd_act, capture_output=True, text=True)
            print(f"Activated {wid}: {res_act.stdout}")
        else:
            print(f"Upload failed for {f}: {res.stdout}")
    except:
        print(f"Upload failed parsing output for {f}: {res.stdout}")
