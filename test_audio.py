#!/usr/bin/env python3
"""
Audio System Diagnostic Test for Lucy-C
Tests both microphone (input) and speaker (output) at Python library level
"""

import sys
import os

print("="*60)
print("🔊 DIAGNÓSTICO DE AUDIO - LUCY-C")
print("="*60)
print()

# Check 1: Can we import the libraries?
print("📦 Verificando librerías de audio...")
try:
    import speech_recognition as sr
    print("  ✅ speech_recognition instalado")
except ImportError:
    print("  ❌ speech_recognition NO instalado")
    print("     Instalá con: pip install SpeechRecognition")
    sys.exit(1)

try:
    from gtts import gTTS
    print("  ✅ gTTS instalado")
except ImportError:
    print("  ❌ gTTS NO instalado")
    print("     Instalá con: pip install gTTS")
    sys.exit(1)

print()

# Check 2: Can we access microphone?
print("🎤 Probando MICRÓFONO (Input)...")
print("   📢 HABLÁ AHORA - Di algo por 5 segundos...")
print()

r = sr.Recognizer()
try:
    with sr.Microphone() as source:
        print("   ⏳ Ajustando ruido ambiental...")
        r.adjust_for_ambient_noise(source, duration=1)
        print("   🔴 GRABANDO (5 segundos)...")
        audio = r.listen(source, timeout=5, phrase_time_limit=5)
        print("   ⏳ Procesando con Google Speech Recognition...")
        
        texto = r.recognize_google(audio, language="es-ES")
        print()
        print(f"   ✅ ¡MICRÓFONO FUNCIONA!")
        print(f"   📝 Te escuché decir: '{texto}'")
        print()
        
        # Check 3: Can we generate speech?
        print("🔊 Probando PARLANTES (Output)...")
        print("   ⏳ Generando respuesta en español...")
        
        tts = gTTS(text=f"Te escuché decir: {texto}", lang='es')
        output_file = "/tmp/lucy_audio_test.mp3"
        tts.save(output_file)
        print(f"   ✅ Audio generado: {output_file}")
        
        # Try to play
        print("   🔊 Reproduciendo audio...")
        print("      (Si no escuchás nada, probá: aplay o mpg123)")
        
        # Try different players
        players = [
            ("ffplay", "ffplay -nodisp -autoexit"),
            ("mpg123", "mpg123"),
            ("cvlc", "cvlc --play-and-exit"),
            ("aplay", "aplay")  # For wav files
        ]
        
        played = False
        for player_name, player_cmd in players:
            if os.system(f"which {player_name} > /dev/null 2>&1") == 0:
                print(f"   🎵 Usando {player_name}...")
                result = os.system(f"{player_cmd} {output_file} 2>/dev/null")
                if result == 0:
                    played = True
                    print(f"   ✅ Reproducción exitosa con {player_name}")
                    break
        
        if not played:
            print(f"   ⚠️  No se pudo reproducir automáticamente")
            print(f"   💡 Ejecutá manualmente: mpg123 {output_file}")
        
        print()
        print("="*60)
        print("✅ DIAGNÓSTICO COMPLETO")
        print("="*60)
        print("📊 Resultados:")
        print("   ✅ Micrófono: FUNCIONA")
        print("   ✅ Reconocimiento de voz: FUNCIONA") 
        print("   ✅ Generación de voz: FUNCIONA")
        if played:
            print("   ✅ Parlantes: FUNCIONAN")
        else:
            print("   ⚠️  Parlantes: No se pudo verificar automáticamente")
        print()
        print("🎯 CONCLUSIÓN: El problema NO es Python ni las librerías.")
        print("   El problema probablemente está en:")
        print("   - La interfaz web (permisos de micrófono)")
        print("   - El navegador (bloqueo de audio automático)")
        print("   - La comunicación WebSocket entre frontend y backend")
        
except sr.WaitTimeoutError:
    print()
    print("   ⏱️  TIMEOUT - No detecté audio en 5 segundos")
    print("   ❌ Posibles problemas:")
    print("      • Micrófono muteado en sistema")
    print("      • Micrófono incorrecto seleccionado")
    print("      • No hay permiso para acceder al mic")
    print()
    print("   💡 Probá:")
    print("      1. Ejecutá: arecord -d 3 test.wav")
    print("      2. Verificá Settings > Sound > Input")
    
except sr.UnknownValueError:
    print()
    print("   ⚠️  Google Speech Recognition no entendió el audio")
    print("   ✅ Pero el MICRÓFONO SÍ FUNCIONA (grabó algo)")
    print("   💡 Probá hablar más claro o más fuerte")
    
except sr.RequestError as e:
    print()
    print(f"   ❌ Error conectando a Google Speech Recognition: {e}")
    print("   💡 Verificá tu conexión a internet")
    
except Exception as e:
    print()
    print(f"   ❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
