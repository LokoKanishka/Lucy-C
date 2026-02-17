import sys
from pathlib import Path
import logging
import os
import shutil

# Add the project root to sys.path
root = Path(__file__).resolve().parents[2]
sys.path.append(str(root))

from lucy_c.config import LucyConfig
from lucy_c.pipeline import Moltbot
from lucy_c.facts_store import FactsStore, default_facts_dir

def test_persistence():
    logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')
    log = logging.getLogger("VerifyPersistence")
    
    cfg_path = root / "config" / "config.yaml"
    cfg = LucyConfig.load(cfg_path)
    
    facts = FactsStore(default_facts_dir())
    moltbot = Moltbot(cfg, facts=facts)
    
    user = "test-user-persistence"
    
    # 1. Start with default
    default_model = cfg.ollama.model
    log.info(f"Default model is: {default_model}")
    
    # 2. Switch brain and persist
    new_model = "mistral:7b"
    log.info(f"Switching brain to {new_model} for {user}...")
    moltbot.switch_brain(new_model, session_user=user)
    
    # 3. Simulate a RESTART (New Moltbot instance)
    log.info("Simulating system restart (new Moltbot instance)...")
    moltbot_reborn = Moltbot(cfg, facts=facts)
    
    # 4. Run a turn and check if it auto-applies the brain
    log.info(f"Running turn for {user} - should auto-apply {new_model}...")
    # We mock the LLM call to avoid real network but let the logic run
    from unittest.mock import MagicMock
    moltbot_reborn.ollama.chat = MagicMock(return_value=MagicMock(text="Respuesta simulada"))
    
    moltbot_reborn.run_turn_from_text("Hola", session_user=user)
    
    current_model = moltbot_reborn.cfg.ollama.model
    if current_model == new_model:
        log.info(f"SUCCESS: Brain choice persistent! Current: {current_model}")
    else:
        log.error(f"FAILURE: Brain choice NOT persistent. Found: {current_model}, Expected: {new_model}")

if __name__ == "__main__":
    test_persistence()
