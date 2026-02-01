# Lucy Core: El Alma y el Cerebro

El **Core** es el sistema nervioso central de Lucy. Su función es procesar el lenguaje, gestionar la memoria y decidir qué herramientas deben utilizarse para cumplir el objetivo del usuario.

## Componentes Principales

### 1. Moltbot (El Orquestador)
Ubicación: `lucy_c/pipeline.py`

Es la clase maestra que une todas las piezas. Sus responsabilidades incluyen:
- **Gestión de Sesión**: Carga y guarda el historial de chat.
- **Inferencia**: Se comunica con los LLM (Ollama o Clawdbot).
- **Loop de Herramientas**: Busca llamadas del tipo `[[tool(args)]]` en la respuesta del modelo y las ejecuta.
- **Reflexión**: Después de usar una herramienta, el Core re-evalúa la situación para dar una respuesta coherente.

### 2. ToolRouter (Capa de Seguridad)
Ubicación: `lucy_c/tool_router.py`

Actúa como una aduana entre los pensamientos de Lucy y sus acciones físicas.
- **Validación de Argumentos**: Asegura que los parámetros enviados por el LLM sean seguros.
- **Prevención de Inyección**: Bloquea caracteres peligrosos (`;`, `&`, `|`) para evitar ejecución de comandos no deseados.
- **Routing**: Dirige la petición al módulo correcto (Memory, Eyes, Hands).

### 3. Memoria (Fact & History)
Ubicación: `lucy_c/facts_store.py` y `lucy_c/history_store.py`

Lucy tiene dos tipos de memoria:
- **Historial**: Una cola persistente de las últimas conversaciones para mantener el contexto.
- **Hechos (Facts)**: Memoria a largo plazo donde guarda datos clave del usuario (ej: "Mi nombre es Diego", "Mi color favorito es el azul"). Se activa mediante herramientas `remember` y `forget`.

## Identidad y Prompting (Prompt v1.0.0)

Lucy no es un simple bot de texto; tiene una identidad porteña definida:
- **Identidad**: Asistente virtual inteligente, analítica pero cercana.
- **Idioma**: Español con deísmo y modismos típicos de Argentina (Voseo: "viste", "tenés", "contame").
- **Política de Honestidad**: Si no sabe algo o no tiene los sensores para verlo, lo admite con franqueza.
- **Soberanía**: Prioriza el procesamiento local (Ollama) siempre que sea posible.

## Configuración Cognitiva
El comportamiento del Core se ajusta en `config/config.yaml`:
- `safe_mode`: Si es `true`, bloquea acciones potencialmente destructivas.
- `llm.provider`: Define quién provee el cerebro (local vs nube).
