from pydantic_ai.models.google import GoogleModel
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers import Provider

from code_reviewer_agent.config.config import Config
from code_reviewer_agent.models.base_types import LLM, ApiKey, BaseUrl, ModelProvider
from code_reviewer_agent.models.provider_factory import ProviderFactory
from code_reviewer_agent.models.pydantic_config_models import LLMConfig
from code_reviewer_agent.models.supabase import SupabaseModel


class LLMDict:
    _config: LLMConfig

    def __init__(self, config: LLMConfig) -> None:
        self._config = config

    @property
    def config(self) -> LLMConfig:
        return self._config

    @config.setter
    def config(self, config: LLMConfig) -> None:
        if config.temperature is not None:
            self._config.temperature = config.temperature
        if config.max_tokens is not None:
            self._config.max_tokens = config.max_tokens
        if config.top_p is not None:
            self._config.top_p = config.top_p
        if config.max_attempts is not None:
            self._config.max_attempts = config.max_attempts

    @property
    def temperature(self) -> float:
        return self._config.temperature

    @property
    def max_tokens(self) -> int:
        return self._config.max_tokens

    @property
    def top_p(self) -> float:
        return self._config.top_p

    @property
    def max_attempts(self) -> int:
        return self._config.max_attempts


class AiModel:
    """Base class for AI model configuration and management.

    This class handles AI model configuration with separated concerns:
    - Configuration management (single responsibility)
    - Provider creation (delegated to factory)
    - Model creation (delegated to factory)

    """

    def __init__(self, config: Config) -> None:
        self._config = config
        self._debug = config.schema.logging.debug

        # Extract configuration values
        llm = config.schema.reviewer.llm
        self._api_key = ApiKey(llm.api_key)
        self._base_url = BaseUrl(llm.base_url)
        self._provider_type = ModelProvider(llm.provider)
        self._llm = LLM(llm.model_name)

        # Setup provider and model using factory
        self._setup_provider_and_model()

        # Initialize other components
        self._llm_config = LLMDict(llm)
        self.supabase = SupabaseModel(config)

    def _setup_provider_and_model(self) -> None:
        """Setup provider and model using factory pattern."""
        # Validate required configuration
        if not self._base_url or not self._api_key:
            raise ValueError("Base URL and API key must be set before provider")

        # Create provider using factory
        self._provider = ProviderFactory.create_provider(
            self._provider_type,
            self._api_key,
            self._base_url if self._provider_type in ("OpenAI", "TogetherAI") else None,
        )

        # Create model using factory
        self._model = ProviderFactory.create_model(
            self._llm,
            self._provider,
            self._provider_type,
        )

    @property
    def debug(self) -> bool:
        return self._debug

    @property
    def api_key(self) -> ApiKey:
        return self._api_key

    @property
    def base_url(self) -> BaseUrl:
        return self._base_url

    @property
    def provider(self) -> Provider:
        """Get the AI provider."""
        return self._provider

    @property
    def llm(self) -> LLM:
        """Get the LLM model name."""
        return self._llm

    @property
    def model(self) -> OpenAIModel | GoogleModel:
        """Get the AI model."""
        return self._model

    @property
    def llm_config(self) -> LLMDict:
        """Get the LLM configuration."""
        return self._llm_config


class AiModelType(type):
    def __new__(cls, name: str, bases: tuple, dct: dict) -> "AiModelType":
        inherit_from_AiModel = False
        for base in bases:
            if base is AiModel:
                inherit_from_AiModel = True
                break

        if not inherit_from_AiModel:
            raise TypeError(f"{name} must inherit from AiModel")

        return super().__new__(cls, name, bases, dct)
