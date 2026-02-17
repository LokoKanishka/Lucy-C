import sys
from pathlib import Path
import logging

# Add the project root to sys.path
root = Path(__file__).resolve().parents[1]
sys.path.append(str(root))

from lucy_c.config import LucyConfig
from lucy_c.pipeline import Moltbot

def verify_file_management():
    logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')
    log = logging.getLogger("VerifyFiles")
    
    cfg_path = root / "config" / "config.yaml"
    cfg = LucyConfig.load(cfg_path)
    
    moltbot = Moltbot(cfg)
    user = "test-files"

    # 1. Test Writing a file
    log.info("TEST 1: Writing a new file...")
    prompt = '[[write_file("data/test_file.txt", "Hola desde el test de Lucy")]]'
    result = moltbot._execute_tools(prompt, session_user=user)
    if "Archivo escrito exitosamente" in result:
        log.info("SUCCESS: File written.")
    else:
        log.error(f"FAILURE: Write failed. Result: {result}")

    # 2. Test Reading the file back
    log.info("TEST 2: Reading the file back...")
    prompt = '[[read_file("data/test_file.txt")]]'
    result = moltbot._execute_tools(prompt, session_user=user)
    if "Hola desde el test de Lucy" in result:
        log.info("SUCCESS: File read correctly.")
    else:
        log.error(f"FAILURE: Read failed. Result: {result}")

    # 3. Test Security Boundary
    log.info("TEST 3: Security boundary (trying to go outside root)...")
    prompt = '[[read_file("../../../etc/passwd")]]'
    result = moltbot._execute_tools(prompt, session_user=user)
    if "Acceso denegado" in result:
        log.info("SUCCESS: Outside-root access blocked.")
    else:
        log.error(f"FAILURE: Security breach possible! Result: {result}")

if __name__ == "__main__":
    verify_file_management()
