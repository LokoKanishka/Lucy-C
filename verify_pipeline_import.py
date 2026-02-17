import sys
import os
sys.path.append(os.getcwd())

try:
    from lucy_c.pipeline import Moltbot
    print("Moltbot imported successfully")
except Exception as e:
    print(f"Import failed: {e}")
    sys.exit(1)
