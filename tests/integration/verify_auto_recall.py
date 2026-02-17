#!/usr/bin/env python3
"""Verification script for Autonomous Recall (without explicit prompting)."""
import sys
import logging
from pathlib import Path
import time

root = Path(__file__).resolve().parents[1]
sys.path.append(str(root))

from lucy_c.config import LucyConfig
from lucy_c.pipeline import Moltbot

logging.basicConfig(level=logging.INFO, format="%(name)s - %(levelname)s - %(message)s")

def test_auto_recall():
    """Test that Lucy uses recall autonomously without being told."""
    print("--- INICIANDO TEST DE AUTO-RECALL (AUTONOMÍA REAL) ---\n")
    
    # Setup: Create technical documentation
    test_file = root / "data" / "test_config.md"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    
    config_doc = """
    # Configuración del Proyecto Lucy-C
    
    ## Base de Datos
    - Motor: PostgreSQL 15
    - Puerto: 5432
    - Host: localhost
    - Database: lucy_production
    
    ## Servidor Web
    - Framework: Flask 3.0
    - Puerto de desarrollo: 5000
    - Puerto de staging: 9999
    - Puerto de producción: 8080
    
    ## Integración n8n
    - URL: http://localhost:5678
    - Webhook prefix: lucy-
    - Timeout: 30 segundos
    
    ## Modelos LLM
    - Modelo local: gpt-oss:20b (Ollama)
    - Modelo SOTA delegado: Gemini 2.0 Flash (vía n8n/OpenRouter)
    
    ## Memoria RAG
    - Motor: ChromaDB
    - Embeddings: all-MiniLM-L6-v2 (sentence-transformers)
    - Directorio: data/chroma_db/
    """
    
    test_file.write_text(config_doc.strip())
    print(f"[SETUP] Created technical documentation: {test_file}\n")
    
    # Initialize and clear memory
    cfg = LucyConfig.load(root / "config" / "config.yaml")
    moltbot = Moltbot(cfg)
    
    if moltbot.memory:
        moltbot.memory.clear()
        print("[SETUP] Cleared existing memory\n")
    
    # Step 1: Ingest the documentation
    print("[STEP 1]: Ingesting documentation")
    print(f"User: Memorizá el archivo {test_file}")
    
    result1 = moltbot.run_turn_from_text(f"Memorizá el archivo {test_file}", session_user="autonomy_tester")
    print(f"Lucy: {result1.reply[:150]}...")
    
    if "memoricé" in result1.reply.lower() or "fragmentos" in result1.reply.lower():
        print("✅ Documentación ingerida\n")
    else:
        print("❌ Fallo en la ingesta\n")
        return
    
    time.sleep(1)
    
    # Step 2: Simulate new session (clear chat history but keep memory)
    print("[STEP 2]: Simulando nueva sesión...")
    moltbot2 = Moltbot(cfg)
    print("Nueva sesión iniciada. Chat history vacío, pero memoria persiste.\n")
    
    # Test Cases - WITHOUT mentioning "memoria" or "recall"
    test_cases = [
        {
            "name": "Puerto de Staging (Autonomía)",
            "question": "¿Cuál es el puerto del servidor de staging?",
            "expected_answer": "9999",
            "check_recall_used": True
        },
        {
            "name": "Base de Datos (Autonomía)",
            "question": "¿Qué motor de base de datos usa el proyecto?",
            "expected_answer": "postgresql",
            "check_recall_used": True
        },
        {
            "name": "Modelo SOTA (Autonomía)",
            "question": "¿Qué modelo usa Lucy cuando delega a la nube?",
            "expected_answer": "gemini",
            "check_recall_used": True
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n[TEST {i}]: {case['name']}")
        print(f"User: {case['question']}")
        print("(Sin mencionar 'memoria' ni 'recall' - Lucy debe buscar por iniciativa propia)")
        
        result = moltbot2.run_turn_from_text(case['question'], session_user="autonomy_tester")
        print(f"Lucy: {result.reply[:300]}...")
        
        # Check if recall was used (look for the tool call in logs or response)
        used_recall = "[[recall" in result.reply or "memoria" in result.reply.lower() or "memoricé" in result.reply.lower()
        
        # Check if correct answer is present
        correct_answer = case['expected_answer'].lower() in result.reply.lower()
        
        if case['check_recall_used'] and used_recall:
            print("✅ Lucy USÓ recall por iniciativa propia")
        elif case['check_recall_used']:
            print("⚠️ Lucy NO usó recall (esperado que lo hiciera)")
        
        if correct_answer:
            print(f"✅ Respuesta correcta encontrada: '{case['expected_answer']}'")
            print("RESULTADO: ✅ EXITO - Autonomía funcional\n")
        else:
            print(f"❌ Respuesta esperada '{case['expected_answer']}' no encontrada")
            print("RESULTADO: ❌ FALLO - No recuperó la información\n")
    
    # Memory stats
    if moltbot2.memory:
        stats = moltbot2.memory.stats()
        print(f"\n[STATS] Fragmentos en memoria: {stats['total_documents']}")
    
    # Cleanup
    test_file.unlink()
    print(f"\n[CLEANUP] Test completed")

if __name__ == "__main__":
    test_auto_recall()
