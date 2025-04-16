import openai
from typing import List
import os

class AzureOpenAIProviderClient:
    def __init__(self, api_key: str, endpoint: str, embedding_model: str, completion_model: str):
        self.api_key = api_key
        self.endpoint = endpoint.rstrip("/")
        self.embedding_model = embedding_model
        self.completion_model = completion_model
        openai.api_key = api_key
        openai.api_base = endpoint
        

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._embed_texts_sync, texts)

    def _embed_texts_sync(self, texts: List[str]) -> List[List[float]]:
        # Ensure texts are strings - important for PDF processing
        texts = [str(text) if not isinstance(text, str) else text for text in texts]
        
        # For Azure OpenAI, we need to use the deployment name as the engine
        response = openai.Embedding.create(
            input=texts,
            engine=self.embedding_model
        )
        
        # Azure returns data in a different format
        return [item["embedding"] for item in response["data"]]

    async def complete(self, prompt: str, **kwargs) -> str:
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._complete_sync, prompt, kwargs)

    def _complete_sync(self, prompt: str, kwargs) -> str:
        response = openai.ChatCompletion.create(
            engine=self.completion_model,
            messages=[{"role": "user", "content": prompt}],
            **kwargs
        )
        return response["choices"][0]["message"]["content"].strip()
