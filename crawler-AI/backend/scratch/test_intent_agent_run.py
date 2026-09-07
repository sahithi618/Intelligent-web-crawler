import os
import asyncio
import sys
import logging
from pathlib import Path

# Setup path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env", override=True)

# Enable logging to see the HTTP requests/responses of pydantic-ai
logging.basicConfig(level=logging.DEBUG)

from services.intent_classifier import intent_classifier_agent

async def test():
    print("Running intent agent...")
    try:
        res = await intent_classifier_agent.run("Find me remote Python developer jobs posted this week")
        print("Success output:")
        print(res.output)
    except Exception as e:
        print("\n\nAgent run failed with exception:")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
