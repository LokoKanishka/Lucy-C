#!/bin/bash
# Audio System Diagnostic - Level 1: Operating System

echo "=========================================="
echo "🔊 PRUEBA 1: Audio a Nivel Sistema (Linux)"
echo "=========================================="
echo ""

# Check if audio tools are installed
echo "📦 Verificando herramientas de audio..."
if ! command -v arecord &> /dev/null; then
    echo "❌ arecord no instalado"
    echo "💡 Instalá con: sudo apt install alsa-utils"
    exit 1
fi

if ! command -v aplay &> /dev/null; then
    echo "❌ aplay no instalado"
    echo "💡 Instalá con: sudo apt install alsa-utils"
    exit 1
fi

echo "✅ Herramientas de audio disponibles"
echo ""

# List audio devices
echo "🎤 Dispositivos de entrada disponibles:"
arecord -l
echo ""

echo "🔊 Dispositivos de salida disponibles:"
aplay -l
echo ""

# Test recording
echo "=========================================="
echo "🎤 PRUEBA DE MICRÓFONO"
echo "=========================================="
echo "📢 Preparate para hablar..."
echo "   Voy a grabar 3 segundos de audio."
echo "   Cuando empiece, decí algo claro y fuerte:"
echo ""
echo "   Ejemplo: 'Hola Lucy, ¿me escuchás?'"
echo ""
read -p "Presioná ENTER cuando estés listo..." 

echo "🔴 GRABANDO EN 3... 2... 1..."
arecord -d 3 -f cd -t wav /tmp/test_mic.wav 2>&1

if [ $? -eq 0 ]; then
    echo "✅ Grabación completada: /tmp/test_mic.wav"
else
    echo "❌ ERROR al grabar"
    exit 1
fi

echo ""
echo "=========================================="
echo "🔊 PRUEBA DE PARLANTES"
echo "=========================================="
echo "🎵 Reproduciendo lo que grabaste..."
echo "   (Deberías escuchar tu propia voz)"
echo ""

aplay /tmp/test_mic.wav 2>&1

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Reproducción completada"
    echo ""
    echo "=========================================="
    echo "📊 RESULTADO"
    echo "=========================================="
    echo ""
    read -p "❓ ¿Te escuchaste a vos mismo? (s/n): " respuesta
    
    if [[ "$respuesta" == "s" || "$respuesta" == "S" ]]; then
        echo ""
        echo "✅ ¡AUDIO DEL SISTEMA FUNCIONA!"
        echo ""
        echo "🎯 Linux está OK. El problema está en otro nivel:"
        echo "   → Probablemente Python o el navegador web"
        echo ""
        echo "📝 Próximo paso:"
        echo "   Ejecutá: python3 test_audio.py"
    else
        echo ""
        echo "❌ PROBLEMA DETECTADO A NIVEL SISTEMA"
        echo ""
        echo "💡 Soluciones:"
        echo "   1. Abrí: Settings > Sound"
        echo "   2. Verificá que el micrófono correcto esté seleccionado"
        echo "   3. Verificá que no esté muteado"
        echo "   4. Probá diferentes dispositivos de entrada/salida"
    fi
else
    echo "❌ ERROR al reproducir"
fi
