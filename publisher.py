import requests

def publish_to_devto(title: str, markdown_content: str, tags: list = None):
    # 1. Configuration
    API_KEY = "z1YMMMKuKwLMA3Gbf85mpYWA" 
    URL = "https://dev.to/api/articles"
    
    # 2. Prepare the payload
    # Dev.to requires a specific JSON structure
    headers = {
        "api-key": API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "article": {
            "title": title,
            "body_markdown": markdown_content,
            "published": False,  # Set to True to publish immediately, False for Draft
            "tags": tags or ["ai", "python", "tech"],
            "series": "AI Agents 101"
        }
    }
    
    # 3. Send Request
    try:
        response = requests.post(URL, json=payload, headers=headers)
        if response.status_code == 201:
            print("✅ Successfully published to Dev.to!")
            return response.json()['url']
        else:
            print(f"❌ Error publishing: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return None
