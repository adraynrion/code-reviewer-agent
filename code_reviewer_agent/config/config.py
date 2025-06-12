"""Configuration management for the code reviewer agent."""

import os
import sys
from pathlib import Path
from typing import Any, Dict

import yaml
from pydantic import BaseModel, Field, ValidationInfo, field_validator

from code_reviewer_agent.utils.rich_utils import print_debug, print_error


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


class Config(BaseModel):
    """Top-level configuration for the code reviewer features."""

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
                "llm": {
                    "model_name": "gpt-4o-mini",
                    "temperature": 0.2,
                    "max_tokens": 500,
                    "top_p": 1.0,
                },
                "supabase": {
                    "url": "your_supabase_url_here",
                    "key": "your_supabase_service_key_here",
                },
                "crawler": {
                    "enabled": False,
                    "openai_api_key": "",
                    "embedding_model": "text-embedding-3-small",
                },
                "reviewer": {
                    "platform": "github",
                    "repository": "owner/repo",
                    "github_token": "your_github_token_here",
                },
                "langfuse": {
                    "enabled": False,
                    "public_key": "",
                    "secret_key": "",
                    "host": "https://cloud.langfuse.com",
                },
                "logging": {
                    "level": "INFO",
                },
            }
        }
    }

    @staticmethod
    def get_config_path() -> Path:
        """Get the path to the config file.

        Returns:
            Path: Path to the config file

        Raises:
            SystemExit: If the config file is not found in any of the standard locations

        """
        # Standard config file locations in order of precedence
        config_paths = [
            Path.cwd() / "config.yaml",  # ./config.yaml
            Path.home()
            / ".config"
            / "code-reviewer"
            / "config.yaml",  # ~/.config/code-reviewer/config.yaml
            Path("/etc/code-reviewer/config.yaml"),  # /etc/code-reviewer/config.yaml
        ]
        for path in config_paths:
            if path.exists():
                return path
        raise SystemExit(
            "Could not find config file in standard locations! Refer to README for instructions."
        )

    @classmethod
    def load(cls) -> "Config":
        """Load configuration from config.yaml file.

        Returns:
            Config: Loaded configuration

        Raises:
            SystemExit: If the config file is not found in any of the standard locations

        """
        try:
            config_path = cls.get_config_path()

            # Start with defaults
            config_data: Dict[str, Any] = {}

            # Load from YAML
            with open(config_path, "r", encoding="utf-8") as f:
                config_data.update(yaml.safe_load(f) or {})
        except Exception as e:
            print_error(f"Error loading config from {config_path}: {e}")
            sys.exit(1)

        print_debug(f"Loaded config: {config_data}")

        # Convert the config data to a Config object
        config = Config(**config_data)

        # Export DEBUG environment variable for use in rich_utils.py
        os.environ["DEBUG"] = str(config.logging.debug)

        return config

    def print_config(self) -> None:
        """Print the current configuration (without sensitive data)."""
        from rich.console import Console
        from rich.table import Table

        console = Console()
        table = Table(title="Current Configuration", show_header=False, show_lines=True)
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")

        # ===== Add non-sensitive configuration =====
        # Crawler
        for field_name in self.crawler.__class__.model_fields:
            if field_name in ("openai_api_key"):
                # Mask sensitive fields
                value = "*" * 8 if getattr(self, field_name, None) else ""
            else:
                value = str(getattr(self, field_name, ""))

            table.add_row(field_name, value)
        # Reviewer
        for field_name in self.reviewer.__class__.model_fields:
            if field_name in ("github_token", "gitlab_token", "llm"):
                # Mask sensitive fields
                value = "*" * 8 if getattr(self, field_name, None) else ""
            else:
                value = str(getattr(self, field_name, ""))

            table.add_row(field_name, value)
        # Reviewer - LLM
        for field_name in self.reviewer.llm.__class__.model_fields:
            if field_name in ("api_key"):
                # Mask sensitive fields
                value = "*" * 8 if getattr(self, field_name, None) else ""
            else:
                value = str(getattr(self, field_name, ""))
            table.add_row(field_name, value)
        # Supabase
        for field_name in self.supabase.__class__.model_fields:
            if field_name in ("key"):
                # Mask sensitive fields
                value = "*" * 8 if getattr(self, field_name, None) else ""
            else:
                value = str(getattr(self, field_name, ""))

            table.add_row(field_name, value)
        # Langfuse
        for field_name in self.langfuse.__class__.model_fields:
            if field_name in ("public_key", "secret_key"):
                # Mask sensitive fields
                value = "*" * 8 if getattr(self, field_name, None) else ""
            else:
                value = str(getattr(self, field_name, ""))

            table.add_row(field_name, value)
        # Logging
        for field_name in self.logging.__class__.model_fields:
            value = str(getattr(self, field_name, ""))
            table.add_row(field_name, value)

        console.print(table)


config = Config.load()
