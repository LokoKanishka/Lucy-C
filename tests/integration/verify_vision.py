import sys
from pathlib import Path
import logging

# Add the project root to sys.path
root = Path(__file__).resolve().parents[1]
sys.path.append(str(root))

from lucy_c.config import LucyConfig
from lucy_c.ollama_llm import OllamaLLM
from lucy_c.tools.vision_tool import SystemEyes

def verify_vision_enhancements():
    logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')
    log = logging.getLogger("VerifyVision")
    
    cfg = LucyConfig() # Use defaults
    ollama = OllamaLLM(cfg.ollama)
    eyes = SystemEyes(ollama)
    
    # 1. Test Active Window
    log.info("TEST 1: Testing active window detection...")
    window = eyes.get_active_window()
    log.info(f"Detected Window: {window}")
    if window and window != "Desconocida":
        log.info("SUCCESS: Window title captured.")
    else:
        log.warning("Could not capture window title (maybe no X session?)")

    # 2. Test Screenshot Capture
    log.info("TEST 2: Testing screenshot capture...")
    img = eyes.capture_screenshot()
    if img and len(img) > 1000:
        log.info(f"SUCCESS: Screenshot captured ({len(img)} bytes base64).")
    else:
        log.error("FAILURE: Screenshot capture failed.")

    # 3. Test Description with fallback
    log.info("TEST 3: Testing screen description (prompting)...")
    # This will likely fallback unless llama3.2-vision is running
    desc = eyes.describe_screen(mode="ocr")
    log.info(f"Result: {desc}")
    if desc:
        log.info("SUCCESS: Vision logic executed correctly.")

if __name__ == "__main__":
    verify_vision_enhancements()
