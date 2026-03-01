#!/usr/bin/env python3
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS_DIR = ROOT / "integration" / "workflows_fusion"


def load_env_file(path: Path):
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def die(message: str, code: int = 1):
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(code)


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
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {url} -> HTTP {exc.code}: {raw}") from None


def load_workflows() -> list[dict]:
    if not WORKFLOWS_DIR.exists():
        die(f"No existe {WORKFLOWS_DIR}. Ejecuta primero build_fusion_workflows.py")

    files = [
        path
        for path in sorted(WORKFLOWS_DIR.glob("*.json"))
        if path.name != "manifest.json"
    ]
    if not files:
        die("No hay workflows fusionados para publicar.")

    workflows = []
    for path in files:
        raw = json.loads(path.read_text(encoding="utf-8"))
        workflows.append(
            {
                "path": path,
                "body": {
                    "name": raw.get("name", path.stem),
                    "nodes": raw.get("nodes", []),
                    "connections": raw.get("connections", {}),
                    "settings": raw.get("settings", {}),
                },
            }
        )
    return workflows


def main() -> int:
    load_env_file(ROOT / ".env.fusion")
    load_env_file(ROOT / ".env.fusion.example")

    base = os.environ.get("N8N_URL", "http://127.0.0.1:5690").rstrip("/")
    api_key = os.environ.get("N8N_API_KEY", "").strip()
    api_ver = os.environ.get("N8N_API_VERSION", "1")

    if not api_key or api_key == "REPLACE_WITH_N8N_UI_API_KEY":
        die(
            "N8N_API_KEY no configurada. Crea una API key en n8n UI "
            "(Settings -> n8n API) y guardala en .env.fusion."
        )

    workflows = load_workflows()

    list_url = f"{base}/api/v{api_ver}/workflows"
    _, payload = http_json("GET", list_url, api_key)
    existing_list = payload.get("data", payload) if isinstance(payload, dict) else payload
    if not isinstance(existing_list, list):
        die("Respuesta inesperada listando workflows.")

    existing_by_name = {}
    for wf in existing_list:
        if isinstance(wf, dict) and wf.get("name"):
            existing_by_name[wf["name"]] = str(wf.get("id"))

    created = 0
    updated = 0

    for item in workflows:
        wf = item["body"]
        name = wf["name"]
        wf_id = existing_by_name.get(name)

        if wf_id:
            url = f"{base}/api/v{api_ver}/workflows/{wf_id}"
            http_json("PUT", url, api_key, wf)
            updated += 1
            print(f"UPDATED  {name} ({wf_id})")
        else:
            url = f"{base}/api/v{api_ver}/workflows"
            _, created_payload = http_json("POST", url, api_key, wf)
            new_id = created_payload.get("id") if isinstance(created_payload, dict) else "?"
            created += 1
            print(f"CREATED  {name} ({new_id})")

    print(f"\nResumen: created={created} updated={updated} total={len(workflows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
