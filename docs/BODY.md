# Lucy Body: Sentidos y Acción

El **Body** representa la interfaz física y digital de Lucy. Son módulos que extienden su capacidad intelectual permitiéndole interactuar con tu entorno informático.

## Sensores (Entrada)

### 👁️ OJOS (Visión)
Ubicación: `lucy_c/tools/vision_tool.py`

Permite a Lucy capturar y "entender" lo que pasa en tu pantalla.
- **Detección de Ventana**: Usa `xdotool` para saber qué aplicación estás usando en este momento.
- **Grounding Visual**: Cuando le pedís que describa la pantalla, Lucy enfoca su "atención" en la ventana activa para dar respuestas más precisas.
- **OCR**: Capacidad de extraer texto de capturas de pantalla para leer documentos o interfaces.

### 🎤 VOZ (Audio Input)
Ubicación: `lucy_c/asr.py`

El oído de Lucy está optimizado para la región rioplatense.
- **Motor**: Usa Whisper (vía `faster-whisper`).
- **Dialecto**: Configuramos un `initial_prompt` con giros idiomáticos locales para que Lucy entienda mejor el "che", el "viste" y el voseo.

## Actuadores (Salida)

### 🖐️ MANOS (Automatización)
Ubicación: `lucy_c/tools/automation_tool.py`

Lucy puede operar tu computadora simulando interacciones humanas.
- **Movimiento Natural**: No se teletransporta; el mouse se mueve con curvas de suavizado (`easing`) para evitar ser detectado como un bot simple por algunas aplicaciones.
- **Teclado**: Capacidad de escribir texto, usar atajos (Hotkeys) y presionar teclas especiales.
- **Seguridad (Failsafe)**: Si movés el mouse bruscamente a una esquina de la pantalla, las acciones de Lucy se detienen inmediatamente.

### 🗣️ HABLA (TTS)
Ubicación: `lucy_c/mimic3_tts.py`

La voz de Lucy es generada localmente.
- **Motor**: Mimic3.
- **Personalidad**: Ajustamos el `length_scale` (velocidad) para que su voz suene natural, cálida y pausada, acorde a su identidad analítica.

## Conectividad (Lucy-C UI)

El Body se materializa en la interfaz web, que actúa como el puente visual:
- **SocketIO**: Comunicación bidireccional en tiempo real para voz y estados.
- **Visual Badges**: Cada vez que Lucy usa un sentido (Ojos) o un actuador (Manos), la UI lo muestra con una tarjeta descriptiva para que sepas qué está haciendo.
