import sys
from pathlib import Path
import logging

# Add the project root to sys.path
root = Path(__file__).resolve().parents[1]
sys.path.append(str(root))

from lucy_c.config import LucyConfig
from lucy_c.pipeline import Moltbot

def verify_reflection_and_safety():
    logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')
    log = logging.getLogger("VerifyReflection")
    
    cfg_path = root / "config" / "config.yaml"
    cfg = LucyConfig.load(cfg_path)
    
    # Enable safe_mode for testing
    cfg.safe_mode = True
    moltbot = Moltbot(cfg)
    user = "test-reflection"

    # 1. Test Safety Block (Write)
    log.info("TEST 1: Testing safety block for write_file...")
    prompt = '[[write_file("data/security_test.txt", "hacked")]]'
    result = moltbot._generate_reply(prompt, session_user=user)
    log.info(f"Result (Should be natural apology): {result}")
    if "Modo Seguro" in result or "seguridad" in result.lower() or "bloqueada" in result.lower():
        log.info("SUCCESS: Safety block reflected naturally.")
    else:
        log.error("FAILURE: Result did not feel reflected or blocked correctly.")

    # 2. Test Reflection loop (Natural Language Response)
    # Since we can't easily force Ollama to always cooperate in one turn, 
    # we'll look for signs of the second pass.
    log.info("TEST 2: Testing reflection on successful tool (remember)...")
    cfg.safe_mode = False # Disable for this test
    prompt = 'Recordá que mi color favorito es el verde usando [[remember("color", "verde")]]. Respondé de forma natural.'
    result = moltbot._generate_reply(prompt, session_user=user)
    log.info(f"Result (Should be a natural sentence): {result}")
    if "verde" in result and "[[remember" not in result:
        log.info("SUCCESS: Reflection loop generated a natural response.")
    else:
        log.info("NOTE: Result might still have tool syntax if model chose to, but check if it's natural.")

    # 3. Test Forget block
    log.info("TEST 3: Testing forget block in safe_mode...")
    cfg.safe_mode = True
    prompt = '[[forget("color")]]'
    result = moltbot._generate_reply(prompt, session_user=user)
    log.info(f"Result: {result}")
    if "bloqueado" in result or "seguridad" in result.lower():
        log.info("SUCCESS: Forget blocked by safe_mode.")

if __name__ == "__main__":
    verify_reflection_and_safety()
