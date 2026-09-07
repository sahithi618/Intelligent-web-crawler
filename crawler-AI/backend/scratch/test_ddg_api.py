import sys
import traceback
from duckduckgo_search import DDGS

def main():
    print("duckduckgo_search version:")
    try:
        import duckduckgo_search
        print(duckduckgo_search.__version__)
    except Exception as e:
        print(e)

    print("\nInspecting DDGS class:")
    try:
        d = DDGS()
        print("Available methods/attributes in DDGS:")
        print([attr for attr in dir(d) if not attr.startswith("_")])
    except Exception as e:
        traceback.print_exc()

    print("\nTrying basic searches with different backends:")
    backends = ["auto", "api", "html", "lite"]
    for backend in backends:
        print(f"\n--- Testing backend: '{backend}' ---")
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text("python programming", backend=backend, max_results=3))
                print(f"Backend '{backend}' got {len(results)} results:")
                for r in results:
                    print(" -", r.get("title"), r.get("href"))
        except Exception as e:
            print(f"Backend '{backend}' raised error:")
            traceback.print_exc()

    print("\nTrying with a different user agent/headers or parameters:")
    try:
        with DDGS() as ddgs:
            # Check what parameters text() takes
            import inspect
            print("ddgs.text signature:", inspect.signature(ddgs.text))
    except Exception as e:
        traceback.print_exc()

if __name__ == "__main__":
    main()
