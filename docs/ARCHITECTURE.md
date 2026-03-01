## Arquitectura de Lucy-C: Core vs Body

Para garantizar que Lucy sea un sistema robusto y no solo una colección de scripts, dividimos el proyecto en dos capas conceptuales y técnicas claras, conectadas por un sistema de routing seguro.

## 1. Lucy Core (El Alma y el Cerebro)
El **Core** es la esencia de Lucy. Debe poder funcionar de forma independiente, sin interfaz gráfica ni sensores físicos.

- **Moltbot (Orquestador)**: El motor lógico que procesa el flujo de pensamiento.
- **Brain (LLM)**: El modelo local que provee la inteligencia.
- **Memory (History & Facts)**: El sistema de persistencia y contexto.
- **Identity Policy**: El sistema de prompts v1.0.0.

## 2. Lucy Body (Los Sentidos y la Acción)
El **Body** son las extensiones que permiten a Lucy interactuar con el mundo exterior.

- **Lucy-C (Premium UI)**: Interfaz glassmorphism con indicadores visuales de estado.
- **Eyes (Vision)**: Captura contextual y OCR de ventana activa.
- **Hands (Automation)**: Control de periféricos con movimientos naturales.
- **Voice (ASR/TTS)**: Procesamiento de audio con sesgo lingüístico local.

## El Puente: ToolRouter
Ubicación: `lucy_c/tool_router.py`

La comunicación entre Core y Body se realiza mediante `ToolRouter`. Este componente garantiza que:
1. Las llamadas a herramientas sean validadas por seguridad.
2. Los argumentos estén bien formados.
3. El Core reciba un feedback estructurado del éxito o fallo de la acción.

> "Lucy sigue siendo Lucy aunque esté ciega o en silencio, pero con el Body su potencial es ilimitado."

---

## Documentación Detallada
- [Manual del Core](file:///home/lucy-ubuntu/Lucy-C/docs/CORE.md)
- [Manual del Body](file:///home/lucy-ubuntu/Lucy-C/docs/BODY.md)
- [Gestión de Modelos](file:///home/lucy-ubuntu/Lucy-C/docs/MODELS.md)
