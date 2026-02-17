import sys
from pathlib import Path
import logging

# Add the project root to sys.path
root = Path(__file__).resolve().parents[1]
sys.path.append(str(root))

from lucy_c.config import LucyConfig
from lucy_c.pipeline import Moltbot
from lucy_c.facts_store import FactsStore, default_facts_dir

def verify_architect_tools():
    logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')
    log = logging.getLogger("VerifyArchitectTools")
    
    cfg_path = root / "config" / "config.yaml"
    cfg = LucyConfig.load(cfg_path)
    
    facts = FactsStore(root / "data" / "facts_architect")
    moltbot = Moltbot(cfg, facts=facts)
    user = "test-architect"

    # 1. Test Complex Arguments (Commas inside quotes)
    log.info("TEST 1: Complex arguments with quotes and commas...")
    prompt = 'Ok, [[remember("lista_compras", "leche, huevos, pan")]]'
    result = moltbot._execute_tools(prompt, session_user=user)
    
    if "Recordado: lista_compras = leche, huevos, pan" in result:
        log.info("SUCCESS: Handled complex quoted arguments.")
    else:
        log.error(f"FAILURE: Complex args failed. Result: {result}")

    # 2. Test Security Filter
    log.info("TEST 2: Security filter (forbidden command injection)...")
    prompt = 'Intentando inyectar: [[remember("test", "hacked; rm -rf /")]]'
    result = moltbot._execute_tools(prompt, session_user=user)
    
    if "[⚠️ SEGURIDAD]" in result:
        log.info("SUCCESS: Blocked suspicious command injection.")
    else:
        log.error(f"FAILURE: Security filter failed to block. Result: {result}")

    # 3. Test Invalid Tool
    log.info("TEST 3: Non-existent tool...")
    prompt = '[[vuela_a_la_luna()]]'
    result = moltbot._execute_tools(prompt, session_user=user)
    if "no disponible" in result:
        log.info("SUCCESS: Correctly handled missing tool.")
    else:
        log.error(f"FAILURE: Missing tool handling failed. Result: {result}")

if __name__ == "__main__":
    verify_architect_tools()
