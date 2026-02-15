import os
import base64
import logging
import time
from io import BytesIO
# import pyautogui  # REMOVED TO PREVENT CRASHES
from PIL import Image

class SystemEyes:
    def __init__(self, ollama_client):
        self.ollama = ollama_client
        self.log = logging.getLogger("SystemEyes")
        # Vision-capable model to use for descriptions
        self.vision_model = "llama3.2-vision" # Or llava:latest, qwen2.5vl:7b

    def capture_screenshot(self) -> str:
        """Capture screenshot using scrot and return as base64 string."""
        import subprocess
        import tempfile
        import os
        
        tmp_file = os.path.join(tempfile.gettempdir(), f"lucy_screen_{int(time.time())}.png")
        try:
            # Ensure DISPLAY is set
            env = os.environ.copy()
            if "DISPLAY" not in env:
                env["DISPLAY"] = ":0"
                
            # Use scrot - simpler and more reliable on Linux/Ubuntu
            self.log.info("Capturing screenshot with scrot to %s...", tmp_file)
            res = subprocess.run(["scrot", "-z", tmp_file], env=env, capture_output=True, timeout=5)
            
            if res.returncode != 0:
                self.log.error("Scrot failed: %s", res.stderr.decode())
                return ""
                
            with open(tmp_file, "rb") as f:
                data = f.read()
                return base64.b64encode(data).decode('utf-8')
        except Exception as e:
            self.log.error("Failed to capture screenshot: %s", e)
            return ""
        finally:
            if os.path.exists(tmp_file):
                try:
                    os.remove(tmp_file)
                except:
                    pass

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
        try:
            img_b64 = self.capture_screenshot()
        except Exception as e:
            self.log.error("CRITICAL: capture_screenshot failed: %s", e)
            return "Error capturando pantalla."
            
        if not img_b64:
            self.log.warning("capture_screenshot returned empty string.")
            return "Error: No pude capturar la pantalla."

        self.log.info("Screenshot captured (length: %d). Getting active window...", len(img_b64))
        active_window = self.get_active_window()
        self.log.info("Active window: %s. Constructing prompt...", active_window)
        
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
            self.log.info("Sending request to vision model: %s", self.vision_model)
            with httpx.Client(timeout=60.0) as client:
                r = client.post(url, json=payload)
                self.log.info("Vision model respond-status: %d", r.status_code)
                r.raise_for_status()
                data = r.json()
                description = data.get("response", "").strip()
                self.log.info("Screen description received: %s", description[:100] + "...")
                return description
        except Exception as e:
            self.log.warning("Vision model failed or not found: %s. Falling back to simple context.", e)
            msg = f"No pude analizar la pantalla con el modelo de visión (timeout o desconexión)."
            if active_window:
                msg += f" Sin embargo, veo que la ventana activa es '{active_window}'."
            return msg
