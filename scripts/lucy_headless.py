#!/usr/bin/env python3
"""
Lucy Headless: Prueba de Lucy Core sin interfaz gráfica y con sensores balanceados.
Demuestra que Lucy Core es independiente del Body.
"""
import os
import sys
import logging
from pathlib import Path

# Add root to sys.path
root = Path(__file__).resolve().parents[1]
sys.path.append(str(root))

from lucy_c.config import LucyConfig
from lucy_c.pipeline import Moltbot

def main():
    logging.basicConfig(level=logging.INFO, format="%(name)s - %(levelname)s - %(message)s")
    log = logging.getLogger("LucyHeadless")

    cfg_path = os.environ.get("LUCY_C_CONFIG", str(root / "config" / "config.yaml"))
    cfg = LucyConfig.load(cfg_path)
    
    log.info("Inicializando Lucy Core (Moltbot)...")
    moltbot = Moltbot(cfg)
    
    print("\n--- LUCY CORE INICIADA (Modo Headless) ---")
    print("Identidad: Lucy")
    print(f"Cerebro: {cfg.ollama.model}")
    print("Escribe 'salir' para terminar.\n")

    while True:
        try:
            text = input("Tú: ")
            if text.lower() in ["salir", "exit", "quit"]:
                break
            
            if not text.strip():
                continue
                
            print("Lucy está pensando...")
            # run_turn_from_text returns a TurnResult which includes the reply
            result = moltbot.run_turn_from_text(text, session_user="headless-dev")
            
            print(f"\nLucy: {result.reply}")
            print("-" * 20)
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            log.exception("Error en el turno")

    print("\nChau! Lucy vuelve a su núcleo.")

if __name__ == "__main__":
    main()
