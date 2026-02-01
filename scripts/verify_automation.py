import sys
from pathlib import Path
import logging
import time

# Add the project root to sys.path
root = Path(__file__).resolve().parents[1]
sys.path.append(str(root))

from lucy_c.config import LucyConfig
from lucy_c.pipeline import Moltbot

def verify_automation_enhancements():
    logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')
    log = logging.getLogger("VerifyAutomation")
    
    cfg_path = root / "config" / "config.yaml"
    cfg = LucyConfig.load(cfg_path)
    
    moltbot = Moltbot(cfg)
    user = "test-automation"

    # 1. Test Move and Click
    log.info("TEST 1: Testing move and click...")
    # Using a safe area or just moving
    prompt = '[[move(100, 100)]] [[click(100, 100, "left")]]'
    result = moltbot._execute_tools(prompt, session_user=user)
    log.info(f"Result: {result}")
    if "Moví el mouse a (100, 100)" in result and "Hice 1 clic(s) left en (100, 100)" in result:
        log.info("SUCCESS: Move and click executed.")
    else:
        log.error("FAILURE: Move or click failed.")

    # 2. Test Wait
    log.info("TEST 2: Testing wait...")
    start_t = time.time()
    prompt = '[[wait(1.5)]]'
    result = moltbot._execute_tools(prompt, session_user=user)
    elapsed = time.time() - start_t
    log.info(f"Wait result: {result} (Elapsed: {elapsed:.2f}s)")
    if elapsed >= 1.5:
        log.info("SUCCESS: Wait tool worked.")
    else:
        log.error("FAILURE: Wait too short.")

    # 3. Test Hotkey
    log.info("TEST 3: Testing hotkey (ctrl+c simulation)...")
    prompt = '[[hotkey("ctrl", "c")]]'
    result = moltbot._execute_tools(prompt, session_user=user)
    log.info(f"Hotkey result: {result}")
    if "Ejecuté el atajo: ctrl + c" in result:
        log.info("SUCCESS: Hotkey executed.")
    else:
        log.error("FAILURE: Hotkey failed.")

if __name__ == "__main__":
    verify_automation_enhancements()
