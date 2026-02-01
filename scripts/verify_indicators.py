import sys
from pathlib import Path
import logging
from typing import Any, Dict

# Add the project root to sys.path
root = Path(__file__).resolve().parents[1]
sys.path.append(str(root))

from lucy_c.config import LucyConfig
from lucy_c.pipeline import Moltbot

def verify_visual_indicators():
    logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')
    log = logging.getLogger("VerifyIndicators")
    
    cfg = LucyConfig()
    
    status_updates = []
    def mock_status_callback(msg, type):
        status_updates.append((msg, type))
        log.info(f"STATUS EMITTED: {msg} ({type})")

    moltbot = Moltbot(cfg, status_callback=mock_status_callback)
    
    # Simulate a tool execution
    import asyncio
    
    async def run_test():
        log.info("Testing status emission for 'screenshot'...")
        prompt = "[[screenshot()]]"
        # We need a context for _execute_tools
        ctx = {"session_user": "test", "safe_mode": False}
        await moltbot._execute_tools(prompt, ctx)
        
        if any("Mirando pantalla..." in s[0] for s in status_updates):
            log.info("SUCCESS: 'Mirando pantalla...' status emitted.")
        else:
            log.error("FAILURE: Status not emitted.")

    asyncio.run(run_test())

if __name__ == "__main__":
    verify_visual_indicators()
