import sys
import json
import urllib.request
import re

def get_video_id(url):
    pattern = r'(?:v=|\/)([0-9A-Za-z_-]{11}).*'
    match = re.search(pattern, url)
    return match.group(1) if match else None

def fetch_transcript(url):
    video_id = get_video_id(url)
    if not video_id:
        return "Error: URL de YouTube inválida."
    
    # Intento de fetch simple (metadatos) ya que las transcripciones requieren libs específicas
    # En un entorno real, aquí usaríamos youtube_transcript_api
    try:
        # Simulamos la extracción de info básica si no hay API de transcripción
        return f"Transcripción simulada para el video {video_id}. (Nota: Se recomienda instalar youtube_transcript_api en el host para resultados reales)."
    except Exception as e:
        return f"Error extrayendo transcripción: {str(e)}"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No se proporcionó URL"}))
        sys.exit(1)
    
    url = sys.argv[1]
    result = fetch_transcript(url)
    print(json.dumps({"url": url, "transcript": result}))
