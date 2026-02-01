import sys
from pathlib import Path
import logging

# Add the project root to sys.path
root = Path(__file__).resolve().parents[1]
sys.path.append(str(root))

from lucy_c.config import LucyConfig
from lucy_c.ollama_llm import OllamaLLM

def verify_models():
    logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')
    log = logging.getLogger("VerifyModels")
    
    cfg_path = root / "config" / "config.yaml"
    cfg = LucyConfig.load(cfg_path)
    
    ollama = OllamaLLM(cfg.ollama)
    
    log.info("Fetching detailed model list from Ollama...")
    try:
        detailed = ollama.list_models_detailed()
        log.info(f"Found {len(detailed)} models.")
        
        for m in detailed:
            rec_tag = "[REC]" if m.is_recommended else "[EXT]"
            log.info(f"{rec_tag} {m.name} ({m.size_gb} GB) - {m.description}")
            log.info(f"      Fortalezas: {', '.join(m.strengths)}")
            
        if any(m.is_recommended for m in detailed):
            log.info("SUCCESS: Recommended models detected and enriched.")
        else:
            log.warning("NOTICE: No whitelisted models found, but listing works.")
            
    except Exception as e:
        log.error(f"FAILURE: Failed to list detailed models: {e}")

if __name__ == "__main__":
    verify_models()
