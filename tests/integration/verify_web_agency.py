#!/usr/bin/env python3
"""Diagnostic script to test tool execution in Lucy-C."""
import sys
import logging
from pathlib import Path

root = Path(__file__).resolve().parents[2]
sys.path.append(str(root))

from lucy_c.config import LucyConfig
from lucy_c.pipeline import Moltbot

logging.basicConfig(level=logging.INFO, format="%(name)s - %(levelname)s - %(message)s")

print("=== LUCY-C TOOL EXECUTION DIAGNOSTIC ===\n")

# Load config
cfg = LucyConfig.load(root / "config" / "config.yaml")

# Create status callback to see what's being sent
status_messages = []
def test_callback(message, type="info"):
    status_messages.append({"message": message, "type": type})
    print(f"[STATUS_{type.upper()}] {message}")

# Initialize Moltbot with callback
moltbot = Moltbot(cfg, status_callback=test_callback)

print(f"Tools available: {list(moltbot.tool_router.tools.keys())}\n")

# Test cases that should trigger tool execution
test_cases = [
    {
        "name": "Web Search",
        "prompt": "Buscá en internet el clima de Buenos Aires",
        "expected_tool": "search_web"
    },
    {
        "name": "OS Control",
        "prompt": "Abrí la calculadora usando gnome-calculator",
        "expected_tool": "os_run"
    },
    {
        "name": "Memory Recall",
        "prompt": "Buscá en tu memoria información sobre configuración",
        "expected_tool": "recall"
    }
]

for i, case in enumerate(test_cases, 1):
    print(f"\n{'='*60}")
    print(f"TEST {i}: {case['name']}")
    print(f"{'='*60}")
    print(f"Prompt: \"{case['prompt']}\"")
    print(f"Expected tool: {case['expected_tool']}\n")
    
    status_messages.clear()
    
    result = moltbot.run_turn_from_text(case['prompt'], session_user="diagnostic_test")
    
    print(f"\n--- RESULT ---")
    print(result.reply)
    print(f"\n--- STATUS MESSAGES ---")
    for msg in status_messages:
        print(f"  [{msg['type']}] {msg['message']}")
    
    # Check if tool was mentioned in reply or logs
    tool_in_reply = case['expected_tool'] in result.reply.lower() or f"[[{case['expected_tool']}" in result.reply
    
    print(f"\n--- ANALYSIS ---")
    print(f"Tool mentioned in reply: {tool_in_reply}")
    print(f"Status callback count: {len(status_messages)}")
    
    if tool_in_reply or len(status_messages) > 2:
        print(f"✅ Tool execution detected")
    else:
        print(f"⚠️ Tool may not have triggered")

print(f"\n\n{'='*60}")
print("DIAGNOSTIC COMPLETE")
print(f"{'='*60}")
