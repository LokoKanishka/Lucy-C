#!/usr/bin/env python3
"""
Test the REMAINING imports from pipeline.py that weren't in the first test
"""

import sys
import traceback

print("=== Testing ADDITIONAL pipeline.py imports ===\n", flush=True)

imports = [
    ("OS Tools", "from lucy_c.tools.os_tools import tool_os_run, tool_window_manager"),
    ("Vision UI Tools", "from lucy_c.tools.vision_ui_tools import tool_scan_ui, tool_click_text, tool_peek_desktop"),
    ("N8N Tools", "from lucy_c.tools.n8n_tools import create_n8n_tools"),
    ("Cognitive Tools", "from lucy_c.tools.cognitive_tools import create_cognitive_tools"),
    ("RAG Engine", "from lucy_c.rag_engine import MemoryEngine"),
    ("Knowledge Tools", "from lucy_c.tools.knowledge_tools import create_knowledge_tools"),
]

for name, import_stmt in imports:
    try:
        print(f"Importing {name}...", flush=True)
        exec(import_stmt)
        print(f"  ✓ {name} OK", flush=True)
    except Exception as e:
        print(f"  ❌ {name} FAILED: {e}", flush=True)
        traceback.print_exc()
        sys.exit(1)

print("\n✅ All additional imports successful!", flush=True)

# Now try the full pipeline import
print("\n=== Testing full pipeline.py import ===", flush=True)
try:
    from lucy_c.pipeline import Moltbot
    print("✅ pipeline.py imported successfully!", flush=True)
except Exception as e:
    print(f"❌ pipeline.py FAILED: {e}", flush=True)
    traceback.print_exc()
