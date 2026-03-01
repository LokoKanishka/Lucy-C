#!/usr/bin/env python3
import json
import os
import sys
import urllib.request
import urllib.error

def die(msg: str, code: int = 1):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(code)

def http_json(method: str, url: str, api_key: str, body_obj=None):
    headers = {
        "Accept": "application/json",
        "X-N8N-API-KEY": api_key,
    }
    data = None
    if body_obj is not None:
        data = json.dumps(body_obj).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {url} -> HTTP {e.code}: {raw}") from None

def sanitize_workflow(obj: dict) -> dict:
    # Cuerpo “seguro” para API: lo mínimo estándar.
    # Evitamos campos que suelen romper validaciones (id, timestamps, etc).
    out = {
        "name": obj.get("name", "Untitled"),
        "nodes": obj.get("nodes", []),
        "connections": obj.get("connections", {}),
        "settings": obj.get("settings", {}),
    }
    # staticData/pinData/meta/versionId suelen ser opcionales o rechazados según versión.
    return out

def main():
    if len(sys.argv) != 2:
        die("Uso: scripts/n8n_upsert_workflow.py workflows/mi_workflow.json")

    wf_path = sys.argv[1]
    if not os.path.isfile(wf_path):
        die(f"No existe el archivo: {wf_path}")

    base = os.environ.get("N8N_URL", "").rstrip("/")
    api_key = os.environ.get("N8N_API_KEY", "")
    api_ver = os.environ.get("N8N_API_VERSION", "1")

    if not base:
        die("Falta N8N_URL (ej: http://127.0.0.1:5678)")
    if not api_key:
        die("Falta N8N_API_KEY (API key creada en Settings → n8n API)")

    with open(wf_path, "r", encoding="utf-8") as f:
        wf_raw = json.load(f)

    wf = sanitize_workflow(wf_raw)
    if not wf["nodes"]:
        die("El workflow no tiene nodes. Exportaste bien el JSON desde n8n?")

    # 1) Buscar si ya existe un workflow con el mismo nombre
    list_url = f"{base}/api/v{api_ver}/workflows"
    _, response_data = http_json("GET", list_url, api_key)
    
    lst = response_data.get("data", response_data) if isinstance(response_data, dict) else response_data
    if not isinstance(lst, list):
        die(f"Respuesta inesperada listando workflows: {type(lst)}")

    matches = [x for x in lst if isinstance(x, dict) and x.get("name") == wf["name"]]
    if len(matches) > 1:
        die(f"Hay {len(matches)} workflows con el mismo nombre '{wf['name']}'. Renombrá uno para upsert determinista.")
    elif len(matches) == 1:
        wf_id = matches[0].get("id")
        if wf_id is None:
            die("No pude leer el id del workflow existente.")
        put_url = f"{base}/api/v{api_ver}/workflows/{wf_id}"
        # Ojo: el schema puede ser estricto; mantenemos body mínimo.
        _, updated = http_json("PUT", put_url, api_key, wf)
        print(json.dumps({"action": "updated", "id": wf_id, "name": wf["name"]}, ensure_ascii=False))
    else:
        post_url = f"{base}/api/v{api_ver}/workflows"
        _, created = http_json("POST", post_url, api_key, wf)
        new_id = created.get("id") if isinstance(created, dict) else None
        print(json.dumps({"action": "created", "id": new_id, "name": wf["name"]}, ensure_ascii=False))

if __name__ == "__main__":
    main()
