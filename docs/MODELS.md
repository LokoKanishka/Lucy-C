# Modelos Locales para Lucy-C

Lucy utiliza [Ollama](https://ollama.com/) para ejecutar modelos de lenguaje de forma local. Esta página documenta los modelos recomendados y cómo gestionarlos.

## Modelos Recomendados (Whitelist)

Lucy tiene una lista curada de modelos que han sido probados y validados para su identidad y tono:

| Modelo | Tamaño (aprox) | Fortalezas | Recomendado para... |
|--------|----------------|------------|---------------------|
| `llama3:8b` | 4.7 GB | General, Español | Diálogo diario y asistencia general. |
| `mistral:7b` | 4.1 GB | Instrucciones, Resumen | Tareas rápidas y procesamiento de texto. |
| `codellama:7b` | 3.8 GB | Programación, Debug | Asistencia técnica y código Python. |
| `phi3:mini` | 2.3 GB | Razonamiento, Ligero | PCs con pocos recursos (CPU/RAM). |
| `dolphin-llama3:8b` | 4.7 GB | Creatividad, Sin censura | Escritura creativa y respuestas directas. |
| `qwen2:7b` | 4.4 GB | Matemáticas, Lógica | Tareas técnicas complejas. |

## Cómo instalar nuevos modelos

Para que Lucy pueda usar un nuevo cerebro, debés instalarlo primero en tu instancia local de Ollama:

```bash
ollama pull llama3:8b
```

Una vez instalado, Lucy lo detectará automáticamente y aparecerá en el selector de "Brain" en la interfaz web.

## Configuración del Modelo Default

El modelo inicial de Lucy se define en el archivo `config/config.yaml`:

```yaml
ollama:
  host: "http://127.0.0.1:11434"
  model: "llama3:8b" # Cambiá esto por tu modelo preferido
```
