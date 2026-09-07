import asyncio
from duckduckgo_search import DDGS

async def test_ddg():
    queries = [
        "remote software engineer",
        "programming jobs",
        "write python code"
    ]
    
    print("Testing DDGS with reused session")
    try:
        with DDGS() as ddgs:
            for q in queries:
                print(f"\nSearching for: '{q}'")
                try:
                    results = list(ddgs.text(q, backend='api', max_results=5))
                    print(f"Got {len(results)} results.")
                    for idx, r in enumerate(results[:2]):
                        print(f"  {idx+1}. {r.get('title')} ({r.get('href')})")
                except Exception as e:
                    print("Error:", e)
    except Exception as e:
        print("Error during DDG search:", e)

if __name__ == "__main__":
    asyncio.run(test_ddg())
