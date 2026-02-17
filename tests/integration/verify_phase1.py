import sys
import os
from pathlib import Path

# Add the project root to sys.path
root = Path(__file__).resolve().parents[1]
sys.path.append(str(root))

import logging
from lucy_c.config import LucyConfig
from lucy_c.pipeline import Moltbot

def test_moltbot_local():
    logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')
    log = logging.getLogger("VerifyPhase1")
    
    cfg_path = root / "config" / "config.yaml"
    if not cfg_path.exists():
        log.error(f"Config file not found at {cfg_path}")
        return

    log.info(f"Loading config from {cfg_path}")
    cfg = LucyConfig.load(cfg_path)
    
    # Force provider to ollama for this test to ensure local-only
    cfg.llm.provider = "ollama"
    
    log.info("Initializing Moltbot...")
    try:
        moltbot = Moltbot(cfg)
    except Exception as e:
        log.error(f"Failed to initialize Moltbot: {e}")
        return

    test_prompt = "Hola Lucy, ¿quién sos y qué modelo estás usando?"
    log.info(f"Sending test prompt: {test_prompt}")
    
    try:
        result = moltbot.run_turn_from_text(test_prompt)
        log.info("--- TEST RESULT ---")
        log.info(f"Transcript: {result.transcript}")
        log.info(f"Reply: {result.reply}")
        log.info(f"Audio Generated: {'Yes' if result.reply_wav else 'No'} ({len(result.reply_wav)} bytes)")
        log.info("-------------------")
        
        if result.reply:
            log.info("SUCCESS: Moltbot responded successfully.")
        else:
            log.error("FAILURE: Moltbot returned an empty response.")
            
    except Exception as e:
        log.error(f"Error during Moltbot turn: {e}")

if __name__ == "__main__":
    test_moltbot_local()
