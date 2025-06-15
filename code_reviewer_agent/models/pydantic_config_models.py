from typing import List

from pydantic import BaseModel, Field, ValidationInfo, field_validator


class CrawlerConfig(BaseModel):
    """Configuration for the crawler."""

    enabled: bool = Field(
        default=False,
        description="Whether to enable the crawler",
    )
    openai_api_key: str = Field(
        default="",
        description="API key for the OpenAI provider (needed for embeddings)",
    )
    embedding_model: str = Field(
        default="text-embedding-3-small",
        description="Name of the embedding model to use (e.g., text-embedding-3-small)",
    )
    max_pages: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum number of pages to crawl",
    )
    max_depth: int = Field(
        default=2,
        ge=1,
        le=10,
        description="Maximum depth of the crawl",
    )
    concurrent_tasks: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Number of concurrent tasks",
    )
    extraction_type: str = Field(
        default="schema",
        description="Type of content extraction ('schema' or 'block')",
    )
    chunk_token_threshold: int = Field(
        default=1000,
        ge=100,
        le=4000,
        description="Token threshold for chunking",
    )
    overlap_rate: float = Field(
        default=0.2,
        ge=0.0,
        le=1.0,
        description="Overlap rate for chunking",
    )
    temperature: float = Field(
        default=0.2,
        ge=0.0,
        le=2.0,
        description="Temperature for text generation",
    )
    max_tokens: int = Field(
        default=800,
        ge=100,
        le=4000,
        description="Maximum number of tokens to generate",
    )
    headless: bool = Field(
        default=True,
        description="Run browser in headless mode",
    )
    locale: str = Field(
        default="en-US",
        description="Browser locale",
    )
    timezone: str = Field(
        default="UTC",
        description="Browser timezone",
    )
    keywords: List[str] = Field(
        default_factory=list,
        description="Keywords for content relevance scoring",
    )
    keyword_weight: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Weight for keyword relevance scoring",
    )

    @field_validator("openai_api_key")
    @classmethod
    def validate_openai_api_key(cls, v: str, info: ValidationInfo) -> str:
        if info.data.get("enabled", False) and not v:
            raise ValueError("OpenAI API key is required")
        return v

    @field_validator("embedding_model")
    @classmethod
    def validate_embedding_model(cls, v: str, info: ValidationInfo) -> str:
        if info.data.get("enabled", False) and not v:
            raise ValueError("Embedding model is required")
        return v


class LLMConfig(BaseModel):
    """Configuration for the LLM model."""

    provider: str = Field(
        default="OpenAI",
        description="Provider for the LLM (OpenAI/TogetherAI, OpenRouter, Google, Ollama)",
    )
    model_name: str = Field(
        default="gpt-4o-mini",
        description="Name of the LLM model to use (e.g., gpt-4o-mini)",
    )
    base_url: str = Field(
        default="https://api.openai.com/v1",
        description="Base URL for the LLM provider",
    )
    api_key: str = Field(
        default="",
        description="API key for the LLM provider",
    )
    temperature: float = Field(
        default=0.2,
        ge=0.0,
        le=2.0,
        description="Temperature for text generation",
    )
    max_tokens: int = Field(
        default=500,
        ge=100,
        le=4000,
        description="Maximum number of tokens to generate",
    )
    top_p: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Nucleus sampling parameter",
    )
    max_attempts: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum number of attempts to generate a valid commit message",
    )

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        if v not in ("OpenAI", "TogetherAI", "OpenRouter", "Google", "Ollama"):
            raise ValueError(
                "Provider must be one of: OpenAI, TogetherAI, OpenRouter, Google, Ollama"
            )
        return v

    @field_validator("api_key")
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        if not v:
            raise ValueError("API key is required")
        return v


class ReviewerConfig(BaseModel):
    """Configuration for the reviewer."""

    llm: LLMConfig = Field(
        default=LLMConfig(),
        description="LLM configuration",
    )
    instruction_dir_path: str = Field(
        default="",
        description="Path to the directory containing your additional instructions",
    )
    platform: str = Field(
        default="github",
        description="Platform to use (github or gitlab)",
    )
    repository: str = Field(
        default="",
        description="Repository to review (format: owner/repo for GitHub, project ID for GitLab)",
    )
    github_token: str = Field(
        default="",
        description="GitHub personal access token",
    )
    gitlab_token: str = Field(
        default="",
        description="GitLab personal access token",
    )
    gitlab_api_url: str = Field(
        default="https://gitlab.com/api/v4",
        description="GitLab API URL",
    )

    @field_validator("platform")
    @classmethod
    def validate_platform(cls, v: str) -> str:
        if v not in ("github", "gitlab"):
            raise ValueError("Platform must be one of: github, gitlab")
        return v

    @field_validator("repository")
    @classmethod
    def validate_repository(cls, v: str) -> str:
        if not v:
            raise ValueError("Repository is required")
        return v

    @field_validator("github_token")
    @classmethod
    def validate_github_token(cls, v: str, info: ValidationInfo) -> str:
        if info.data.get("platform") == "github" and not v:
            raise ValueError("GitHub token is required")
        return v

    @field_validator("gitlab_token")
    @classmethod
    def validate_gitlab_token(cls, v: str, info: ValidationInfo) -> str:
        if info.data.get("platform") == "gitlab" and not v:
            raise ValueError("GitLab token is required")
        return v

    @field_validator("gitlab_api_url")
    @classmethod
    def validate_gitlab_api_url(cls, v: str, info: ValidationInfo) -> str:
        if info.data.get("platform") == "gitlab" and not v:
            raise ValueError("GitLab API URL is required")
        return v


class SupabaseConfig(BaseModel):
    """Configuration for Supabase."""

    url: str = Field(
        default="",
        description="Supabase project URL",
    )
    key: str = Field(
        default="",
        description="Supabase project API key",
    )

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not v:
            raise ValueError("URL is required")
        return v

    @field_validator("key")
    @classmethod
    def validate_key(cls, v: str) -> str:
        if not v:
            raise ValueError("Key is required")
        return v


class LangfuseConfig(BaseModel):
    """Configuration for Langfuse tracing."""

    enabled: bool = Field(
        default=False,
        description="Whether to enable Langfuse tracing",
    )
    public_key: str = Field(
        default="",
        description="Langfuse public key",
    )
    secret_key: str = Field(
        default="",
        description="Langfuse secret key",
    )
    host: str = Field(
        default="https://cloud.langfuse.com",
        description="Langfuse host URL",
    )

    @field_validator("public_key")
    @classmethod
    def validate_public_key(cls, v: str, info: ValidationInfo) -> str:
        if info.data.get("enabled", False) and not v:
            raise ValueError("Public key is required")
        return v

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v: str, info: ValidationInfo) -> str:
        if info.data.get("enabled", False) and not v:
            raise ValueError("Secret key is required")
        return v


class LoggingConfig(BaseModel):
    """Configuration for logging."""

    level: str = Field(
        default="WARNING",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )

    @property
    def debug(self) -> bool:
        return self.level == "DEBUG"

    @field_validator("level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        v_upper = v.upper()
        if v_upper not in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
            raise ValueError(
                f"Invalid log level: {v}. Must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL"
            )
        return v_upper


class ConfigModel(BaseModel):
    crawler: CrawlerConfig = Field(
        default=CrawlerConfig(),
        description="Crawler configuration",
    )
    reviewer: ReviewerConfig = Field(
        default=ReviewerConfig(),
        description="Reviewer configuration",
    )
    supabase: SupabaseConfig = Field(
        default=SupabaseConfig(),
        description="Supabase configuration",
    )
    langfuse: LangfuseConfig = Field(
        default=LangfuseConfig(),
        description="Langfuse tracing configuration",
    )
    logging: LoggingConfig = Field(
        default=LoggingConfig(),
        description="Logging configuration",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "crawler": {
                    "enabled": False,
                    "openai_api_key": "",
                    "embedding_model": "text-embedding-3-small",
                },
                "reviewer": {
                    "instruction_dir_path": "",
                    "platform": "github",
                    "repository": "owner/repo",
                    "github_token": "your_github_token_here",
                    # "gitlab_token": "your_gitlab_token_here",
                    # "gitlab_api_url": "https://gitlab.com/api/v4",
                    "llm": {
                        "provider": "OpenAI",
                        "model_name": "gpt-4o-mini",
                        "base_url": "https://api.openai.com/v1",
                        "api_key": "your_openai_api_key_here",
                        "temperature": 0.2,
                        "max_tokens": 500,
                        "top_p": 1.0,
                        "max_attempts": 3,
                    },
                },
                "supabase": {
                    "url": "your_supabase_url_here",
                    "key": "your_supabase_service_key_here",
                },
                "langfuse": {
                    "enabled": False,
                    "public_key": "your_langfuse_public_key_here",
                    "secret_key": "your_langfuse_secret_key_here",
                    "host": "https://cloud.langfuse.com",
                },
                "logging": {
                    "level": "INFO",
                },
            }
        }
    }
