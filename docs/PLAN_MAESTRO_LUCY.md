# PLAN MAESTRO DEL PROYECTO LUCY

**Lucy = Moltbot + Cerebro Local + Cuerpo (UI, ojos, manos, voz)**

## PRINCIPIO FUNDAMENTAL (no negociable)

Lucy funciona **exclusivamente con modelos locales**.
No hay LLM cloud.
No hay dependencia externa para pensar.

---

## FASE 0 — DEFINICIÓN DEL NÚCLEO (acordada)

Antes de escribir más código, fijamos esto:

* **Moltbot** = arquitecto / orquestador
* **Cerebro** = modelo LLM local vía Ollama
* **Lucy** = identidad persistente que sobrevive al cambio de modelo

El modelo **no define a Lucy**.
Lucy **usa** modelos.

---

## FASE 1 — MOLTBOT + CEREBRO LOCAL (mínimo vital funcional)

### Objetivo

Tener a Moltbot funcionando **solo con Ollama**, usando **un modelo local fijo** (ej: `gpt-oss:20b`).

### Alcance

* Moltbot enruta prompts
* Un único provider local (Ollama)
* Un único modelo activo
* Sin UI compleja
* Sin ojos, manos ni voz

### Criterio de éxito

* Moltbot responde consistentemente usando el modelo local
* Logs claros de:

  * prompt
  * modelo usado
  * respuesta
* El sistema funciona **offline**

---

## FASE 2 — INTERCAMBIO DE CEREBRO (modelos locales múltiples)

### Objetivo

Poder **cambiar el modelo local sin romper a Lucy**.

Ejemplos:

* `gpt-oss:20b`
* `qwen2.5:14b`
* `mistral:7b`
* `tinyllama`
* etc.

### Qué se habilita

* Selector de modelo **local**
* Default estable
* Cambio:

  * por sesión
  * o por tarea (más adelante)

### Qué NO se hace todavía

* No auto-routing por modelo
* No benchmarking automático
* No mezcla de modelos

### Criterio de éxito

* Cambio de modelo sin reiniciar el sistema
* Lucy mantiene identidad, memoria y estilo
* El modelo es **intercambiable**, no estructural

---

## FASE 3 — INTEGRACIÓN CON INTERFAZ (Lucy-C)

### Objetivo

Dar cuerpo visual mínimo a Lucy sin alterar el núcleo.

### Rol de Lucy-C

* UI local
* Entrada/salida de texto
* Selector de **modelo local**
* Logs visibles

Lucy-C **no decide**:

* qué modelo existe
* qué herramientas se usan
  Eso lo decide Moltbot.

### Criterio de éxito

* Lucy-C muestra y usa modelos locales detectados
* No aparecen opciones cloud
* UI desacoplada del cerebro

---

## FASE 4 — CUERPO SENSORIOMOTOR (ojos, manos, voz)

Esta fase se hace **después** de que Lucy piense bien.

### 4.1 OJOS

* Screenshot
* OCR
* Lectura de pantalla
* Estado del escritorio

### 4.2 MANOS

* X11 / Wayland automation
* Teclado
* Mouse
* Ventanas
* Archivos
* VS Code

### 4.3 VOZ

* ASR local (Whisper u otro)
* TTS local
* Wake word (opcional)

### Regla

Los sentidos **no piensan**.
El cerebro decide qué hacer con lo que perciben.

---

## ARQUITECTURA FINAL (resumen)

```
[ Usuario ]
    ↓
[ Lucy-C (UI / Voz) ]
    ↓
[ Moltbot (arquitecto) ]
    ↓
[ Cerebro Local (Ollama / LLM) ]
    ↓
[ Herramientas / Ojos / Manos ]
```

---

## IDEA RECTORA (para no perdernos)

> **Lucy no es un modelo.
> Lucy no es una UI.
> Lucy es una identidad técnica que usa modelos locales para pensar y herramientas locales para actuar.**
