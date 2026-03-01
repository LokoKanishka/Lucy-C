import os
import json
import subprocess

REPO_DIR = "/home/lucy-ubuntu/Escritorio/NIN"
WORKFLOWS_DIR = os.path.join(REPO_DIR, "workflows")
CLI_SCRIPT = os.path.join(REPO_DIR, "scripts", "n8n_cli.py")

def get_cli_json(*args):
    result = subprocess.run(["python3", CLI_SCRIPT] + list(args), capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error ejecutando CLI: {result.stderr}")
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"Error parseando JSON: {result.stdout}")
        return None

def sync():
    if not os.path.exists(WORKFLOWS_DIR):
        os.makedirs(WORKFLOWS_DIR)

    print("Obteniendo lista de flujos de n8n...")
    res = get_cli_json("list")
    if not res or not res.get("ok"):
        print("Fallo al obtener los flujos.")
        return

    workflows = res.get("workflows", [])
    active_files = []

    for wf in workflows:
        wf_id = wf["id"]
        # Limpiar nombre para archivo seguro
        safe_name = "".join(c for c in wf["name"] if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_name = safe_name.replace(" ", "_").lower()
        file_name = f"{safe_name}_{wf_id}.json"
        active_files.append(file_name)

        print(f"Exportando: {wf['name']} ({wf_id})...")
        wf_res = get_cli_json("get", wf_id)
        if wf_res and wf_res.get("ok"):
            file_path = os.path.join(WORKFLOWS_DIR, file_name)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(wf_res.get("workflow", {}), f, indent=2, ensure_ascii=False)

    # Limpiar archivos de flujos que ya no existen en n8n
    for existing_file in os.listdir(WORKFLOWS_DIR):
        if existing_file.endswith(".json") and existing_file not in active_files:
            file_path = os.path.join(WORKFLOWS_DIR, existing_file)
            print(f"Borrando flujo antiguo/eliminado: {existing_file}")
            os.remove(file_path)

    print("¡Sincronización completa!")

if __name__ == "__main__":
    sync()
