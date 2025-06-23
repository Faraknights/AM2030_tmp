import requests

def query_model_ollama(model_name: str, prompt: str) -> str:
    url = "http://localhost:11434/api/generate"
    payload = {Z
        "model": model_name,
        "prompt": prompt,
        "stream": False
    }

    response = requests.post(url, json=payload)
    response.raise_for_status()

    return response.json()["response"]


# Example usage
if __name__ == "__main__":
    model = "COM"  # Replace with your model name
    prompt = "Get me a pizza"
    result = query_model_ollama(model, prompt)
    print("✅ Model response:", result)
