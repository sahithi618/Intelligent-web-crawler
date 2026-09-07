#!/usr/bin/env python3
"""
Full pipeline test - simulates what happens when calling the backend
"""

import sys
import asyncio
from pathlib import Path

backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from services.search_agent_service import SearchAgentService

async def test_search_pipeline():
    """Test the complete search pipeline with time-filtered job query"""
    
    query = "Find me remote Python developer jobs posted this week"
    
    print("\n" + "=" * 80)
    print("[SEARCH] TESTING FULL SEARCH PIPELINE WITH TIME-FILTER QUERY")
    print("=" * 80)
    print(f"\n[Query]: {query}\n")
    
    try:
        print("[Status] Running search pipeline... (this may take 10-15 seconds)")
        print("-" * 80)
        
        result = await SearchAgentService.run_pipeline(query)
        
        print("\n[Status] PIPELINE COMPLETE!\n")
        print("=" * 80)
        print("[RESULTS SUMMARY]")
        print("=" * 80)
        
        print(f"\n[1] INTENT CLASSIFICATION:")
        print(f"   Intent: {result['intent'].upper()}")
        confidence = result['confidence_score']
        if isinstance(confidence, str):
            print(f"   Confidence: {confidence}")
        else:
            print(f"   Confidence: {confidence:.0%}")
        
        print(f"\n[2] KEY CLAIM:")
        print(f"   {result['key_claim']}")
        print(f"   Verdict: {result['key_claim_verdict']}")
        
        print(f"\n[3] SUMMARY:")
        print(f"   {result['summary']}")
        
        print(f"\n[4] JOBS FOUND: {len(result.get('jobs', []))}")
        if result.get('jobs'):
            for i, job in enumerate(result['jobs'][:5], 1):
                print(f"\n   Job #{i}:")
                if isinstance(job, dict):
                    print(f"      Title: {job.get('title', 'N/A')}")
                    print(f"      Company: {job.get('company', 'N/A')}")
                    print(f"      Location: {job.get('location', 'N/A')}")
                    print(f"      Salary: {job.get('salary_range', 'N/A')}")
                    print(f"      Score: {job.get('match_score', 'N/A')}")
                    print(f"      URL: {job.get('apply_url', 'N/A')[:60]}...")
                else:
                    print(f"      {job}")
        else:
            print("   [Note] No jobs found - checking if web search needs to be enabled")
        
        print(f"\n[5] SOURCES USED: {len(result.get('sources', []))}")
        if result.get('sources'):
            for i, source in enumerate(result['sources'][:3], 1):
                title = source.get('title', 'N/A')[:60]
                url = source.get('url', 'N/A')[:60]
                print(f"   {i}. {title}")
                print(f"      {url}")
        
        print(f"\n[6] ACTION PROMPT:")
        print(f"   {result['action_prompt']}\n")
        
        print("=" * 80)
        
    except Exception as e:
        print(f"\n[ERROR] ERROR during pipeline: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_search_pipeline())
