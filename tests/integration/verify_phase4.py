import sys
import os
from pathlib import Path

# Add the project root to sys.path
root = Path(__file__).resolve().parents[1]
sys.path.append(str(root))

import logging
from lucy_c.config import LucyConfig
from lucy_c.pipeline import Moltbot

def test_sensorimotor():
    logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')
    log = logging.getLogger("VerifyPhase4")
    
    cfg_path = root / "config" / "config.yaml"
    cfg = LucyConfig.load(cfg_path)
    moltbot = Moltbot(cfg)
    
    # 1. Test "Eyes" (direct tool call first)
    log.info("--- TESTING EYES (Screenshot) ---")
    description = moltbot.eyes.describe_screen()
    log.info(f"Screen Description: {description}")
    
    # 2. Test "Hands" (direct tool call)
    log.info("--- TESTING HANDS (Type) ---")
    moltbot.hands.type_text("Test de Lucy")
    log.info("Hands test complete (check your active window if you can)")
    
    # 3. Test Orchestration (Moltbot invoking tools)
    log.info("--- TESTING ORCHESTRATION ---")
    # We simulate a response from the LLM that includes a tool call
    simulated_response = "Claro, te digo qué veo. [[screenshot()]]"
    processed = moltbot._execute_tools(simulated_response)
    log.info(f"Processed Multi-turn: {processed}")

if __name__ == "__main__":
    test_sensorimotor()
