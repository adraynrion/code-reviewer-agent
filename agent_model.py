import os

from crawl4ai import LLMConfig

from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.models.google import GoogleModel

from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.providers.openrouter import OpenRouterProvider
from pydantic_ai.providers.google import GoogleProvider

from supabase import create_client

def get_model(as_llm_config: bool = False):
    provider = os.getenv("PROVIDER", "OpenAI")
    llm = os.getenv("MODEL_CHOICE", "gpt-4.1-mini")
    base_url = os.getenv("BASE_URL", "https://api.openai.com/v1")
    api_key = os.getenv("LLM_API_KEY", "no-api-key-provided")

    if not as_llm_config:
        if provider == "OpenAI" or provider == "TogetherAI":
            return OpenAIModel(llm, provider=OpenAIProvider(base_url=base_url, api_key=api_key))
        elif provider == "OpenRouter":
            return OpenAIModel(llm, provider=OpenRouterProvider(api_key=api_key))
        elif provider == "Google":
            return GoogleModel(llm, provider=GoogleProvider(api_key=api_key))
    else:
        if provider == "OpenAI":
            return LLMConfig(
                provider="openai/" + llm,
                api_token=api_key
            )
        elif provider == "TogetherAI":
            return LLMConfig(
                provider="together_ai/" + llm,
                api_token=api_key
            )
        elif provider == "OpenRouter":
            return LLMConfig(
                provider="openrouter/" + llm,
                api_token=api_key
            )
        elif provider == "Google":
            return LLMConfig(
                provider="gemini/" + llm,
                api_token=api_key
            )

def get_embedding_model_str() -> str:
    embedding_llm = os.getenv("EMBEDDING_MODEL_CHOICE", "text-embedding-ada-002")
    return embedding_llm

def get_supabase():
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
