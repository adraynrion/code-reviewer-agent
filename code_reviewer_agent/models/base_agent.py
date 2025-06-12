"""Agent models and utilities."""

from typing import Union

from crawl4ai import LLMConfig
from pydantic_ai.models import Model
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.providers.openrouter import OpenRouterProvider
from supabase import Client, create_client

from code_reviewer_agent.config.config import config


def get_model(as_llm_config: bool = False) -> Union[Model, LLMConfig]:
    provider = config.reviewer.llm.provider
    llm = config.reviewer.llm.model_name
    api_key = config.reviewer.llm.api_key

    if not as_llm_config:
        if provider == "OpenAI" or provider == "TogetherAI":
            return OpenAIModel(
                llm,
                provider=OpenAIProvider(
                    base_url=config.reviewer.llm.base_url, api_key=api_key
                ),
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


def get_supabase() -> Client:
    """Initialize and return a Supabase client."""
    return create_client(config.supabase.url, config.supabase.key)
