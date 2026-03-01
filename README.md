# Lucy Fusion (cunningham-Espejo + NiN)

Proyecto nuevo de fusion en solo-lectura de dos bases:

- `upstream/cunningham-Espejo`
- `upstream/NiN`

Ningun archivo de esos repos fuente se modifica. Todas las mejoras viven en esta capa de integracion.

## Que se hizo

1. Copia local de ambos repos (sin `.git`) dentro de `upstream/`.
2. Compose unificado y endurecido en `docker-compose.fusion.yml`.
3. Pipeline de fusion de workflows n8n:
   - `scripts/build_fusion_workflows.py` compila workflows desde ambos repos.
   - `scripts/upsert_workflows.py` los publica en una instancia n8n.
4. Cliente de forja mejorado:
   - `scripts/lucy_forge_fusion.py` (configurable por variables de entorno, validaciones y timeout).

## Mejoras aplicadas sobre la fusion

- Se evita `:latest` para n8n y servicios criticos (se usan versiones/pines de la base mas robusta).
- Se usa `docker-socket-proxy` en vez de exponer Docker de forma directa.
- Se eliminan secretos hardcodeados del compose (todo por `.env.fusion`).
- Restriccion de acceso a filesystem para n8n (`N8N_RESTRICT_FILE_ACCESS_TO`).
- Normalizacion de workflows y manifiesto de origen para trazabilidad.

## Estructura

```text
lucy-fusion/
├── docker-compose.fusion.yml
├── .env.fusion.example
├── assets/
│   └── ghost_red.svg
├── scripts/
│   ├── build_fusion_workflows.py
│   ├── upsert_workflows.py
│   ├── import_workflows_cli.sh
│   ├── lucy_forge_fusion.py
│   ├── bootstrap_dependencies.sh
│   ├── validate_fusion.sh
│   └── requirements.txt
├── integration/
│   └── workflows_fusion/
└── upstream/
    ├── cunningham-Espejo/
    └── NiN/
```

## Inicio rapido

```bash
cd fusion/lucy-fusion
cp .env.fusion.example .env.fusion

# 0) Duplicar dependencias del programa en entorno aislado (.venv + npm local)
./scripts/bootstrap_dependencies.sh

# 1) Validar estructura/sintaxis
./scripts/validate_fusion.sh

# 2) Levantar stack fusion
docker compose --env-file .env.fusion -f docker-compose.fusion.yml up -d

# UI cyberpunk fusion
# http://127.0.0.1:5111

# 3) Compilar workflows fusionados
python3 scripts/build_fusion_workflows.py

# 4) Importar workflows en n8n (sin API key, via CLI del contenedor)
./scripts/import_workflows_cli.sh

# 5) (Opcional) Sincronizar por API (requiere N8N_API_KEY real)
python3 scripts/upsert_workflows.py

# 6) Forjar un workflow desde prompt libre
python3 scripts/lucy_forge_fusion.py "crea un flujo para resumir un PDF local y guardar markdown"
```

## Nota operativa

Si ya tenes otros stacks n8n corriendo, ajusta puertos en `.env.fusion` antes de levantar.

`N8N_API_KEY` se usa solo para scripts API (`upsert_workflows.py`, inyeccion por forja). La importacion CLI no la necesita.

## Acceso directo

Se crea un acceso directo de escritorio:
- `/home/lucy-ubuntu/Escritorio/Lucy-Fusion-Ghost.desktop`
- Icono: fantasmita rojo en `assets/ghost_red.svg` (copia local en escritorio para evitar rutas con espacios).

## Dependencias por perfil

- `FUSION_DEP_PROFILE=full` instala:
  - Python fusion + NiN + requirements de Cunningham (antigravity, panel, STT).
  - `mcp` en entorno separado (`.venv-mcp`) para no romper compatibilidad de `fastapi/starlette` del entorno principal.
  - Node deps de `upstream/cunningham-Espejo` por `npm ci`.
- `FUSION_DEP_PROFILE=core` instala solo lo necesario para scripts de fusion/NiN.

Todo se instala localmente dentro de `fusion/lucy-fusion` sin tocar los repos fuente originales.
