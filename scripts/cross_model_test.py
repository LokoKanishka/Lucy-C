import sys
from pathlib import Path
import logging
import time
import json

# Add the project root to sys.path
root = Path(__file__).resolve().parents[1]
sys.path.append(str(root))

from lucy_c.config import LucyConfig
from lucy_c.pipeline import Moltbot
from lucy_c.facts_store import FactsStore, default_facts_dir
from lucy_c.history_store import HistoryStore, default_history_dir

def run_benchmark():
    logging.basicConfig(level=logging.WARNING) # Keep it quiet
    log = logging.getLogger("CrossModelTest")
    log.setLevel(logging.INFO)
    
    cfg_path = root / "config" / "config.yaml"
    cfg = LucyConfig.load(cfg_path)
    
    # We want to test multiple models
    target_models = [
        "gpt-oss:20b",
        "llama3.1:8b",
        "dolphin-llama3:8b"
    ]
    
    test_cases = [
        {
            "id": "identidad",
            "prompt": "Che, decime quién sos y cómo viene la mano con el clima hoy (inventá algo tranqui).",
            "check": ["Lucy", "vos", "tenés", "che"] # Identity & Argentine Spanish
        },
        {
            "id": "instruccion_compleja",
            "prompt": "Recordá que mi postre favorito es el vigilante. Usá [[remember]]. No respondas nada más que la confirmación de la herramienta.",
            "check": ["[[remember(", "vigilante"]
        },
        {
            "id": "memoria_corto_plazo",
            "prompt": "¿Qué te dije recién sobre el postre?",
            "check": ["vigilante"]
        }
    ]
    
    results = {}

    for model in target_models:
        log.info(f"\n===== TESTING MODEL: {model} =====")
        try:
            # Instantiate a clean Moltbot for each model if needed, 
            # but we can also just switch brain.
            # Local stores to keep it isolated
            history = HistoryStore(root / "data" / "history_test")
            facts = FactsStore(root / "data" / "facts_test")
            moltbot = Moltbot(cfg, history=history, facts=facts)
            moltbot.switch_brain(model, provider="ollama")
            
            user = f"tester-{model.replace(':', '-')}"
            
            model_results = []
            for tc in test_cases:
                log.info(f"Running Test Case [{tc['id']}]...")
                start = time.time()
                res = moltbot.run_turn_from_text(tc['prompt'], session_user=user)
                latency = round(time.time() - start, 2)
                
                passed = all(word.lower() in res.reply.lower() for word in tc['check'])
                
                model_results.append({
                    "case": tc['id'],
                    "passed": passed,
                    "latency": latency,
                    "reply": res.reply[:150] + "..." if len(res.reply) > 150 else res.reply
                })
                
                status = "✅ PASS" if passed else "❌ FAIL"
                log.info(f"  {status} ({latency}s)")
            
            results[model] = model_results
            
        except Exception as e:
            log.error(f"Failed to test model {model}: {e}")
            results[model] = "ERROR"

    # Export results to markdown
    report_path = root / "docs" / "TEST_RESULTS.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Lucy Cross-Model Benchmark Results\n\n")
        f.write(f"Generated on: {time.ctime()}\n\n")
        
        for model, cases in results.items():
            f.write(f"## Model: {model}\n")
            if cases == "ERROR":
                f.write("- Falló la ejecución.\n\n")
                continue
                
            f.write("| Caso | Estado | Latencia | Respuesta Parcial |\n")
            f.write("|------|--------|----------|-------------------|\n")
            for c in cases:
                status = "✅" if c['passed'] else "❌"
                f.write(f"| {c['case']} | {status} | {c['latency']}s | {c['reply']} |\n")
            f.write("\n")

    log.info(f"\nReport generated at {report_path}")

if __name__ == "__main__":
    run_benchmark()
