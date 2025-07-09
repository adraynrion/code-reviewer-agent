from pydantic_ai.models.google import GoogleModel
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers import Provider
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.providers.openrouter import OpenRouterProvider

from code_reviewer_agent.models.base_types import LLM, ApiKey, BaseUrl, ModelProvider


class ProviderFactory:
    """Factory for creating AI model providers.

    This factory implements the Factory pattern to create different AI model providers
    without exposing the creation logic to clients. Following the Open/Closed Principle,
    new providers can be added without modifying existing code.

    """

    @staticmethod
    def create_provider(
        provider_type: ModelProvider,
        api_key: ApiKey,
        base_url: BaseUrl | None = None,
    ) -> Provider:
        """Create a provider based on the provider type.

        Args:
            provider_type: The type of provider to create
            api_key: The API key for the provider
            base_url: The base URL (optional, for OpenAI/TogetherAI)

        Returns:
            A configured provider instance

        Raises:
            ValueError: If the provider type is not supported

        """
        if provider_type not in (
            "OpenAI",
            "TogetherAI",
            "OpenRouter",
            "Google",
            "Ollama",
        ):
            raise ValueError(
                "Provider must be one of: OpenAI, TogetherAI, OpenRouter, Google, Ollama"
            )

        if provider_type == "OpenAI" or provider_type == "TogetherAI":
            if not base_url:
                raise ValueError(f"Base URL is required for {provider_type}")
            return OpenAIProvider(base_url=base_url, api_key=api_key)
        elif provider_type == "OpenRouter":
            return OpenRouterProvider(api_key=api_key)
        elif provider_type == "Google":
            return GoogleProvider(api_key=api_key)
        else:
            raise ValueError(f"Unsupported provider type: {provider_type}")

    @staticmethod
    def create_model(
        llm: LLM,
        provider: Provider,
        provider_type: ModelProvider,
    ) -> OpenAIModel | GoogleModel:
        """Create a model based on the provider type.

        Args:
            llm: The LLM model name
            provider: The configured provider
            provider_type: The type of provider

        Returns:
            A configured model instance

        Raises:
            ValueError: If the provider type is not supported

        """
        if provider_type in ("OpenAI", "TogetherAI", "OpenRouter"):
            return OpenAIModel(
                model_name=llm,
                provider=provider,
            )
        elif provider_type == "Google":
            return GoogleModel(
                model_name=llm,
                provider=provider,
            )
        else:
            raise ValueError(f"Unsupported provider type: {provider_type}")
