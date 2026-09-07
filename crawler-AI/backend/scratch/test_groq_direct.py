import os
import requests
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env", override=True)

def test():
    api_key = os.getenv("GROQ_API_KEY")
    print("GROQ_API_KEY:", repr(api_key))
    if not api_key:
        print("No API Key")
        return
        
    api_key = api_key.strip()
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "user", "content": "Hello"}],
        "max_tokens": 10
    }
    
    print("Sending request to Groq...")
    try:
        res = requests.post(url, headers=headers, json=data, timeout=10)
        print("Status Code:", res.status_code)
        print("Response:", res.text)
    except Exception as e:
        print("Exception:", e)

if __name__ == "__main__":
    test()
