#!/usr/bin/env python3
"""
Debug which import in pipeline.py is failing
"""

import sys
import traceback

print("=== Testing pipeline.py imports ===\n", flush=True)

imports = [
    ("ASR", "from lucy_c.asr import FasterWhisperASR"),
    ("ClawdbotLLM", "from lucy_c.clawdbot_llm import ClawdbotLLM"),
    ("Config", "from lucy_c.config import LucyConfig"),
    ("Mimic3TTS", "from lucy_c.mimic3_tts import Mimic3TTS"),
    ("OllamaLLM", "from lucy_c.ollama_llm import OllamaLLM"),
    ("HistoryStore", "from lucy_c.history_store import HistoryStore, default_history_dir"),
    ("FactsStore", "from lucy_c.facts_store import FactsStore, default_facts_dir"),
    ("TextNormalizer", "from lucy_c.text_normalizer import normalize_for_tts"),
    ("Prompts", "from lucy_c.prompts import SYSTEM_PROMPT, PROMPT_VERSION"),
    ("ToolRouter", "from lucy_c.tool_router import ToolRouter, ToolResult"),
    ("FileTools", "from lucy_c.tools.file_tools import tool_read_file, tool_write_file"),
    ("BusinessTools", "from lucy_c.tools.business_tools import tool_check_shipping, tool_process_payment, tool_generate_budget_pdf"),
    ("WebTools", "from lucy_c.tools.web_tools import tool_web_search, tool_open_url, tool_read_url"),
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

print("\n✅ All imports successful!", flush=True)
