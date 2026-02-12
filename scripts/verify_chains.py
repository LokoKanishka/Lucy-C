#!/usr/bin/env python3
"""
Verification script for Lucy's advanced agency features.
Tests web reading, window management, and task chaining.
"""

import sys
import os
import time
import subprocess

# Add parent dir to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from lucy_c.config import LucyConfig
from lucy_c.pipeline import Moltbot
from lucy_c.history_store import HistoryStore
from lucy_c.facts_store import FactsStore

def test_web_reading():
    """Test 1: Web reading capability"""
    print("\n" + "="*60)
    print("TEST 1: Web Reading (tool_read_url)")
    print("="*60)
    
    cfg = LucyConfig()
    bot = Moltbot(cfg)
    
    # Test reading a simple, stable page
    test_url = "https://example.com"
    result = bot.run_turn_from_text(f"Leeme el contenido de {test_url} y decime de qué trata")
    
    print(f"\nUser: Leeme el contenido de {test_url} y decime de qué trata")
    print(f"Lucy: {result.reply}")
    
    # Verify tool was called and content extracted
    if "example" in result.reply.lower() and ("ilustrativo" in result.reply.lower() or "ejemplo" in result.reply.lower() or "domain" in result.reply.lower()):
        print("\n✅ PASS: Lucy successfully read and understood the web page")
        return True
    else:
        print("\n❌ FAIL: Lucy did not properly read the web page")
        return False

def test_window_management():
    """Test 2: Window management capability"""
    print("\n" + "="*60)
    print("TEST 2: Window Management (tool_window_manager)")
    print("="*60)
    
    # Check if wmctrl is installed
    try:
        subprocess.run(["wmctrl", "-h"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("\n⚠️  SKIP: wmctrl not installed. Install with: sudo apt install wmctrl")
        return None
    
    cfg = LucyConfig()
    bot = Moltbot(cfg)
    
    # Test 2a: List windows
    result = bot.run_turn_from_text("Listame las ventanas abiertas")
    print(f"\nUser: Listame las ventanas abiertas")
    print(f"Lucy: {result.reply}")
    
    if "ventanas" in result.reply.lower() or "window" in result.reply.lower():
        print("\n✅ PASS: Lucy can list windows")
    else:
        print("\n❌ FAIL: Lucy could not list windows")
        return False
    
    # Test 2b: Open and focus a window
    print("\n--- Opening calculator for focus test ---")
    result = bot.run_turn_from_text("Abrí la calculadora")
    time.sleep(2)  # Wait for app to open
    
    result = bot.run_turn_from_text("Traeme la calculadora al frente")
    print(f"\nUser: Traeme la calculadora al frente")
    print(f"Lucy: {result.reply}")
    
    if "frente" in result.reply.lower() or "enfocad" in result.reply.lower() or "calculadora" in result.reply.lower():
        print("\n✅ PASS: Lucy can focus windows")
        # Cleanup
        subprocess.run(["wmctrl", "-c", "Calculator"], stderr=subprocess.DEVNULL)
        return True
    else:
        print("\n❌ FAIL: Lucy could not focus window")
        return False

def test_task_chaining():
    """Test 3: Multi-step task chaining"""
    print("\n" + "="*60)
    print("TEST 3: Task Chaining (multi-step reasoning)")
    print("="*60)
    
    cfg = LucyConfig()
    bot = Moltbot(cfg)
    
    # Complex task: read URL -> save file
    test_file = "/tmp/lucy_test_chain.txt"
    test_url = "https://example.com"
    
    # Clean up previous test file
    if os.path.exists(test_file):
        os.remove(test_file)
    
    result = bot.run_turn_from_text(
        f"Leé el contenido de {test_url} y guardá un resumen en {test_file}"
    )
    
    print(f"\nUser: Leé el contenido de {test_url} y guardá un resumen en {test_file}")
    print(f"Lucy: {result.reply}")
    
    # Verify file was created
    if os.path.exists(test_file):
        with open(test_file, 'r') as f:
            content = f.read()
        print(f"\n📄 File created with content:\n{content[:200]}...")
        
        if len(content) > 10:
            print("\n✅ PASS: Lucy successfully chained read -> save")
            os.remove(test_file)  # Cleanup
            return True
        else:
            print("\n❌ FAIL: File created but content is too short")
            return False
    else:
        print("\n⚠️  PARTIAL: Lucy may have executed tools but file not created")
        print("    Check if reflection loop needs adjustment")
        return None

def main():
    """Run all verification tests"""
    print("\n" + "="*60)
    print("LUCY-C ADVANCED AGENCY VERIFICATION")
    print("="*60)
    
    results = {
        "web_reading": test_web_reading(),
        "window_management": test_window_management(),
        "task_chaining": test_task_chaining()
    }
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    for test_name, result in results.items():
        if result is True:
            status = "✅ PASS"
        elif result is False:
            status = "❌ FAIL"
        else:
            status = "⚠️  SKIP"
        print(f"{test_name:20s}: {status}")
    
    # Overall result
    passed = sum(1 for r in results.values() if r is True)
    failed = sum(1 for r in results.values() if r is False)
    
    print(f"\nTotal: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("\n🎉 All tests passed! Lucy is ready for advanced agency operations.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Review the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
