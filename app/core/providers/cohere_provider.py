import cohere
from typing import List
import os

class CohereProviderClient:
    def __init__(self, api_key: str, embedding_model: str = "embed-english-v3.0", completion_model: str = "command-r-plus"):
        self.api_key = api_key
        self.embedding_model = embedding_model
        self.completion_model = completion_model
        self.client = cohere.Client(api_key)

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._embed_texts_sync, texts)

    def _embed_texts_sync(self, texts: List[str]) -> List[List[float]]:
        response = self.client.embed(texts=texts, model=self.embedding_model)
        return response.embeddings

    async def complete(self, prompt: str, **kwargs) -> str:
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._complete_sync, prompt, kwargs)

    def _complete_sync(self, prompt: str, kwargs) -> str:
        response = self.client.generate(
            prompt=prompt,
            model=self.completion_model,
            max_tokens=kwargs.get("max_tokens", 512)
        )
        return response.generations[0].text.strip()
