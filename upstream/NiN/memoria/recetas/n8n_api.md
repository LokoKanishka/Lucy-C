# 🔧 Receta: Acceso a la API de n8n desde el sandbox

> **Problema**: Desde el sandbox de Antigravity no se puede acceder a `localhost:5678` (ni curl ni browser).
>
> **Solución**: Usar `docker exec n8n-lucy node -e '...'` para ejecutar requests HTTP desde dentro del container.

## Método: Node.js dentro del container

### GET — Listar workflows

```bash
docker exec n8n-lucy node -e '
const http = require("http");
const opts = {
  hostname: "localhost", port: 5678, path: "/api/v1/workflows", method: "GET",
  headers: {
    "Accept": "application/json",
    "X-N8N-API-KEY": process.env.N8N_API_KEY || "PONER_KEY_ACA"
  }
};
const req = http.request(opts, (res) => {
  let body = "";
  res.on("data", (c) => body += c);
  res.on("end", () => console.log(body));
});
req.on("error", (e) => console.error("ERROR: " + e.message));
req.end();
'
```

### POST — Crear workflow

```bash
docker exec n8n-lucy node -e '
const http = require("http");
const data = JSON.stringify({
  "name": "Mi Workflow",
  "nodes": [ /* ...nodos... */ ],
  "connections": { /* ...conexiones... */ },
  "settings": {}
});
const opts = {
  hostname: "localhost", port: 5678, path: "/api/v1/workflows", method: "POST",
  headers: {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "X-N8N-API-KEY": "PONER_KEY_ACA",
    "Content-Length": Buffer.byteLength(data)
  }
};
const req = http.request(opts, (res) => {
  let body = "";
  res.on("data", (c) => body += c);
  res.on("end", () => console.log("HTTP " + res.statusCode + ": " + body));
});
req.on("error", (e) => console.error("ERROR: " + e.message));
req.write(data);
req.end();
'
```

## Lo que NO funciona

| Método | Resultado |
|--------|-----------|
| `curl localhost:5678` desde sandbox | ❌ Timeout infinito |
| Browser Playwright del sandbox | ❌ No tiene sesión de login |
| `docker exec wget --post-data` | ❌ Se cuelga en POST (GET sí funciona) |

## API Key

Leer de `/home/lucy-ubuntu/Escritorio/NIN/.env` → variable `N8N_API_KEY`

## Endpoints útiles

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/v1/workflows` | GET | Listar todos los workflows |
| `/api/v1/workflows` | POST | Crear workflow nuevo |
| `/api/v1/workflows/{id}` | PUT | Actualizar workflow existente |
| `/api/v1/workflows/{id}` | DELETE | Eliminar workflow |
| `/api/v1/workflows/{id}/activate` | POST | Activar workflow |
