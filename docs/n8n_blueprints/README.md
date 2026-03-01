# n8n Blueprints para Lucy-C

Este directorio contiene workflows de n8n listos para importar que extienden las capacidades de Lucy-C.

## 📋 Workflows Disponibles

### 1. SOTA Brain (`sota_brain_workflow.json`)

**Propósito**: Permite a Lucy delegar preguntas complejas a modelos SOTA en la nube (Gemini 2.0, GPT-4, Claude).

**Importación**:
1. Abrí tu instancia de n8n en el navegador
2. Abrí el archivo `sota_brain_workflow.json`
3. Seleccioná todo el contenido (Ctrl+A) y copialo (Ctrl+C)
4. En n8n, hacé click en cualquier parte del canvas y pegá (Ctrl+V)
5. Los nodos aparecerán automáticamente

**Configuración Inicial**:
1. **Credenciales de API**:
   - Click en el nodo "OpenRouter (SOTA Model)"
   - Configurá tus credenciales de OpenRouter (o el proveedor que elijas)
   - Para OpenRouter:
     * Creá una cuenta en [openrouter.ai](https://openrouter.ai/)
     * Generá una API Key
     * En n8n: Credentials → New → HTTP Header Auth
     * Name: `Authorization`
     * Value: `Bearer TU_API_KEY_AQUI`

2. **Modelo** (Opcional):
   - El blueprint usa `google/gemini-2.0-flash-001` por defecto
   - Podés cambiarlo a:
     * `anthropic/claude-3.5-sonnet` (más potente)
     * `openai/gpt-4-turbo` (OpenAI)
     * `google/gemini-pro-1.5` (contexto masivo)

3. **Activar el Workflow**:
   - Toggle "Active" en la esquina superior derecha
   - Verificá que el webhook esté escuchando en `/webhook/lucy-ask-sota`

**Cómo Usarlo**:

Una vez activado, simplemente decile a Lucy:
- *"Lucy, explicame la teoría de cuerdas en detalle"*
- *"Necesito un análisis profundo sobre el impacto de la IA en 2025"*
- *"Escribime un poema épico sobre la física cuántica"*

Lucy detectará automáticamente que necesita capacidades SOTA y delegará la pregunta al workflow.

---

## 🔧 Alternativas a OpenRouter

Si preferís otro proveedor, modificá el nodo HTTP Request:

### Google AI Studio (Gratis)
```
URL: https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent
Header: x-goog-api-key: TU_API_KEY
Body: { "contents": [{"parts": [{"text": "{{ $json.body.prompt }}"}]}] }
```

### OpenAI Direct
```
URL: https://api.openai.com/v1/chat/completions
Header: Authorization: Bearer TU_API_KEY
Body: Ya está configurado (solo cambiá el model a "gpt-4-turbo")
```

### Anthropic Claude
```
URL: https://api.anthropic.com/v1/messages
Header: x-api-key: TU_API_KEY, anthropic-version: 2023-06-01
Body: { "model": "claude-3-opus-20240229", "messages": [...] }
```

---

## 🚀 Próximos Blueprints

- **lucy_document_analysis.json**: OCR y análisis de PDFs
- **lucy_email_workflows.json**: Envío automatizado de emails
- **lucy_data_pipeline.json**: ETL y transformación de datos

---

**Nota**: Estos workflows requieren que Lucy-C esté corriendo con la configuración de n8n activa en `config/config.yaml`.
