import os
from typing import Optional, Dict, Any

class ProviderManager:
    """
    Loads and manages LLM/embedding provider configuration from environment variables.
    Supports dynamic instantiation of any provider (OpenAI, Azure, Ollama, Cohere, Anthropic, etc.).
    """
    def __init__(self):
        self.providers = {}
        self.provider_registry = {
            "openai": self._instantiate_openai,
            "azure": self._instantiate_azure,
            "ollama": self._instantiate_ollama,
            "cohere": self._instantiate_cohere,
            "anthropic": self._instantiate_anthropic,
        }
        self.load_providers()

    def load_providers(self):
        # OpenAI
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            self.providers["openai"] = {
                "api_key": openai_key,
                "api_type": os.getenv("OPENAI_API_TYPE", "openai"),
                "embedding_model": os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-ada-002"),
                "completion_model": os.getenv("OPENAI_COMPLETION_MODEL", "gpt-3.5-turbo")
            }
        # Azure OpenAI
        azure_key = os.getenv("AZURE_OPENAI_API_KEY")
        if azure_key:
            self.providers["azure"] = {
                "api_key": azure_key,
                "endpoint": os.getenv("AZURE_OPENAI_ENDPOINT"),
                "embedding_model": os.getenv("AZURE_OPENAI_EMBEDDING_MODEL"),
                "completion_model": os.getenv("AZURE_OPENAI_COMPLETION_MODEL")
            }
        # Ollama (local)
        ollama_host = os.getenv("OLLAMA_HOST")
        if ollama_host:
            self.providers["ollama"] = {
                "host": ollama_host,
                "model": os.getenv("OLLAMA_MODEL", "llama2")
            }
        # Cohere
        cohere_key = os.getenv("COHERE_API_KEY")
        if cohere_key:
            self.providers["cohere"] = {
                "api_key": cohere_key,
                "embedding_model": os.getenv("COHERE_EMBEDDING_MODEL", "embed-english-v3.0"),
                "completion_model": os.getenv("COHERE_COMPLETION_MODEL", "command-r-plus")
            }
        # Anthropic
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            self.providers["anthropic"] = {
                "api_key": anthropic_key,
                "completion_model": os.getenv("ANTHROPIC_COMPLETION_MODEL", "claude-3-opus-20240229")
            }

    def get_provider_config(self, name: str) -> Optional[dict]:
        return self.providers.get(name)

    def get_available_providers(self):
        return list(self.providers.keys())

    def get_provider_client(self, name: str):
        """
        Dynamically instantiate and return the provider client for the given provider name.
        Raises a descriptive error if the provider is not configured in the environment.
        """
        if name not in self.provider_registry:
            raise ValueError(f"Provider '{name}' is not supported. Please check your provider name.")
        config = self.get_provider_config(name)
        if not config:
            raise RuntimeError(
                f"Provider '{name}' is not configured in your environment variables. "
                f"Please set the required environment variables for this provider (see .env.example)."
            )
        return self.provider_registry[name](config)

    def _instantiate_openai(self, config: Dict[str, Any]):
        from app.core.providers.openai_provider import OpenAIProviderClient
        return OpenAIProviderClient(
            api_key=config["api_key"],
            embedding_model=config.get("embedding_model", "text-embedding-ada-002"),
            completion_model=config.get("completion_model", "gpt-3.5-turbo")
        )

    def _instantiate_azure(self, config: Dict[str, Any]):
        from app.core.providers.azure_openai_provider import AzureOpenAIProviderClient
        return AzureOpenAIProviderClient(
            api_key=config["api_key"],
            endpoint=config["endpoint"],
            embedding_model=config["embedding_model"],
            completion_model=config["completion_model"]
        )

    def _instantiate_ollama(self, config: Dict[str, Any]):
        from app.core.providers.ollama_provider import OllamaProviderClient
        return OllamaProviderClient(
            host=config["host"],
            model=config.get("model", "llama2")
        )

    def _instantiate_cohere(self, config: Dict[str, Any]):
        from app.core.providers.cohere_provider import CohereProviderClient
        return CohereProviderClient(
            api_key=config["api_key"],
            embedding_model=config.get("embedding_model", "embed-english-v3.0"),
            completion_model=config.get("completion_model", "command-r-plus")
        )

    def _instantiate_anthropic(self, config: Dict[str, Any]):
        from app.core.providers.anthropic_provider import AnthropicProviderClient
        return AnthropicProviderClient(
            api_key=config["api_key"],
            completion_model=config.get("completion_model", "claude-3-opus-20240229")
        )
