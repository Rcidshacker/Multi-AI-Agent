import httpx
import json
import sys

def pull_model():
    print("Attempting to pull llama3.1 via API (since CLI is unavailable)...")
    url = "http://localhost:11434/api/pull"
    data = {"name": "llama3.1", "stream": True}
    
    try:
        with httpx.stream("POST", url, json=data, timeout=None) as response:
            if response.status_code != 200:
                print(f"Failed to connect to Ollama API. Status: {response.status_code}")
                return

            for line in response.iter_lines():
                if line:
                    try:
                        json_response = json.loads(line)
                        if "status" in json_response:
                            # Print status, avoiding too much spam
                            status = json_response['status']
                            completed = json_response.get('completed', 0)
                            total = json_response.get('total', 1)
                            if total > 0 and 'completed' in json_response:
                                percent = (completed / total) * 100
                                sys.stdout.write(f"\r{status}: {percent:.1f}%")
                            else:
                                sys.stdout.write(f"\r{status}               ")
                    except Exception:
                        pass
        print("\nPull complete! You can now run the main script.")
        
    except Exception as e:
        print(f"\nError: {e}")
        print("Please ensure Ollama is running in the background.")

if __name__ == "__main__":
    pull_model()
