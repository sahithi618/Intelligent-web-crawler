import os
import asyncio
import sys
from pathlib import Path
from pydantic_ai import Agent

# Setup path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env", override=True)

from fact_checker.llm import build_model

agent = Agent(
    name="TestAgentNoTool",
    model=build_model(),
    system_prompt="You are a helpful assistant. Return your response in JSON format: {'greeting': 'Hello'}"
)

async def test():
    print("Running test agent without output_type...")
    try:
        res = await agent.run("Hello there!")
        print("Attributes:", dir(res))
        if hasattr(res, "data"):
            print("res.data:", repr(res.data))
        if hasattr(res, "output"):
            print("res.output:", repr(res.output))
        if hasattr(res, "text"):
            print("res.text:", repr(res.text))
    except Exception as e:
        print("Exception:", e)

if __name__ == "__main__":
    asyncio.run(test())
