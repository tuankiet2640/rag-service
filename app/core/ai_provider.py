# Abstraction for dispatching queries to different AI providers
from app.models.schemas import QueryRequest, QueryResponse

from app.core.providers.openai_provider import OpenAIProviderClient

def dispatch_query(request: QueryRequest, provider=None) -> QueryResponse:
    # Flexible dispatch based on provider type
    if provider and provider.type == "openai":
        # Use OpenAI for LLM completion
        client = OpenAIProviderClient(
            api_key=provider.api_key,
            completion_model=provider.config_json or "gpt-3.5-turbo"
        )
        # For now, just use the query as the prompt
        import asyncio
        answer = asyncio.run(client.complete(request.query))
        return QueryResponse(
            answer=answer,
            citations=[],
            provider=provider.name
        )
    # Default stub for other providers
    provider_name = provider.name if provider else (request.ai_provider or "default")
    return QueryResponse(
        answer=f"[Stub] Answer for '{request.query}' from KB '{request.knowledge_base_id}' via provider '{provider_name}'",
        citations=[],
        provider=provider_name
    )
