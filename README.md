# Lucy-C + Lucy Fusion

This repository contains the upstream Lucy-C voice assistant stack plus a fusion layer used to integrate and operate workflows from two source projects in read-only mode:

- `sources/cunningham-Espejo`
- `sources/NiN`

No files in those source repositories are modified. Fusion changes live in `fusion/lucy-fusion`.

## Quick start (Lucy-C base)

```bash
git clone https://github.com/LokoKanishka/Lucy-C.git
cd Lucy-C
./scripts/install.sh
./scripts/run_web_ui.sh
```

Default UI endpoint: `http://127.0.0.1:5000`

## Quick start (Fusion stack)

```bash
cd fusion/lucy-fusion
cp .env.fusion.example .env.fusion

./scripts/bootstrap_dependencies.sh
./scripts/validate_fusion.sh

docker compose --env-file .env.fusion -f docker-compose.fusion.yml up -d

python3 scripts/build_fusion_workflows.py
./scripts/import_workflows_cli.sh
```

Fusion panel endpoint: `http://127.0.0.1:5111`

## Core requirements

- Linux (Ubuntu recommended)
- `ffmpeg`
- local `ollama` (default `http://127.0.0.1:11434`)
- `mimic3` CLI for TTS
- Docker + Docker Compose

## Notes

- `N8N_API_KEY` is only required for API sync scripts such as `scripts/upsert_workflows.py`.
- CLI import (`scripts/import_workflows_cli.sh`) does not require that key.
- Fusion assets and scripts are isolated under `fusion/lucy-fusion`.

## Git Sync And Troubleshooting

If you see `fatal: not a git repository`, you are outside the repo root.

Use this from the repository root:

```bash
git status
git branch --show-current
git fetch origin
git rebase origin/main
git push --force-with-lease
```

From any directory, use `git -C`:

```bash
git -C "/home/lucy-ubuntu/Escritorio/lucy c demon/fusion/lucy-fusion" status
git -C "/home/lucy-ubuntu/Escritorio/lucy c demon/fusion/lucy-fusion" fetch origin
git -C "/home/lucy-ubuntu/Escritorio/lucy c demon/fusion/lucy-fusion" rebase origin/main
```

Or use the helper script included in this repo:

```bash
./scripts/git_sync_main.sh
./scripts/git_sync_main.sh --force-with-lease
```

## Bitacora y memoria de personalidad

Se agrego una bitacora de proyecto y un agente CLI simple para guardar notas de personalidad/preferencias humanas:

- Bitacora: `docs/BITACORA_PROYECTO.md`
- Perfil del agente: `config/personality_agent.json`
- CLI: `scripts/personality_agent.py`

Ejemplos:

```bash
python3 scripts/personality_agent.py show
python3 scripts/personality_agent.py add-note --text "Mantener explicaciones cortas y claras."
python3 scripts/personality_agent.py add-preference --preference "Confirmar antes de force-push."
python3 scripts/personality_agent.py log --cambio "Ajuste de UI" --detalle "Refactor de layout panel NiN." --estado hecho
```
