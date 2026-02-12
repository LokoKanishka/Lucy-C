#!/usr/bin/env python3
"""Simple web search test"""
import sys
sys.path.insert(0, '/home/lucy-ubuntu/Lucy-C')

from lucy_c.tools.web_tools import tool_web_search

queries = ["Python tutorials", "AI news", "Weather forecast"]

print("=== Web Search Test ===\n")
for q in queries:
    print(f"Searching: {q}")
    result = tool_web_search([q], None)
    if result.success:
        print(f"✅ {result.output[:100]}...")
    else:
        print(f"❌ {result.output}")
    print()
