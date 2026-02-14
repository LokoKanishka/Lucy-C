#!/usr/bin/env python3
"""
Stress test for web search functionality in Lucy-C
Tests that web_search tool can actually search the internet
"""

import sys
import time
from lucy_c.tools.web_tools import tool_web_search
from lucy_c.tool_router import ToolResult

print("=== Web Search Stress Test ===\n")

# Test queries
test_queries = [
    "Python programming tutorials 2024",
    "Latest AI news",
    "Weather Buenos Aires",
    "Ubuntu 24.04 installation guide",
    "NVIDIA RTX 5090 specs",
]

print(f"Testing {len(test_queries)} search queries...\n")

passed = 0
failed = 0

for i, query in enumerate(test_queries, 1):
    print(f"[{i}/{len(test_queries)}] Searching: '{query}'")
    
    start_time = time.time()
    
    try:
        # Call the tool
        result = tool_web_search([query], None)
        
        elapsed = time.time() - start_time
        
        if isinstance(result, ToolResult) and result.success:
            print(f"  ✅ SUCCESS ({elapsed:.2f}s)")
            print(f"     Result preview: {result.output[:100]}...")
            passed += 1
        else:
            print(f"  ❌ FAILED ({elapsed:.2f}s)")
            print(f"     Error: {result.output if isinstance(result, ToolResult) else result}")
            failed += 1
            
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"  ❌ EXCEPTION ({elapsed:.2f}s)")
        print(f"     {type(e).__name__}: {e}")
        failed += 1
    
    print()
    time.sleep(0.5)  # Small delay between requests

print("\n" + "="*50)
print(f"Results: {passed} passed, {failed} failed")
print("="*50)

if failed > 0:
    print("\n⚠️  Web search has issues!")
    sys.exit(1)
else:
    print("\n✅ All web searches working!")
    sys.exit(0)
