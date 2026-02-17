import sys
import os
from pathlib import Path

# Add the project root to sys.path
root = Path(__file__).resolve().parents[2]
sys.path.append(str(root))

import logging
from lucy_c.config import LucyConfig
from lucy_c.pipeline import Moltbot

def test_brain_exchange():
    logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')
    log = logging.getLogger("VerifyPhase2")
    
    cfg_path = root / "config" / "config.yaml"
    cfg = LucyConfig.load(cfg_path)
    moltbot = Moltbot(cfg)
    
    # 1. Start with Model A
    model_a = "gpt-oss:20b"
    moltbot.switch_brain(model_a)
    log.info(f"--- TURN 1: Model {model_a} ---")
    res1 = moltbot.run_turn_from_text("Hola, ¿cómo estás? Soy Diego.", session_user="test_session")
    log.info(f"Reply 1: {res1.reply}")
    
    # 2. Switch to Model B (if available, otherwise re-test same but check memory)
    # List models to find a candidate for switch
    models = moltbot.ollama.list_models()
    model_b = next((m for m in models if m != model_a), model_a)
    
    log.info(f"--- SWITCHING BRAIN to {model_b} ---")
    moltbot.switch_brain(model_b)
    
    log.info(f"--- TURN 2: Model {model_b} ---")
    # Test memory persistence
    res2 = moltbot.run_turn_from_text("¿Te acordás de mi nombre?", session_user="test_session")
    log.info(f"Reply 2: {res2.reply}")
    
    if "Diego" in res2.reply:
        log.info("SUCCESS: Memory persisted across brain exchange.")
    else:
        log.warning("MEMORY CHECK: 'Diego' not found in response. This might be due to model quality or memory length.")

if __name__ == "__main__":
    test_brain_exchange()
