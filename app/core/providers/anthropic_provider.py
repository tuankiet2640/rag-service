import anthropic
from typing import List
import os

class AnthropicProviderClient:
    def __init__(self, api_key: str, completion_model: str = "claude-3-opus-20240229"):
        self.api_key = api_key
        self.completion_model = completion_model
        self.client = anthropic.Anthropic(api_key=api_key)

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        # Anthropic does not (yet) provide embeddings as of 2024-04
        raise NotImplementedError("Anthropic does not support embeddings yet.")

    async def complete(self, prompt: str, **kwargs) -> str:
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._complete_sync, prompt, kwargs)

    def _complete_sync(self, prompt: str, kwargs) -> str:
        response = self.client.messages.create(
            model=self.completion_model,
            max_tokens=kwargs.get("max_tokens", 512),
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text.strip() if response.content else ""
