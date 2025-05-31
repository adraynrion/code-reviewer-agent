import os

from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.models.google import GoogleModel

from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.providers.openrouter import OpenRouterProvider
from pydantic_ai.providers.google import GoogleProvider

def get_model():
    provider = os.getenv('PROVIDER', 'OpenAI')
    llm = os.getenv('MODEL_CHOICE', 'gpt-4.1-mini')
    base_url = os.getenv('BASE_URL', 'https://api.openai.com/v1')
    api_key = os.getenv('LLM_API_KEY', 'no-api-key-provided')

    if provider == 'OpenAI' or provider == 'TogetherAI':
        return OpenAIModel(llm, provider=OpenAIProvider(base_url=base_url, api_key=api_key))
    elif provider == 'OpenRouter':
        return OpenAIModel(llm, provider=OpenRouterProvider(api_key=api_key))
    elif provider == 'Google':
        return GoogleModel(llm, provider=GoogleProvider(api_key=api_key))
