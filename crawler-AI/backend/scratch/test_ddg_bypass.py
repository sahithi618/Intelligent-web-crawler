import asyncio
from duckduckgo_search import DDGS

async def test_bypass():
    q = "remote python developer"
    print(f"Testing direct _text_html and _text_lite bypass for: '{q}'")
    
    with DDGS() as ddgs:
        # 1. Test direct _text_html
        print("\n--- Testing direct _text_html ---")
        try:
            results = ddgs._text_html(q, max_results=5)
            print(f"Got {len(results)} results.")
            for idx, r in enumerate(results[:2]):
                print(f"  {idx+1}. {r.get('title')} ({r.get('href')})")
        except Exception as e:
            print("Error in _text_html:", e)
            
        # 2. Test direct _text_lite
        print("\n--- Testing direct _text_lite ---")
        try:
            results = ddgs._text_lite(q, max_results=5)
            print(f"Got {len(results)} results.")
            for idx, r in enumerate(results[:2]):
                print(f"  {idx+1}. {r.get('title')} ({r.get('href')})")
        except Exception as e:
            print("Error in _text_lite:", e)

if __name__ == "__main__":
    asyncio.run(test_bypass())
