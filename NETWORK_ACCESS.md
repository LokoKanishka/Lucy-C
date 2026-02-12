# 🌐 Acceso por Red Local - Lucy-C

## ✅ Configuración Completa

Lucy-C ya está configurada para aceptar conexiones desde cualquier dispositivo en tu red local.

---

## 📡 Tu IP Local

**IP de este equipo**: `192.168.0.3`

---

## 🚀 Cómo Iniciar Lucy con Acceso de Red

### Opción 1: Script Recomendado (con todas las funciones)

```bash
cd /home/lucy-ubuntu/Lucy-C
export LUCY_TTS_PROVIDER=xtts
export LUCY_VIRTUAL_DISPLAY=1
source .venv/bin/activate
python3 lucy_c/web/app.py
```

### Opción 2: Script Rápido

```bash
cd /home/lucy-ubuntu/Lucy-C
./scripts/run_web_ui.sh
```

---

## 📱 Conectarse desde Otros Dispositivos

### Desde tu Celular/Tablet (mismo WiFi):

1. **Asegúrate de estar en la misma red WiFi** que este equipo
2. **Abre el navegador** (Chrome, Safari, Firefox)
3. **Ingresa a**: `http://192.168.0.3:5050`

### Desde otra computadora (misma red):

1. **Abre el navegador**
2. **Ingresa a**: `http://192.168.0.3:5050`

---

## 🔍 Verificación

Cuando Lucy esté corriendo, deberías ver en la terminal:

```
* Running on http://0.0.0.0:5050
* Running on http://192.168.0.3:5050
```

Esto confirma que está escuchando en todas las interfaces de red.

---

## 🛡️ Firewall (si no puedes conectar)

Si no puedes conectarte desde otro dispositivo, puede que necesites abrir el puerto en el firewall:

```bash
sudo ufw allow 5050/tcp
sudo ufw status
```

---

## 🎯 Conectividad Local vs Remota

- ✅ **Desde este equipo**: `http://localhost:5050` o `http://127.0.0.1:5050`
- ✅ **Desde la red local**: `http://192.168.0.3:5050`
- ❌ **Desde Internet**: No accesible (solo red local, más seguro)

---

## 💡 Tips

1. **Marca como favorito** en tu celular para acceso rápido
2. **Agrega a la pantalla de inicio** (funciona como una app)
3. **Usa auriculares** en el celular para mejor experiencia de voz
