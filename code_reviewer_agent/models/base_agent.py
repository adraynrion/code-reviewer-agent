from pydantic_ai.models import Model
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.providers.openrouter import OpenRouterProvider

from code_reviewer_agent.config.config import Config
from code_reviewer_agent.models.base_types import StringValidator
from code_reviewer_agent.models.pydantic_config_models import LLMConfig
from code_reviewer_agent.models.supabase import SupabaseModel


class ApiKey(StringValidator):
    pass


class BaseUrl(StringValidator):
    pass


class ModelProvider(StringValidator):
    pass


class LLM(StringValidator):
    pass


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
    _debug: bool
    _api_key = ApiKey()
    _base_url = BaseUrl()
    _provider = ModelProvider()
    _llm = LLM()
    _llm_config: LLMDict
    supabase: SupabaseModel

    def __init__(self, config: Config) -> None:
        self._debug = config.schema.logging.debug

        llm = config.schema.reviewer.llm
        self._api_key = llm.api_key
        self._base_url = llm.base_url
        self.provider = llm.provider
        self.llm = llm.model_name

        self._llm_config = LLMDict(llm)
        self.supabase = SupabaseModel(config)

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
    def provider(self) -> ModelProvider:
        return self._provider

    @provider.setter
    def provider(self, value: ModelProvider):
        if not self.base_url or not self.api_key:
            raise ValueError("Base URL and API key must be set before provider")

        if value not in ("OpenAI", "TogetherAI", "OpenRouter", "Google", "Ollama"):
            raise ValueError(
                "Provider must be one of: OpenAI, TogetherAI, OpenRouter, Google, Ollama"
            )

        if value == "OpenAI" or value == "TogetherAI":
            self._provider = OpenAIProvider(
                base_url=self.base_url, api_key=self.api_key
            )
        elif value == "OpenRouter":
            self._provider = OpenRouterProvider(api_key=self.api_key)
        elif value == "Google":
            self._provider = GoogleProvider(api_key=self.api_key)

    @property
    def llm(self) -> LLM:
        return self._llm

    @llm.setter
    def llm(self, value: LLM):
        if not self.provider:
            raise ValueError("Provider must be set before LLM")

        self._llm = value

        if self.provider in ("OpenAI", "TogetherAI", "OpenRouter"):
            self._model = OpenAIModel(self.llm, self.provider)
        elif self.provider == "Google":
            self._model = GoogleModel(self.llm, self.provider)

    @property
    def model(self) -> Model:
        return self._model

    @property
    def llm_config(self) -> LLMDict:
        return self._llm_config


class AiModelType(type):
    """Type for AiModel classes.

    Ensures that all classes inherit from AiModel.

    """

    def __new__(cls, name, bases, dct):
        inherit_from_AiModel = False
        for base in bases:
            if base is AiModel:
                inherit_from_AiModel = True
                break

        if not inherit_from_AiModel:
            raise TypeError(f"{name} must inherit from AiModel")

        return super().__new__(cls, name, bases, dct)
