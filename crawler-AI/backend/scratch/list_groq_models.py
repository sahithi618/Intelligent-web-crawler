import os
import requests
from dotenv import load_dotenv

load_dotenv(dotenv_path="../.env", override=True)

def main():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("GROQ_API_KEY not found in environment or .env!")
        return
        
    url = "https://api.groq.com/openai/v1/models"
    headers = {"Authorization": f"Bearer {api_key}"}
    
    try:
        res = requests.get(url, headers=headers)
        print("Status Code:", res.status_code)
        if res.status_code == 200:
            models_data = res.json().get("data", [])
            print("Available models:")
            for m in models_data:
                print(f"  - {m['id']}")
        else:
            print("Error response:", res.json())
    except Exception as e:
        print("Error connecting to Groq:", e)

if __name__ == "__main__":
    main()
