import requests

def query_ollama(prompt):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "google/gemma-4-e2b-it",
            "prompt": prompt,
            "stream": False
        }
    )

    return response.json()["response"]