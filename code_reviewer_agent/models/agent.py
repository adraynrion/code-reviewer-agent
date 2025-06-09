"""Agent models and utilities."""

import os
from typing import Union

from crawl4ai import LLMConfig
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.providers.openrouter import OpenRouterProvider
from supabase import Client, create_client


def get_supabase() -> Client:
    """Initialize and return a Supabase client."""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")

    if not supabase_url or not supabase_key:
        raise ValueError(
            "SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in environment variables"
        )

    return create_client(supabase_url, supabase_key)


def get_embedding_model_str() -> str:
    """Get the embedding model string from environment variables."""
    return os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")


def get_model(as_llm_config: bool = False) -> Union[OpenAIModel, LLMConfig]:
    provider = os.getenv("PROVIDER", "OpenAI")
    llm = os.getenv("MODEL_CHOICE", "gpt-4.1-mini")
    base_url = os.getenv("BASE_URL", "https://api.openai.com/v1")
    api_key = os.getenv("LLM_API_KEY", "no-api-key-provided")

    if not as_llm_config:
        if provider == "OpenAI" or provider == "TogetherAI":
            return OpenAIModel(
                llm, provider=OpenAIProvider(base_url=base_url, api_key=api_key)
            )
        elif provider == "OpenRouter":
            return OpenAIModel(llm, provider=OpenRouterProvider(api_key=api_key))
        elif provider == "Google":
            return GoogleModel(llm, provider=GoogleProvider(api_key=api_key))
    else:
        if provider == "OpenAI":
            return LLMConfig(provider="openai/" + llm, api_token=api_key)
        elif provider == "TogetherAI":
            return LLMConfig(provider="together_ai/" + llm, api_token=api_key)
        elif provider == "OpenRouter":
            return LLMConfig(provider="openrouter/" + llm, api_token=api_key)
        elif provider == "Google":
            return LLMConfig(provider="gemini/" + llm, api_token=api_key)

    raise ValueError(f"Unsupported provider: {provider}")
