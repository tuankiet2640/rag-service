import openai
from typing import List
import os

class OpenAIProviderClient:
    def __init__(self, api_key: str, embedding_model: str = "text-embedding-ada-002", completion_model: str = "gpt-3.5-turbo"):
        self.api_key = api_key
        self.embedding_model = embedding_model
        self.completion_model = completion_model
        openai.api_key = api_key

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        # OpenAI's API is synchronous, so run in thread executor if needed
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._embed_texts_sync, texts)

    def _embed_texts_sync(self, texts: List[str]) -> List[List[float]]:
        # Ensure texts are strings - important for PDF processing
        texts = [str(text) if not isinstance(text, str) else text for text in texts]
        
        response = openai.embeddings.create(
            input=texts,
            model=self.embedding_model
        )
        # Fix: openai>=1.0 returns an object, not a dict
        return [item.embedding for item in response.data]

    async def complete(self, prompt: str, **kwargs) -> str:
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._complete_sync, prompt, kwargs)

    def _complete_sync(self, prompt: str, kwargs) -> str:
        response = openai.chat.completions.create(
            model=self.completion_model,
            messages=[{"role": "user", "content": prompt}],
            **kwargs
        )
        return response.choices[0].message.content.strip()
