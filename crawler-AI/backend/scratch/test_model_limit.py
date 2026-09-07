import os
from pydantic_ai import Agent
from pydantic_ai.models.groq import GroqModel
from dotenv import load_dotenv

load_dotenv(dotenv_path="../.env", override=True)

def main():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("GROQ_API_KEY not found!")
        return
        
    print("Initializing GroqModel with llama-3.1-8b-instant...")
    from pydantic_ai.providers.groq import GroqProvider
    model = GroqModel(
        "llama-3.1-8b-instant",
        provider=GroqProvider(api_key=api_key)
    )
    
    agent = Agent(
        model=model,
        system_prompt="You are a helpful assistant."
    )
    
    try:
        print("Running prompt...")
        result = agent.run_sync("Say hello!")
        print("Result:", result.data)
    except Exception as e:
        print("Error during run:", e)

if __name__ == "__main__":
    main()
