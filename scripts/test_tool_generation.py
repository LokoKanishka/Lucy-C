#!/usr/bin/env python3
"""Final test to verify tool execution in Web UI after disabling native Ollama tools."""
import sys
import time
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.append(str(root))

from lucy_c.config import load_config
from lucy_c.pipeline import Moltbot

def test_tool_generation():
    """Test that LLM generates [[tool()]] commands from SYSTEM_PROMPT."""
    print("=" * 60)
    print(" FINAL TOOL GENERATION TEST")
    print("=" * 60)
    
    cfg = load_config()
    moltbot = Moltbot(cfg)
    
    test_cases = [
        "Busca el clima en Buenos Aires",
        "Abrí la calculadora",
        "Lee el archivo /tmp/test.txt"
    ]
    
    for prompt in test_cases:
        print(f"\n📝 Test: {prompt}")
        print("-" * 60)
        
        result = moltbot._generate_reply(prompt, session_user="test_user")
        
        # Check if tools were detected/executed
        has_tool_marker = "[[" in result or "[TAG_" in result
        
        print(f"✓ Response length: {len(result)} chars")
        print(f"✓ Tool markers found: {has_tool_marker}")
        print(f"✓ Response preview: {result[:200]}...")
        
        if has_tool_marker:
            print("✅ PASS: Tool detected in response")
        else:
            print("⚠️  WARN: No tool markers found (might be hallucinating)")
        
        time.sleep(1)
    
    print("\n" + "=" * 60)
    print("Test completed!")

if __name__ == "__main__":
    test_tool_generation()
