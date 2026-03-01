---
description: Flujo de trabajo de prueba x1
---

# Prueba x1

Workflow de prueba para verificar que Antigravity puede crear y publicar workflows en n8n.

## Pasos

1. **Crear el JSON del workflow**
   ```bash
   # El archivo ya existe en: workflows/prueba_x1.json
   cat workflows/prueba_x1.json
   ```

2. **Publicar en n8n usando el script helper**
   ```bash
   bash scripts/n8n_publish.sh workflows/prueba_x1.json
   ```

3. **Verificar en la UI de n8n**
   - Abrir http://localhost:5678/home/workflows
   - El workflow "Prueba x1 - Test de Antigravity" debería aparecer en la lista

> [!NOTE]
> Este workflow usa `docker exec n8n-lucy node -e '...'` internamente porque el sandbox de Antigravity no tiene acceso directo a localhost:5678.
