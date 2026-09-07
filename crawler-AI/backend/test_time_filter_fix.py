#!/usr/bin/env python3
"""
Quick test to verify the time-filter query fix works
"""

import sys
from pathlib import Path

backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(backend_path / "services"))

from services.intent_classifier import IntentClassifier

# Test the problematic query
test_queries = [
    "Find me remote Python developer jobs posted this week",
    "python jobs this week",
    "remote jobs last 7 days",
    "hiring python developers this month",
]

print("=" * 70)
print("TESTING TIME-FILTER JOB QUERY FIX")
print("=" * 70)

for query in test_queries:
    print(f"\n[Query]: {query}")
    print("-" * 70)
    
    result = IntentClassifier.fallback_classify(query)
    
    print(f"[Intent]: {result.intent}")
    print(f"[Confidence]: {result.confidence:.2f}")
    print(f"[Keywords]: {result.keywords}")
    print(f"[Suggested Search Queries]:")
    for i, sq in enumerate(result.suggested_queries, 1):
        print(f"  {i}. {sq}")

print("\n" + "=" * 70)
print("✅ If you see time-filter keywords (this week, 7 days ago, etc)")
print("   preserved in the suggested queries, the fix is working!")
print("=" * 70)
