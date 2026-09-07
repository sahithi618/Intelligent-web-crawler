import asyncio
import sys
from pathlib import Path

# Add backend to sys path
sys.path.insert(0, str(Path(__file__).parent))

from services.search_agent_service import SearchAgentService

async def main():
    query = "Find me remote Python developer jobs posted this week"
    print(f"Running pipeline for query: '{query}'")
    try:
        res = await SearchAgentService.run_pipeline(query)
        print("\n=== SUCCESS ===")
        print(f"Detected Intent: {res['intent']} (Confidence: {res['confidence_score']})")
        print(f"Synthesized Answer:\n{res['synthesized_answer']}")
        print(f"Action Prompt: {res['action_prompt']}")
        print(f"Jobs Count: {len(res['jobs'])}")
        if res['jobs']:
            print(f"First Job Listing: {res['jobs'][0]['title']} at {res['jobs'][0]['company']}")
        print(f"Citations Count: {len(res['sources'])}")
    except Exception as e:
        print(f"\n=== FAILURE ===")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
