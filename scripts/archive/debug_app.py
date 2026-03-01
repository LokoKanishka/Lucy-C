#!/usr/bin/env python3
"""
Debug script to find where app.py is failing
"""

import sys
import traceback

print("=== Starting Lucy-C debug ===", flush=True)

try:
    print("1. Importing Flask...", flush=True)
    from flask import Flask
    print("   ✓ Flask OK", flush=True)
    
    print("2. Importing lucy_c.config...", flush=True)
    from lucy_c.config import LucyConfig
    print("   ✓ Config OK", flush=True)
    
    print("3. Importing lucy_c.pipeline...", flush=True)
    from lucy_c.pipeline import Moltbot
    print("   ✓ Pipeline OK", flush=True)
    
    print("4. Loading config...", flush=True)
    cfg = LucyConfig.load()
    print(f"   ✓ Config loaded: {cfg}", flush=True)
    
    print("5. Creating Moltbot...", flush=True)
    moltbot = Moltbot(cfg.moltbot, session_id="test")
    print("   ✓ Moltbot created", flush=True)
    
    print("\n✅ All imports and initialization successful!", flush=True)
    
except Exception as e:
    print(f"\n❌ ERROR: {e}", flush=True)
    traceback.print_exc()
    sys.exit(1)
