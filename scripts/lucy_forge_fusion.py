#!/usr/bin/env python3
import argparse
import json
import os
import re
import sys
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parent.parent


def load_env_file(path: Path):
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def extract_json_blob(text: str) -> str:
    cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    fenced = re.search(r"```(?:json)?(.*?)```", cleaned, flags=re.DOTALL)
    if fenced:
        cleaned = fenced.group(1)

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return cleaned
    return cleaned[start : end + 1]


def load_system_prompt(prompt_path: Path) -> str:
    if prompt_path.exists():
        return prompt_path.read_text(encoding="utf-8").strip()
    return (
        "Eres el Arquitecto del Proyecto LUCY. "
        "Responde unicamente JSON valido con name, nodes y connections."
    )


def forge_workflow(
    prompt: str,
    ollama_url: str,
    model: str,
    system_prompt: str,
    retries: int = 3,
) -> dict:
    current_prompt = prompt
    for attempt in range(1, retries + 1):
        print(f"[FORGE] intento {attempt}/{retries}")
        response = requests.post(
            ollama_url,
            json={
                "model": model,
                "stream": False,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": current_prompt},
                ],
            },
            timeout=60,
        )
        response.raise_for_status()
        raw = response.json().get("message", {}).get("content", "")

        maybe_json = extract_json_blob(raw)
        try:
            data = json.loads(maybe_json)
            if "settings" not in data or not isinstance(data.get("settings"), dict):
                data["settings"] = {"executionOrder": "v1"}
            return data
        except json.JSONDecodeError as exc:
            current_prompt = (
                "Tu salida anterior no era parseable. "
                f"Error: {exc}. Devuelve solo JSON valido."
            )
    raise RuntimeError("No se pudo forjar un JSON valido tras varios intentos.")


def inject_workflow(n8n_base_url: str, api_key: str, workflow: dict):
    headers = {
        "X-N8N-API-KEY": api_key,
        "Content-Type": "application/json",
    }
    url = n8n_base_url.rstrip("/") + "/api/v1/workflows"
    response = requests.post(url, headers=headers, json=workflow, timeout=30)
    if response.status_code != 200:
        raise RuntimeError(f"Inyeccion fallida [{response.status_code}]: {response.text}")
    payload = response.json()
    print(f"[OK] workflow creado id={payload.get('id', 'unknown')}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Forja e inyeccion fusionada de workflows.")
    parser.add_argument("prompt", help="Instruccion natural para forjar workflow.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Solo imprime el JSON forjado, sin inyectar.",
    )
    parser.add_argument(
        "--out",
        default=str(ROOT / "integration" / "workflows_fusion" / "forged_latest.json"),
        help="Archivo de salida del workflow forjado.",
    )
    return parser.parse_args()


def main() -> int:
    load_env_file(ROOT / ".env.fusion")
    load_env_file(ROOT / ".env.fusion.example")

    args = parse_args()

    ollama_url = os.environ.get("LUCY_OLLAMA_URL", "http://127.0.0.1:11434/api/chat")
    model = os.environ.get("LUCY_MODEL", "huihui_ai/qwq-abliterated:32b-Q6_K")
    prompt_file = Path(
        os.environ.get(
            "LUCY_ARCHITECT_PROMPT",
            str(ROOT / "upstream" / "NiN" / "prompts" / "architect_v2_prompt.md"),
        )
    )
    n8n_url = os.environ.get("N8N_URL", "http://127.0.0.1:5690")
    api_key = os.environ.get("N8N_API_KEY", "").strip()

    system_prompt = load_system_prompt(prompt_file)
    workflow = forge_workflow(args.prompt, ollama_url, model, system_prompt)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(workflow, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[FORGE] workflow guardado en {out_path}")

    if args.dry_run:
        return 0

    if not api_key:
        print("ERROR: falta N8N_API_KEY para inyectar en n8n.", file=sys.stderr)
        return 1

    inject_workflow(n8n_url, api_key, workflow)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
