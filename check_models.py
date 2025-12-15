import httpx

def list_models():
    try:
        response = httpx.get("http://localhost:11434/api/tags")
        if response.status_code == 200:
            models = response.json().get('models', [])
            print("Available models:")
            for m in models:
                print(f"- {m['name']}")
        else:
            print(f"Failed to list models. Status: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_models()
