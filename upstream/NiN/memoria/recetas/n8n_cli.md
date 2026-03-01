# Cliente n8n (n8n_cli.py)

**Problema:**
Desde el sandbox de Antigravity no hay acceso directo a la red del host (`localhost:5678`). Usar `docker exec n8n-lucy node -e '...'` funciona para scripts rápidos, pero cuando se encolan muchas peticiones o hay errores, se generan procesos "zombies" que saturan Docker y lo bloquean por completo.

**Solución:**
Un cliente Python puro (`scripts/n8n_cli.py`) que obtiene la IP interna del container en la red bridge de Docker (`172.29.0.4`) y se comunica mediante HTTP directo, evitando `docker exec`.

## Características Clave

1. **Conexión Directa:** Usa la IP de la red de Docker para saltarse el forwarding de puertos y el overhead de `docker exec`.
2. **Caching de IP:** La IP se guarda en `.n8n_ip` para no tener que ejecutar `docker inspect` en cada llamada (lo que también puede ser lento si Docker está sobrecargado).
3. **Strip Heavy:** La API de n8n devuelve muchísima data inútil (como todas las versiones anteriores de un workflow). El CLI intercepta la respuesta y descarta los campos pesados (`activeVersion`, `shared`, etc.) para serializar la respuesta al stdout 100x más rápido.
4. **Timeouts:** Todas las operaciones tienen un timeout estricto de 15 segundos para evitar cuelgues.

## Uso

El script se ejecuta desde la raíz del repositorio:

```bash
# Verificar conectividad
python3 scripts/n8n_cli.py test

# Listar todos los workflows (rápido)
python3 scripts/n8n_cli.py list

# Ver estructura de un workflow (nodos y conexiones)
python3 scripts/n8n_cli.py inspect <id>

# Ver JSON completo
python3 scripts/n8n_cli.py get <id>

# Crear un workflow desde un archivo JSON
python3 scripts/n8n_cli.py create ruta/al/archivo.json

# Actualizar un workflow existente desde un JSON
python3 scripts/n8n_cli.py update <id> ruta/al/archivo.json

# Activar / Desactivar
python3 scripts/n8n_cli.py activate <id>
python3 scripts/n8n_cli.py deactivate <id>

# Ejecutar un workflow (solo workflows que inician con webhook o manual trigger)
python3 scripts/n8n_cli.py execute <id> '{"input": "data"}'

# Ver últimas ejecuciones
python3 scripts/n8n_cli.py executions [id]
```

## Limitaciones Conocidas

- No se puede usar el comando `execute` en workflows cuyo nodo inicial sea `When Executed by Another Workflow`. La API de n8n bloquea esto con un error `405 Method Not Allowed`. Estos workflows solo pueden ser invocados por un workflow padre (ej: el AI Agent principal).
- Los comandos `get` e `inspect` sobre workflows muy masivos pueden tardar varios segundos porque el cuello de botella es la base de datos interna de n8n empaquetando el JSON.
