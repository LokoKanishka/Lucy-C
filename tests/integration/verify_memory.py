import sys
from pathlib import Path
import logging
import time

# Add the project root to sys.path
root = Path(__file__).resolve().parents[2]
sys.path.append(str(root))

from lucy_c.config import LucyConfig
from lucy_c.pipeline import Moltbot
from lucy_c.history_store import HistoryStore, default_history_dir
from lucy_c.facts_store import FactsStore, default_facts_dir

def test_memory():
    logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')
    log = logging.getLogger("VerifyMemory")
    
    cfg_path = root / "config" / "config.yaml"
    cfg = LucyConfig.load(cfg_path)
    cfg.llm.provider = "ollama"
    
    history = HistoryStore(default_history_dir())
    facts = FactsStore(default_facts_dir())
    moltbot = Moltbot(cfg, history=history, facts=facts)
    
    user = "test-user-memory"
    
    # Clean old facts
    log.info(f"Cleaning facts for {user}...")
    moltbot.facts.remove_fact(user, "color_favorito")
    
    # 1. Test direct fact setting
    log.info("Testing direct fact setting...")
    moltbot.facts.set_fact(user, "prefijo", "Sr.")
    
    # 2. Test fact injection in prompt
    log.info("Verifying fact injection...")
    messages = moltbot._get_chat_messages("Hola", session_user=user)
    system_msg = messages[0]["content"]
    if "prefijo" in system_msg and "Sr." in system_msg:
        log.info("SUCCESS: Fact injected into system prompt.")
    else:
        log.error("FAILURE: Fact NOT found in system prompt.")
        return

    # 3. Test autonomous remembering via tool
    log.info("Testing autonomous memory tool [[remember()]]...")
    prompt = "Lucy, recordá que mi color favorito es el azul. Usá la herramienta [[remember]]."
    result = moltbot.run_turn_from_text(prompt, session_user=user)
    log.info(f"Moltbot reply: {result.reply}")
    
    if "🧠 MEMORIA" in result.reply and "color_favorito" in result.reply:
        log.info("SUCCESS: Moltbot used the remember tool.")
    else:
        log.error("FAILURE: Moltbot did not use the remember tool correctly.")
        
    # Verify it persists
    persisted_facts = moltbot.facts.get_facts(user)
    if persisted_facts.get("color_favorito") == "azul":
        log.info("SUCCESS: Fact persisted to disk.")
    else:
        log.error(f"FAILURE: Fact not persisted. Current facts: {persisted_facts}")

    # 4. Test forgetting
    log.info("Testing autonomous forget tool [[forget()]]...")
    prompt = "Lucy, olvidá mi color favorito."
    result = moltbot.run_turn_from_text(prompt, session_user=user)
    log.info(f"Moltbot reply: {result.reply}")
    
    if "Olvidado: color_favorito" in result.reply:
        log.info("SUCCESS: Moltbot used the forget tool.")
    else:
        log.error("FAILURE: Moltbot did not use the forget tool correctly.")

    persisted_facts = moltbot.facts.get_facts(user)
    if "color_favorito" not in persisted_facts:
        log.info("SUCCESS: Fact removed from disk.")
    else:
        log.error("FAILURE: Fact still exists on disk.")

if __name__ == "__main__":
    test_memory()
