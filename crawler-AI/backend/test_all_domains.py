import asyncio
import sys
from pathlib import Path

# Add backend to sys path
sys.path.insert(0, str(Path(__file__).parent))

from services.search_agent_service import SearchAgentService

async def run_query(query: str):
    print("\n" + "="*80)
    print(f"RUNNING PIPELINE FOR QUERY: '{query}'")
    print("="*80)
    try:
        res = await SearchAgentService.run_pipeline(query)
        print(f"Detected Intent: {res['intent']} (Confidence: {res['confidence_score']})")
        print(f"Synthesized Answer:\n{res['synthesized_answer']}")
        print(f"Key Highlights: {res['key_points']}")
        print(f"Jobs Count: {len(res.get('jobs', []))}")
        if res.get('jobs'):
            print(f"First Job Listing: {res['jobs'][0]['title']} at {res['jobs'][0]['company']}")
        print(f"Products Count: {len(res.get('products', []))}")
        if res.get('products'):
            print(f"First Product: {res['products'][0]['name']} - {res['products'][0]['price']}")
        print(f"Events Count: {len(res.get('events', []))}")
        if res.get('events'):
            print(f"First Event: {res['events'][0]['name']} at {res['events'][0]['location']}")
        print(f"Sources Count: {len(res['sources'])}")
    except Exception as e:
        import traceback
        traceback.print_exc()

async def main():
    queries = [
        "Find remote Python developer jobs posted this week.",
        "Find AI hackathons happening this month in Hyderabad.",
        "What is the best budget mechanical keyboard right now?"
    ]
    for q in queries:
        await run_query(q)

if __name__ == "__main__":
    asyncio.run(main())
