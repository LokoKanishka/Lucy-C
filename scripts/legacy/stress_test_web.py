#!/usr/bin/env python3
"""
Enhanced web search stress test with timing and rate limiting
"""
import sys
import time
sys.path.insert(0, '/home/lucy-ubuntu/Lucy-C')

from lucy_c.tools.web_tools import tool_web_search

# More diverse queries
queries = [
    "Python programming tutorial",
    "Latest artificial intelligence news",
    "Ubuntu Linux tips",
    "How to learn machine learning",
    "Best practices for web development"
]

print("=== 🌐 Web Search Stress Test ===\n")
print(f"Testing {len(queries)} queries with proper rate limiting...\n")

results = {"success": 0, "failed": 0, "empty": 0}
total_time = 0

for i, query in enumerate(queries, 1):
    print(f"[{i}/{len(queries)}] Searching: '{query}'")
    
    start = time.time()
    result = tool_web_search([query], None)
    elapsed = time.time() - start
    total_time += elapsed
    
    if result.success:
        if "No encontré resultados" in result.output:
            print(f"  ⚠️  EMPTY ({elapsed:.2f}s) - No results from DuckDuckGo")
            results["empty"] += 1
        else:
            print(f"  ✅ SUCCESS ({elapsed:.2f}s)")
            print(f"     Preview: {result.output[:80]}...")
            results["success"] += 1
    else:
        print(f"  ❌ FAILED ({elapsed:.2f}s) - {result.output}")
        results["failed"] += 1
    
    # Rate limiting - wait between requests
    if i < len(queries):
        time.sleep(2)

print("\n" + "="*60)
print(f"📊 Results Summary:")
print(f"   ✅ Successful: {results['success']}")
print(f"   ⚠️  Empty: {results['empty']}")
print(f"   ❌ Failed: {results['failed']}")
print(f"   ⏱️  Average time: {total_time/len(queries):.2f}s")
print(f"   🕐 Total time: {total_time:.2f}s")
print("="*60)

if results['success'] > 0:
    print("\n✅ Web search is functional!")
else:
    print("\n⚠️  All searches failed or returned empty")
