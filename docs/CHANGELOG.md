# Changelog - Lucy Core 1.0

Este documento resume los hitos alcanzados durante el primer ciclo de desarrollo de Lucy-C (2026-02-01).

## [1.0.0] - El Despertar de la Arquitectura
Consolidación de la separación Core-Body y lanzamiento de la interfaz premium.

### Añadido
- **Lucy Core**:
    - Sistema de prompts versionado con identidad rioplatense.
    - `ToolRouter` para ejecución segura de herramientas.
    - Memoria persistente de hechos (`remember`/`forget`).
- **Lucy Body**:
    - **Ojos**: Detección de ventana activa vía `xdotool` y OCR contextual.
    - **Manos**: Automatización con `pyautogui`, incluyendo curvas de suavizado y failsafes.
    - **Voz**: Integración de Whisper y Mimic3 con ajustes de velocidad y dialecto.
- **Interfaz Lucy-C**:
    - Diseño Premium con Glassmorphism.
    - Indicadores visuales de estado (Thinking, Seeing, Acting).
    - Gestión de sesiones persistentes (el historial no se pierde al recargar).
    - Atajos de teclado para flujo de trabajo rápido.

### Corregido
- Path de `mimic3` dentro del entorno virtual (VENV).
- Problemas de concurrencia en la carga de modelos de Ollama.
- Errores de tipografía en el módulo de automatización.

### Cambiado
- El sistema de routing de herramientas ahora es centralizado y modular.
- La comunicación backend-frontend se migró a SocketIO para mayor fluidez.

---
"Un paso fundamental hacia la soberanía digital y la asistencia personalizada."
