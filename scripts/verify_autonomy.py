#!/usr/bin/env python3
"""Verification script for Autonomous Context (RAG Local Memory)."""
import sys
import logging
from pathlib import Path
import time

root = Path(__file__).resolve().parents[1]
sys.path.append(str(root))

from lucy_c.config import LucyConfig
from lucy_c.pipeline import Moltbot

logging.basicConfig(level=logging.INFO, format="%(name)s - %(levelname)s - %(message)s")

def test_autonomy():
    """Test RAG memory for autonomous context retrieval."""
    print("--- INICIANDO TEST DE AUTONOMÍA (RAG MEMORY) ---\n")
    
    # Clear any previous test data
    test_file = root / "data" / "test_mission.txt"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Create test document with unique information
    secret_info = """
    PROYECTO OMEGA - DOCUMENTACIÓN CLASIFICADA
    
    Objetivo Principal: Colonizar Marte en la década de 2030
    
    Fases del Proyecto:
    1. Diseño de naves de transporte (2025-2027)
    2. Construcción de hábitats marcianos (2027-2029)
    3. Pruebas de sistemas de soporte vital (2029-2030)
    4. Primera misión tripulada (2031)
    
    Código de Acceso: OMEGA-7744
    
    Directora del Proyecto: Dra. Elena Rodríguez
    Presupuesto Total: 50 mil millones de dólares
    
    Notas Técnicas:
    - Propulsión: Motores iónicos de nueva generación
    - Alimentación: Energía nuclear compacta
    - Comunicaciones: Sistema de retransmi

sión cuántica
    
    CONFIDENCIAL - NO DISTRIBUIR
    """
    
    test_file.write_text(secret_info.strip())
    print(f"[SETUP] Created test file: {test_file}")
    
    # Load config and create Moltbot
    cfg = LucyConfig.load(root / "config" / "config.yaml")
    moltbot = Moltbot(cfg)
    
    # Clear any existing memory to ensure clean test
    if moltbot.memory:
        moltbot.memory.clear()
        print("[SETUP] Cleared existing memory\n")
    
    # Test Case 1: Ingest document
    print("\n[TEST 1]: Document Ingestion")
    print(f"User: Lucy, memorizá este archivo: {test_file}")
    
    result1 = moltbot.run_turn_from_text(f"Memorizá el archivo {test_file}", session_user="tester")
    print(f"Lucy: {result1.reply[:200]}...")
    
    if "fragmentos guardados" in result1.reply.lower() or "memoricé" in result1.reply.lower():
        print("RESULTADO: ✅ EXITO - Documento ingerido\n")
    else:
        print("RESULTADO: ❌ FALLO - No se ingesto el documento\n")
    
    # Wait a bit for embeddings to settle
    time.sleep(1)
    
    # Test Case 2: Cross-Session Recall (simulate restart)
    print("\n[TEST 2]: Cross-Session Memory (Autonomous Recall)")
    print("Simulando reinicio de Lucy...")
    
    # Create new Moltbot instance (simulates restart)
    moltbot2 = Moltbot(cfg)
    print("Lucy reiniciada. El chat está vacío, pero la memoria persiste.")
    
    print("\nUser: ¿Cuál es el objetivo del Proyecto Omega?")
    result2 = moltbot2.run_turn_from_text("¿Cuál es el objetivo del Proyecto Omega?", session_user="tester")
    print(f"Lucy: {result2.reply[:300]}...")
    
    if "marte" in result2.reply.lower() or "colonizar" in result2.reply.lower():
        print("RESULTADO: ✅ EXITO - Recuperó información de memoria persistente\n")
    else:
        print("RESULTADO: ⚠️ FALLO - No recordó el documento")
        print(f"Respuesta completa: {result2.reply}\n")
    
    # Test Case 3: Semantic Search (not exact text)
    print("\n[TEST 3]: Semantic Search (Concept Understanding)")
    print("User: ¿Quién dirige el proyecto espacial?")
    
    result3 = moltbot2.run_turn_from_text("¿Quién dirige el proyecto espacial?", session_user="tester")
    print(f"Lucy: {result3.reply[:300]}...")
    
    if "elena" in result3.reply.lower() or "rodríguez" in result3.reply.lower():
        print("RESULTADO: ✅ EXITO - Búsqueda semántica funcional\n")
    else:
        print("RESULTADO: ⚠️ No encontró la información relevante\n")
    
    # Test Case 4: Code of Access Retrieval
    print("\n[TEST 4]: Specific Data Retrieval")
    print("User: ¿Cuál es el código de acceso del proyecto?")
    
    result4 = moltbot2.run_turn_from_text("¿Cuál es el código de acceso del proyecto?", session_user="tester")
    print(f"Lucy: {result4.reply[:300]}...")
    
    if "7744" in result4.reply or "OMEGA-7744" in result4.reply:
        print("RESULTADO: ✅ EXITO - Recuperó datos específicos\n")
    else:
        print("RESULTADO: ⚠️ No encontró el código exacto\n")
    
    # Memory Stats
    if moltbot2.memory:
        stats = moltbot2.memory.stats()
        print(f"\n[STATS] Memoria: {stats['total_documents']} fragmentos almacenados")
        print(f"[STATS] Ubicación: {stats['persist_directory']}")
    
    # Cleanup
    test_file.unlink()
    print(f"\n[CLEANUP] Removed test file")

if __name__ == "__main__":
    test_autonomy()
