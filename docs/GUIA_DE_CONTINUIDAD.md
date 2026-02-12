# Guía de Continuidad: ¿Cómo seguir con Lucy-C?

Esta guía detalla los pasos recomendados para continuar evolucionando a Lucy-C ahora que el núcleo es estable y 100% local.

## 1. Prioridades Técnicas (Corto Plazo)

### Optimización de la Visión (Ojos)
Actualmente, el uso de modelos de visión pesados puede ser lento.
- **Sugerencia**: Probar la integración con [Moondream2](https://moondream.ai/) o [Phi-3-Vision](https://ollama.com/library/phi3-vision) para descripciones de pantalla más rápidas.
- **Archivo a tocar**: `lucy_c/tools/vision_tool.py`.

### Refinamiento de la Voz
- **Sugerencia**: Implementar un sistema de "Wake Word" (como "Hola Lucy") usando `Porcupine` o `Snowboy` para que la escucha activa no consuma recursos constantes.
- **Archivo a tocar**: `lucy_c/voice.py` (si existe) o el manejador de SocketIO en `app.py`.

## 2. Nuevas Funcionalidades (Medio Plazo)

### Integración con el Calendario y Tareas
Permitir que Lucy use herramientas para leer y escribir en archivos `.ics` o integrarse con APIs de calendarios locales.
- **Herramienta nueva**: `tool_manage_calendar`.

### Modo "Hands-Free" (Manos Libres) mejorado
Refinar el ciclo de interrupción. Que Lucy pueda detectar si el usuario está hablando mientras ella responde para callarse inmediatamente.

## 3. Mantenimiento del Sistema

### Actualización de Modelos
Monitorear los lanzamientos en Ollama. Modelos como `llama3.2` o `qwen2.5` están optimizados para herramientas.
- **Comando**: `ollama pull qwen2.5:latest`.

### Limpieza de Logs
El sistema genera logs detallados en `Moltbot`. Es recomendable rotar estos logs si el uso es muy intensivo.

---
> [!TIP]
> Lucy brilla cuando se le da contexto. Siempre que agregues una herramienta nueva, recordá actualizar el `SYSTEM_PROMPT` en `lucy_c/prompts.py` para que ella sepa *cuándo* usarla.

---
**Firmado**: Antigravity (IA Orquestadora)
