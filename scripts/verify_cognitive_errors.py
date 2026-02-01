import sys
from pathlib import Path
import logging
from unittest.mock import MagicMock, patch

# Add the project root to sys.path
root = Path(__file__).resolve().parents[1]
sys.path.append(str(root))

from lucy_c.config import LucyConfig
from lucy_c.pipeline import Moltbot

def test_error_handling():
    logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')
    log = logging.getLogger("VerifyCognitiveErrors")
    
    cfg_path = root / "config" / "config.yaml"
    cfg = LucyConfig.load(cfg_path)
    cfg.llm.provider = "ollama"
    
    moltbot = Moltbot(cfg)
    
    # 1. Test Recovery from empty response after retry
    log.info("TEST 1: Recovery from empty response after 1 retry...")
    with patch.object(moltbot.ollama, 'chat') as mock_chat:
        # Mock 1: Empty, Mock 2: Success
        mock_chat.side_effect = [
            MagicMock(text=""),
            MagicMock(text="Hola, ahora sí funciono.")
        ]
        
        result = moltbot.run_turn_from_text("Hola")
        log.info(f"Reply: {result.reply}")
        if "Hola, ahora sí funciono" in result.reply:
            log.info("SUCCESS: Recovered from empty response.")
        else:
            log.error("FAILURE: Did not recover correctly.")

    # 2. Test Timeout Fallback
    log.info("TEST 2: Connection/Timeout fallback...")
    with patch.object(moltbot.ollama, 'chat') as mock_chat:
        mock_chat.side_effect = Exception("Connection timed out")
        
        result = moltbot.run_turn_from_text("Hola")
        log.info(f"Reply: {result.reply}")
        if "problema de conexión" in result.reply.lower():
            log.info("SUCCESS: Correct connection fallback message.")
        else:
            log.error("FAILURE: Incorrect fallback or message.")

    # 3. Test Cognitive Fallback (all empty)
    log.info("TEST 3: Cognitive fallback (all retries empty)...")
    with patch.object(moltbot.ollama, 'chat') as mock_chat:
        mock_chat.side_effect = [
            MagicMock(text=""),
            MagicMock(text=" "),
            MagicMock(text="  ")
        ]
        
        result = moltbot.run_turn_from_text("Hola")
        log.info(f"Reply: {result.reply}")
        if "cerebro se quedó en blanco" in result.reply.lower():
            log.info("SUCCESS: Correct cognitive fallback message.")
        else:
            log.error("FAILURE: Incorrect fallback or message.")

if __name__ == "__main__":
    test_error_handling()
