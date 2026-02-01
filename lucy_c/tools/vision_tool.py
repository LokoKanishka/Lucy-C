import os
import base64
import logging
from io import BytesIO
import pyautogui
from PIL import Image

class SystemEyes:
    def __init__(self, ollama_client):
        self.ollama = ollama_client
        self.log = logging.getLogger("SystemEyes")
        # Vision-capable model to use for descriptions
        self.vision_model = "llama3.2-vision" # Or llava:latest, qwen2.5vl:7b

    def capture_screenshot(self) -> str:
        """Capture screenshot and return as base64 string."""
        try:
            screenshot = pyautogui.screenshot()
            buffered = BytesIO()
            screenshot.save(buffered, format="PNG")
            return base64.b64encode(buffered.getvalue()).decode('utf-8')
        except Exception as e:
            self.log.error("Failed to capture screenshot: %s", e)
            return ""

    def get_active_window(self) -> str:
        """Get the title of the currently active window using xdotool."""
        try:
            import subprocess
            res = subprocess.run(["xdotool", "getactivewindow", "getwindowname"], 
                               capture_output=True, text=True, check=False)
            if res.returncode == 0:
                return res.stdout.strip()
        except Exception as e:
            self.log.debug("Failed to get active window: %s", e)
        return "Desconocida"

    def describe_screen(self, mode: str = "general") -> str:
        """Capture screen and get a description from the local vision model."""
        self.log.info("Capturing screen for analysis (mode: %s)...", mode)
        img_b64 = self.capture_screenshot()
        if not img_b64:
            return "Error: No pude capturar la pantalla."

        active_window = self.get_active_window()
        
        if mode == "ocr":
            prompt = f"La ventana activa es '{active_window}'. Extraé todo el texto legible de esta imagen de forma estructurada."
        else:
            prompt = f"La ventana activa es '{active_window}'. Describí qué hay en esta pantalla de forma concisa pero completa, mencionando elementos principales."
        
        try:
            url = f"{self.ollama.cfg.host.rstrip('/')}/api/generate"
            import httpx
            payload = {
                "model": self.vision_model,
                "prompt": prompt,
                "images": [img_b64],
                "stream": False
            }
            with httpx.Client(timeout=120.0) as client:
                r = client.post(url, json=payload)
                r.raise_for_status()
                data = r.json()
                description = data.get("response", "").strip()
                self.log.info("Screen description received: %s", description[:100] + "...")
                return description
        except Exception as e:
            self.log.warning("Vision model failed or not found: %s. Falling back to simple context.", e)
            return f"No tengo un modelo de visión activo ahora, pero veo que tenés abierta la ventana '{active_window}'."
