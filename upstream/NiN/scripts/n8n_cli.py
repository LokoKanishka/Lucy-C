#!/usr/bin/env python3
"""
n8n_cli.py — Control directo de n8n desde Antigravity

Se conecta a la IP interna del container Docker (red bridge),
evitando docker exec y sus problemas de procesos zombies.

Uso:
    python3 scripts/n8n_cli.py test
    python3 scripts/n8n_cli.py list
    python3 scripts/n8n_cli.py inspect <workflow_id>
    python3 scripts/n8n_cli.py get <workflow_id>
    python3 scripts/n8n_cli.py update <workflow_id> <json_file>
    python3 scripts/n8n_cli.py create <json_file>
    python3 scripts/n8n_cli.py delete <workflow_id>
    python3 scripts/n8n_cli.py activate <workflow_id>
    python3 scripts/n8n_cli.py deactivate <workflow_id>
"""
import json
import os
import subprocess
import sys
import urllib.request
import urllib.error

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.dirname(SCRIPT_DIR)
ENV_FILE = os.path.join(REPO_DIR, ".env")
CONTAINER = "n8n-lucy"
TIMEOUT = 15  # seconds per request


def load_api_key() -> str:
    if not os.path.isfile(ENV_FILE):
        die("No existe .env en " + REPO_DIR)
    with open(ENV_FILE) as f:
        for line in f:
            line = line.strip()
            if line.startswith("N8N_API_KEY="):
                return line.split("=", 1)[1].strip()
    die("N8N_API_KEY no encontrada en .env")


def die(msg: str):
    print(json.dumps({"error": msg}))
    sys.exit(1)


def get_container_ip() -> str:
    """Obtiene la IP interna del container. Cachea en .n8n_ip para evitar docker inspect en cada llamada."""
    cache_file = os.path.join(REPO_DIR, ".n8n_ip")

    # 1. Try cached IP first (validate it's still reachable)
    if os.path.isfile(cache_file):
        cached_ip = open(cache_file).read().strip()
        if cached_ip:
            try:
                urllib.request.urlopen(f"http://{cached_ip}:5678/healthz", timeout=3)
                return cached_ip
            except Exception:
                pass  # Cache stale, refresh

    # 2. Get fresh IP from docker inspect
    try:
        result = subprocess.run(
            ["docker", "inspect", CONTAINER, "--format",
             "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}"],
            capture_output=True, text=True, timeout=2
        )
        ip = result.stdout.strip()
        if ip:
            with open(cache_file, "w") as f:
                f.write(ip)
            return ip
    except Exception:
        pass # Fallback agresivo al escáner de red

    try:
        import concurrent.futures
        def check_ip(test_ip: str) -> str:
            try:
                urllib.request.urlopen(f"http://{test_ip}:5678/healthz", timeout=0.3)
                return test_ip
            except Exception:
                return ""

        ips_to_test = ["127.0.0.1"]
        for subnet in range(17, 32):
            for host in range(1, 6):
                ips_to_test.append(f"172.{subnet}.0.{host}")

        with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
            for future in concurrent.futures.as_completed([executor.submit(check_ip, i) for i in ips_to_test]):
                res = future.result()
                if res:
                    with open(cache_file, "w") as f:
                        f.write(res)
                    return res
    except Exception:
        pass

    die(f"Error crítico: Docker no responde y el escáner falló en encontrar n8n")


def api_request(base_url: str, api_key: str, method: str, path: str,
                body: dict | None = None) -> tuple[int, dict]:
    """HTTP request directo al container via IP interna."""
    url = f"{base_url}/api/v1{path}"
    headers = {
        "Accept": "application/json",
        "X-N8N-API-KEY": api_key,
    }
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        try:
            return e.code, json.loads(raw)
        except json.JSONDecodeError:
            return e.code, {"error": raw[:500]}
    except urllib.error.URLError as e:
        die(f"No se puede conectar a {url}: {e.reason}")
    except TimeoutError:
        die(f"Timeout ({TIMEOUT}s) en {method} {path}")


def strip_heavy(wf: dict) -> dict:
    """Remueve campos pesados de un workflow para respuestas más rápidas."""
    for key in ("activeVersion", "shared", "staticData", "pinData", "tags"):
        wf.pop(key, None)
    return wf


def cmd_test(base: str, key: str, args: list):
    status, data = api_request(base, key, "GET", "/workflows?limit=1")
    print(json.dumps({"ok": True, "status": status, "message": "Connected to n8n!",
                       "base_url": base}))


def cmd_list(base: str, key: str, args: list):
    status, data = api_request(base, key, "GET", "/workflows")
    wfs = data.get("data", data) if isinstance(data, dict) else data
    summary = [{"id": w["id"], "name": w["name"], "active": w.get("active"),
                "updatedAt": w.get("updatedAt")} for w in wfs]
    print(json.dumps({"ok": True, "count": len(summary), "workflows": summary},
                     ensure_ascii=False, indent=2))


def cmd_inspect(base: str, key: str, args: list):
    if not args:
        die("Usage: inspect <workflow_id>")
    wf_id = args[0]
    status, data = api_request(base, key, "GET", f"/workflows/{wf_id}")
    data = strip_heavy(data)
    nodes = [{"name": n["name"], "type": n["type"],
              "params": n.get("parameters", {})} for n in data.get("nodes", [])]
    print(json.dumps({
        "ok": True, "id": data.get("id"), "name": data.get("name"),
        "active": data.get("active"), "nodes": nodes,
        "connections": list(data.get("connections", {}).keys())
    }, ensure_ascii=False, indent=2))


def cmd_get(base: str, key: str, args: list):
    if not args:
        die("Usage: get <workflow_id>")
    wf_id = args[0]
    status, data = api_request(base, key, "GET", f"/workflows/{wf_id}")
    data = strip_heavy(data)
    print(json.dumps({"ok": True, "workflow": data}, ensure_ascii=False, indent=2))


def cmd_update(base: str, key: str, args: list):
    if len(args) < 2:
        die("Usage: update <workflow_id> <json_file>")
    wf_id, json_path = args[0], args[1]
    if not os.path.isfile(json_path):
        die(f"Archivo no existe: {json_path}")
    with open(json_path, "r", encoding="utf-8") as f:
        wf_data = json.load(f)
    status, data = api_request(base, key, "PUT", f"/workflows/{wf_id}", wf_data)
    print(json.dumps({"ok": status == 200, "status": status,
                       "id": wf_id, "name": data.get("name", "?")},
                     ensure_ascii=False, indent=2))


def cmd_create(base: str, key: str, args: list):
    if not args:
        die("Usage: create <json_file>")
    json_path = args[0]
    if not os.path.isfile(json_path):
        die(f"Archivo no existe: {json_path}")
    with open(json_path, "r", encoding="utf-8") as f:
        wf_data = json.load(f)
    status, data = api_request(base, key, "POST", "/workflows", wf_data)
    print(json.dumps({"ok": status == 200, "status": status,
                       "id": data.get("id"), "name": data.get("name", "?")},
                     ensure_ascii=False, indent=2))


def cmd_delete(base: str, key: str, args: list):
    if not args:
        die("Usage: delete <workflow_id>")
    wf_id = args[0]
    status, data = api_request(base, key, "DELETE", f"/workflows/{wf_id}")
    print(json.dumps({"ok": status == 200, "status": status, "id": wf_id},
                     indent=2))


def cmd_activate(base: str, key: str, args: list):
    if not args:
        die("Usage: activate <workflow_id>")
    wf_id = args[0]
    status, data = api_request(base, key, "POST", f"/workflows/{wf_id}/activate")
    if status == 200:
        print(json.dumps({"ok": True, "status": status, "id": wf_id, "active": True}, indent=2))
    else:
        print(json.dumps({"ok": False, "status": status, "error": data}, indent=2))


def cmd_deactivate(base: str, key: str, args: list):
    if not args:
        die("Usage: deactivate <workflow_id>")
    wf_id = args[0]
    status, data = api_request(base, key, "POST", f"/workflows/{wf_id}/deactivate")
    if status == 200:
        print(json.dumps({"ok": True, "status": status, "id": wf_id, "active": False}, indent=2))
    else:
        print(json.dumps({"ok": False, "status": status, "error": data}, indent=2))


def cmd_execute(base: str, key: str, args: list):
    if not args:
        die("Usage: execute <workflow_id> [json_input]")
    wf_id = args[0]
    payload = {"workflowId": wf_id}
    if len(args) > 1:
        try:
            payload["triggerData"] = json.loads(args[1])
        except json.JSONDecodeError:
            die("El input debe ser un JSON string válido")
            
    status, data = api_request(base, key, "POST", "/executions", payload)
    print(json.dumps({"ok": 200 <= status < 300, "status": status, "result": data},
                     ensure_ascii=False, indent=2))


def cmd_executions(base: str, key: str, args: list):
    # Opcional: filtrar por workflow_id
    wf_id = args[0] if args else None
    path = f"/executions?workflowId={wf_id}&limit=5" if wf_id else "/executions?limit=5"
    
    status, data = api_request(base, key, "GET", path)
    execs = data.get("data", data) if isinstance(data, dict) else data
    summary = []
    if isinstance(execs, list):
        for e in execs:
            summary.append({
                "id": e.get("id"),
                "status": e.get("status"),
                "finished": e.get("finished"),
                "startedAt": e.get("startedAt"),
                "workflowId": e.get("workflowId")
            })
    print(json.dumps({"ok": True, "count": len(summary), "executions": summary},
                     ensure_ascii=False, indent=2))


COMMANDS = {
    "test": cmd_test, "test-connection": cmd_test,
    "list": cmd_list,
    "inspect": cmd_inspect,
    "get": cmd_get,
    "update": cmd_update,
    "create": cmd_create,
    "delete": cmd_delete,
    "activate": cmd_activate,
    "deactivate": cmd_deactivate,
    "execute": cmd_execute,
    "executions": cmd_executions,
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)

    command = sys.argv[1]
    args = sys.argv[2:]

    if command not in COMMANDS:
        die(f"Comando desconocido: {command}. Disponibles: {', '.join(COMMANDS.keys())}")

    api_key = load_api_key()
    container_ip = get_container_ip()
    base_url = f"http://{container_ip}:5678"

    COMMANDS[command](base_url, api_key, args)


if __name__ == "__main__":
    main()
