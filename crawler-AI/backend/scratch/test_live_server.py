import requests

def test():
    url = "http://localhost:8000/detect/analyze"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer test-token" # Wait, auth_routes expects user token, let's see how auth works.
    }
    
    # Wait, instead of calling a protected route directly without a token, 
    # let's just fetch the docs or root to see if the server is up!
    try:
        res = requests.get("http://localhost:8000/", timeout=3)
        print("Root Status Code:", res.status_code)
        print("Root Response:", res.text)
    except Exception as e:
        print("Error connecting to root:", e)
        
    try:
        res = requests.get("http://localhost:8000/docs", timeout=3)
        print("Docs Status Code:", res.status_code)
    except Exception as e:
        print("Error connecting to docs:", e)

if __name__ == "__main__":
    test()
