import requests
from typing import List

class OllamaProviderClient:
    def __init__(self, host: str, model: str = "llama2"):
        self.host = host.rstrip("/")
        self.model = model

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        # Ollama doesn't natively support embeddings yet; this is a placeholder
        # You would need to add your own embedding logic or call a compatible endpoint
        raise NotImplementedError("Ollama embedding not implemented. Use OpenAI or another provider.")

    async def complete(self, prompt: str, **kwargs) -> str:
        # Call Ollama's completion endpoint
        url = f"{self.host}/api/generate"
        payload = {"model": self.model, "prompt": prompt}
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        return data.get("response", "")
