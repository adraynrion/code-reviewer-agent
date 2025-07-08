import pytest
from pydantic import ValidationError

from code_reviewer_agent.models.pydantic_config_models import (
    ConfigModel,
    CrawlerConfig,
    LangfuseConfig,
    LLMConfig,
    LoggingConfig,
    ReviewerConfig,
    SupabaseConfig,
)


class TestCrawlerConfig:
    """Test CrawlerConfig validation and field constraints."""

    def test_crawler_config_defaults(self) -> None:
        """Test CrawlerConfig with default values."""
        config = CrawlerConfig()
        assert config.enabled is False
        assert config.openai_api_key == ""
        assert config.embedding_model == "text-embedding-3-small"
        assert config.max_pages == 10
        assert config.max_depth == 2
        assert config.concurrent_tasks == 5
        assert config.extraction_type == "schema"
        assert config.chunk_token_threshold == 1000
        assert config.overlap_rate == 0.2
        assert config.temperature == 0.2
        assert config.max_tokens == 800
        assert config.headless is True
        assert config.locale == "en-US"
        assert config.timezone == "UTC"
        assert config.keywords == []
        assert config.keyword_weight == 0.7

    def test_crawler_config_valid_values(self) -> None:
        """Test CrawlerConfig with valid values."""
        config = CrawlerConfig(
            enabled=True,
            openai_api_key="test_key",
            embedding_model="text-embedding-3-large",
            max_pages=50,
            max_depth=5,
            concurrent_tasks=8,
            extraction_type="block",
            chunk_token_threshold=2000,
            overlap_rate=0.5,
            temperature=1.0,
            max_tokens=2000,
            headless=False,
            locale="en-GB",
            timezone="EST",
            keywords=["test", "example"],
            keyword_weight=0.9,
        )
        assert config.enabled is True
        assert config.openai_api_key == "test_key"
        assert config.max_pages == 50
        assert config.max_depth == 5
        assert config.concurrent_tasks == 8
        assert config.keywords == ["test", "example"]

    def test_crawler_config_max_pages_validation(self) -> None:
        """Test max_pages field validation constraints."""
        # Valid range: 1-100
        with pytest.raises(ValidationError) as exc_info:
            CrawlerConfig(max_pages=0)
        assert "greater than or equal to 1" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            CrawlerConfig(max_pages=101)
        assert "less than or equal to 100" in str(exc_info.value)

        # Valid values
        config = CrawlerConfig(max_pages=1)
        assert config.max_pages == 1
        config = CrawlerConfig(max_pages=100)
        assert config.max_pages == 100

    def test_crawler_config_max_depth_validation(self) -> None:
        """Test max_depth field validation constraints."""
        # Valid range: 1-10
        with pytest.raises(ValidationError) as exc_info:
            CrawlerConfig(max_depth=0)
        assert "greater than or equal to 1" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            CrawlerConfig(max_depth=11)
        assert "less than or equal to 10" in str(exc_info.value)

    def test_crawler_config_concurrent_tasks_validation(self) -> None:
        """Test concurrent_tasks field validation constraints."""
        # Valid range: 1-10
        with pytest.raises(ValidationError) as exc_info:
            CrawlerConfig(concurrent_tasks=0)
        assert "greater than or equal to 1" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            CrawlerConfig(concurrent_tasks=11)
        assert "less than or equal to 10" in str(exc_info.value)

    def test_crawler_config_chunk_token_threshold_validation(self) -> None:
        """Test chunk_token_threshold field validation constraints."""
        # Valid range: 100-4000
        with pytest.raises(ValidationError) as exc_info:
            CrawlerConfig(chunk_token_threshold=99)
        assert "greater than or equal to 100" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            CrawlerConfig(chunk_token_threshold=4001)
        assert "less than or equal to 4000" in str(exc_info.value)

    def test_crawler_config_overlap_rate_validation(self) -> None:
        """Test overlap_rate field validation constraints."""
        # Valid range: 0.0-1.0
        with pytest.raises(ValidationError) as exc_info:
            CrawlerConfig(overlap_rate=-0.1)
        assert "greater than or equal to 0" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            CrawlerConfig(overlap_rate=1.1)
        assert "less than or equal to 1" in str(exc_info.value)

    def test_crawler_config_temperature_validation(self) -> None:
        """Test temperature field validation constraints."""
        # Valid range: 0.0-2.0
        with pytest.raises(ValidationError) as exc_info:
            CrawlerConfig(temperature=-0.1)
        assert "greater than or equal to 0" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            CrawlerConfig(temperature=2.1)
        assert "less than or equal to 2" in str(exc_info.value)

    def test_crawler_config_max_tokens_validation(self) -> None:
        """Test max_tokens field validation constraints."""
        # Valid range: 100-4000
        with pytest.raises(ValidationError) as exc_info:
            CrawlerConfig(max_tokens=99)
        assert "greater than or equal to 100" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            CrawlerConfig(max_tokens=4001)
        assert "less than or equal to 4000" in str(exc_info.value)

    def test_crawler_config_keyword_weight_validation(self) -> None:
        """Test keyword_weight field validation constraints."""
        # Valid range: 0.0-1.0
        with pytest.raises(ValidationError) as exc_info:
            CrawlerConfig(keyword_weight=-0.1)
        assert "greater than or equal to 0" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            CrawlerConfig(keyword_weight=1.1)
        assert "less than or equal to 1" in str(exc_info.value)

    def test_crawler_config_openai_api_key_validator(self) -> None:
        """Test openai_api_key custom validator."""
        # When enabled=False, empty api_key is allowed
        config = CrawlerConfig(enabled=False, openai_api_key="")
        assert config.openai_api_key == ""

        # When enabled=True, api_key is required
        with pytest.raises(ValidationError) as exc_info:
            CrawlerConfig(enabled=True, openai_api_key="")
        assert "OpenAI API key is required" in str(exc_info.value)

        # When enabled=True, valid api_key is accepted
        config = CrawlerConfig(enabled=True, openai_api_key="test_key")
        assert config.openai_api_key == "test_key"

    def test_crawler_config_embedding_model_validator(self) -> None:
        """Test embedding_model custom validator."""
        # When enabled=False, empty embedding_model is allowed
        config = CrawlerConfig(enabled=False, embedding_model="")
        assert config.embedding_model == ""

        # When enabled=True, embedding_model is required
        with pytest.raises(ValidationError) as exc_info:
            CrawlerConfig(enabled=True, embedding_model="")
        assert "Embedding model is required" in str(exc_info.value)


class TestLLMConfig:
    """Test LLMConfig validation and field constraints."""

    def test_llm_config_defaults(self) -> None:
        """Test LLMConfig with default values."""
        config = LLMConfig()
        assert config.provider == "OpenAI"
        assert config.model_name == "gpt-4o-mini"
        assert config.base_url == "https://api.openai.com/v1"
        assert config.api_key == ""
        assert config.temperature == 0.2
        assert config.max_tokens == 500
        assert config.top_p == 1.0
        assert config.max_attempts == 3

    def test_llm_config_valid_values(self) -> None:
        """Test LLMConfig with valid values."""
        config = LLMConfig(
            provider="Google",
            model_name="gemini-pro",
            base_url="https://api.google.com/v1",
            api_key="test_key",
            temperature=1.5,
            max_tokens=2000,
            top_p=0.9,
            max_attempts=5,
        )
        assert config.provider == "Google"
        assert config.model_name == "gemini-pro"
        assert config.base_url == "https://api.google.com/v1"
        assert config.api_key == "test_key"
        assert config.temperature == 1.5
        assert config.max_tokens == 2000
        assert config.top_p == 0.9
        assert config.max_attempts == 5

    def test_llm_config_provider_validator(self) -> None:
        """Test provider field validator."""
        valid_providers = ["OpenAI", "TogetherAI", "OpenRouter", "Google", "Ollama"]

        for provider in valid_providers:
            config = LLMConfig(provider=provider, api_key="test_key")
            assert config.provider == provider

        with pytest.raises(ValidationError) as exc_info:
            LLMConfig(provider="InvalidProvider", api_key="test_key")
        assert "Provider must be one of" in str(exc_info.value)

    def test_llm_config_api_key_validator(self) -> None:
        """Test api_key field validator."""
        with pytest.raises(ValidationError) as exc_info:
            LLMConfig(api_key="")
        assert "API key is required" in str(exc_info.value)

        config = LLMConfig(api_key="test_key")
        assert config.api_key == "test_key"

    def test_llm_config_temperature_validation(self) -> None:
        """Test temperature field validation constraints."""
        # Valid range: 0.0-2.0
        with pytest.raises(ValidationError) as exc_info:
            LLMConfig(api_key="test", temperature=-0.1)
        assert "greater than or equal to 0" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            LLMConfig(api_key="test", temperature=2.1)
        assert "less than or equal to 2" in str(exc_info.value)

    def test_llm_config_max_tokens_validation(self) -> None:
        """Test max_tokens field validation constraints."""
        # Valid range: 100-4000
        with pytest.raises(ValidationError) as exc_info:
            LLMConfig(api_key="test", max_tokens=99)
        assert "greater than or equal to 100" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            LLMConfig(api_key="test", max_tokens=4001)
        assert "less than or equal to 4000" in str(exc_info.value)

    def test_llm_config_top_p_validation(self) -> None:
        """Test top_p field validation constraints."""
        # Valid range: 0.0-1.0
        with pytest.raises(ValidationError) as exc_info:
            LLMConfig(api_key="test", top_p=-0.1)
        assert "greater than or equal to 0" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            LLMConfig(api_key="test", top_p=1.1)
        assert "less than or equal to 1" in str(exc_info.value)

    def test_llm_config_max_attempts_validation(self) -> None:
        """Test max_attempts field validation constraints."""
        # Valid range: 1-10
        with pytest.raises(ValidationError) as exc_info:
            LLMConfig(api_key="test", max_attempts=0)
        assert "greater than or equal to 1" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            LLMConfig(api_key="test", max_attempts=11)
        assert "less than or equal to 10" in str(exc_info.value)


class TestReviewerConfig:
    """Test ReviewerConfig validation and field constraints."""

    def test_reviewer_config_defaults(self) -> None:
        """Test ReviewerConfig with default values."""
        config = ReviewerConfig()
        assert isinstance(config.llm, LLMConfig)
        assert config.instruction_dir_path == ""
        assert config.platform == "github"
        assert config.repository == ""
        assert config.github_token == ""
        assert config.gitlab_token == ""
        assert config.gitlab_api_url == "https://gitlab.com/api/v4"

    def test_reviewer_config_valid_values(self) -> None:
        """Test ReviewerConfig with valid values."""
        llm_config = LLMConfig(api_key="test_llm_key")
        config = ReviewerConfig(
            llm=llm_config,
            instruction_dir_path="/path/to/instructions",
            platform="gitlab",
            repository="project/repo",
            github_token="github_token",
            gitlab_token="gitlab_token",
            gitlab_api_url="https://custom.gitlab.com/api/v4",
        )
        assert config.llm == llm_config
        assert config.instruction_dir_path == "/path/to/instructions"
        assert config.platform == "gitlab"
        assert config.repository == "project/repo"
        assert config.github_token == "github_token"
        assert config.gitlab_token == "gitlab_token"
        assert config.gitlab_api_url == "https://custom.gitlab.com/api/v4"

    def test_reviewer_config_platform_validator(self) -> None:
        """Test platform field validator."""
        valid_platforms = ["github", "gitlab"]

        for platform in valid_platforms:
            config = ReviewerConfig(
                platform=platform,
                repository="test/repo",
                github_token="token" if platform == "github" else "",
                gitlab_token="token" if platform == "gitlab" else "",
            )
            assert config.platform == platform

        with pytest.raises(ValidationError) as exc_info:
            ReviewerConfig(platform="invalid_platform", repository="test/repo")
        assert "Platform must be one of: github, gitlab" in str(exc_info.value)

    def test_reviewer_config_repository_validator(self) -> None:
        """Test repository field validator."""
        with pytest.raises(ValidationError) as exc_info:
            ReviewerConfig(repository="")
        assert "Repository is required" in str(exc_info.value)

        config = ReviewerConfig(repository="test/repo", github_token="token")
        assert config.repository == "test/repo"

    def test_reviewer_config_github_token_validator(self) -> None:
        """Test github_token field validator."""
        # When platform is github, token is required
        with pytest.raises(ValidationError) as exc_info:
            ReviewerConfig(platform="github", repository="test/repo", github_token="")
        assert "GitHub token is required" in str(exc_info.value)

        # When platform is gitlab, github token is not required
        config = ReviewerConfig(
            platform="gitlab",
            repository="test/repo",
            github_token="",
            gitlab_token="gitlab_token",
        )
        assert config.github_token == ""

        # Valid github token
        config = ReviewerConfig(
            platform="github", repository="test/repo", github_token="github_token"
        )
        assert config.github_token == "github_token"

    def test_reviewer_config_gitlab_token_validator(self) -> None:
        """Test gitlab_token field validator."""
        # When platform is gitlab, token is required
        with pytest.raises(ValidationError) as exc_info:
            ReviewerConfig(platform="gitlab", repository="test/repo", gitlab_token="")
        assert "GitLab token is required" in str(exc_info.value)

        # When platform is github, gitlab token is not required
        config = ReviewerConfig(
            platform="github",
            repository="test/repo",
            gitlab_token="",
            github_token="github_token",
        )
        assert config.gitlab_token == ""

    def test_reviewer_config_gitlab_api_url_validator(self) -> None:
        """Test gitlab_api_url field validator."""
        # When platform is gitlab, API URL is required
        with pytest.raises(ValidationError) as exc_info:
            ReviewerConfig(
                platform="gitlab",
                repository="test/repo",
                gitlab_token="token",
                gitlab_api_url="",
            )
        assert "GitLab API URL is required" in str(exc_info.value)


class TestSupabaseConfig:
    """Test SupabaseConfig validation."""

    def test_supabase_config_defaults(self) -> None:
        """Test SupabaseConfig with default values."""
        config = SupabaseConfig()
        assert config.url == ""
        assert config.key == ""

    def test_supabase_config_valid_values(self) -> None:
        """Test SupabaseConfig with valid values."""
        config = SupabaseConfig(url="https://test.supabase.co", key="test_supabase_key")
        assert config.url == "https://test.supabase.co"
        assert config.key == "test_supabase_key"

    def test_supabase_config_url_validator(self) -> None:
        """Test url field validator."""
        with pytest.raises(ValidationError) as exc_info:
            SupabaseConfig(url="")
        assert "URL is required" in str(exc_info.value)

        config = SupabaseConfig(url="https://test.supabase.co", key="test_key")
        assert config.url == "https://test.supabase.co"

    def test_supabase_config_key_validator(self) -> None:
        """Test key field validator."""
        with pytest.raises(ValidationError) as exc_info:
            SupabaseConfig(key="")
        assert "Key is required" in str(exc_info.value)

        config = SupabaseConfig(url="https://test.supabase.co", key="test_key")
        assert config.key == "test_key"


class TestLangfuseConfig:
    """Test LangfuseConfig validation."""

    def test_langfuse_config_defaults(self) -> None:
        """Test LangfuseConfig with default values."""
        config = LangfuseConfig()
        assert config.enabled is False
        assert config.public_key == ""
        assert config.secret_key == ""
        assert config.host == "https://cloud.langfuse.com"

    def test_langfuse_config_valid_values(self) -> None:
        """Test LangfuseConfig with valid values."""
        config = LangfuseConfig(
            enabled=True,
            public_key="test_public_key",
            secret_key="test_secret_key",
            host="https://custom.langfuse.com",
        )
        assert config.enabled is True
        assert config.public_key == "test_public_key"
        assert config.secret_key == "test_secret_key"
        assert config.host == "https://custom.langfuse.com"

    def test_langfuse_config_public_key_validator(self) -> None:
        """Test public_key field validator."""
        # When enabled=False, empty public_key is allowed
        config = LangfuseConfig(enabled=False, public_key="")
        assert config.public_key == ""

        # When enabled=True, public_key is required
        with pytest.raises(ValidationError) as exc_info:
            LangfuseConfig(enabled=True, public_key="")
        assert "Public key is required" in str(exc_info.value)

        # When enabled=True, valid public_key is accepted
        config = LangfuseConfig(
            enabled=True, public_key="test_key", secret_key="test_secret"
        )
        assert config.public_key == "test_key"

    def test_langfuse_config_secret_key_validator(self) -> None:
        """Test secret_key field validator."""
        # When enabled=False, empty secret_key is allowed
        config = LangfuseConfig(enabled=False, secret_key="")
        assert config.secret_key == ""

        # When enabled=True, secret_key is required
        with pytest.raises(ValidationError) as exc_info:
            LangfuseConfig(enabled=True, secret_key="")
        assert "Secret key is required" in str(exc_info.value)

        # When enabled=True, valid secret_key is accepted
        config = LangfuseConfig(
            enabled=True, public_key="test_public", secret_key="test_secret"
        )
        assert config.secret_key == "test_secret"


class TestLoggingConfig:
    """Test LoggingConfig validation."""

    def test_logging_config_defaults(self) -> None:
        """Test LoggingConfig with default values."""
        config = LoggingConfig()
        assert config.level == "WARNING"
        assert config.debug is False

    def test_logging_config_valid_levels(self) -> None:
        """Test LoggingConfig with valid log levels."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

        for level in valid_levels:
            config = LoggingConfig(level=level)
            assert config.level == level
            assert config.debug == (level == "DEBUG")

    def test_logging_config_case_insensitive(self) -> None:
        """Test LoggingConfig accepts lowercase levels."""
        config = LoggingConfig(level="debug")
        assert config.level == "DEBUG"
        assert config.debug is True

        config = LoggingConfig(level="info")
        assert config.level == "INFO"
        assert config.debug is False

    def test_logging_config_invalid_level(self) -> None:
        """Test LoggingConfig rejects invalid log levels."""
        with pytest.raises(ValidationError) as exc_info:
            LoggingConfig(level="INVALID")
        assert "Invalid log level" in str(exc_info.value)
        assert "Must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL" in str(
            exc_info.value
        )

    def test_logging_config_debug_property(self) -> None:
        """Test debug property for all log levels."""
        config = LoggingConfig(level="DEBUG")
        assert config.debug is True

        for level in ["INFO", "WARNING", "ERROR", "CRITICAL"]:
            config = LoggingConfig(level=level)
            assert config.debug is False


class TestConfigModel:
    """Test ConfigModel integration."""

    def test_config_model_defaults(self) -> None:
        """Test ConfigModel with default values."""
        config = ConfigModel()
        assert isinstance(config.crawler, CrawlerConfig)
        assert isinstance(config.reviewer, ReviewerConfig)
        assert isinstance(config.supabase, SupabaseConfig)
        assert isinstance(config.langfuse, LangfuseConfig)
        assert isinstance(config.logging, LoggingConfig)

    def test_config_model_valid_values(self) -> None:
        """Test ConfigModel with valid nested configurations."""
        config_data = {
            "crawler": {
                "enabled": True,
                "openai_api_key": "test_openai_key",
                "max_pages": 20,
            },
            "reviewer": {
                "platform": "github",
                "repository": "test/repo",
                "github_token": "test_github_token",
                "llm": {"api_key": "test_llm_key"},
            },
            "supabase": {
                "url": "https://test.supabase.co",
                "key": "test_supabase_key",
            },
            "langfuse": {
                "enabled": True,
                "public_key": "test_public_key",
                "secret_key": "test_secret_key",
            },
            "logging": {"level": "DEBUG"},
        }

        config = ConfigModel(**config_data)
        assert config.crawler.enabled is True
        assert config.crawler.openai_api_key == "test_openai_key"
        assert config.reviewer.platform == "github"
        assert config.reviewer.repository == "test/repo"
        assert config.supabase.url == "https://test.supabase.co"
        assert config.langfuse.enabled is True
        assert config.logging.level == "DEBUG"

    def test_config_model_partial_data(self) -> None:
        """Test ConfigModel with partial configuration data."""
        config_data = {
            "reviewer": {
                "repository": "test/repo",
                "github_token": "test_token",
                "llm": {"api_key": "test_key"},
            }
        }

        config = ConfigModel(**config_data)
        # Other configs should have defaults
        assert config.crawler.enabled is False
        assert config.reviewer.repository == "test/repo"
        assert config.logging.level == "WARNING"

    def test_config_model_serialization(self) -> None:
        """Test ConfigModel serialization and deserialization."""
        config_data = {
            "reviewer": {
                "repository": "test/repo",
                "github_token": "test_token",
                "llm": {"api_key": "test_key"},
            },
            "logging": {"level": "INFO"},
        }

        config = ConfigModel(**config_data)

        # Test model_dump
        dumped = config.model_dump()
        assert isinstance(dumped, dict)
        assert dumped["reviewer"]["repository"] == "test/repo"
        assert dumped["logging"]["level"] == "INFO"

        # Test round-trip
        new_config = ConfigModel(**dumped)
        assert new_config.reviewer.repository == config.reviewer.repository
        assert new_config.logging.level == config.logging.level

    def test_config_model_validation_errors(self) -> None:
        """Test ConfigModel with validation errors in nested configs."""
        # Invalid platform
        with pytest.raises(ValidationError) as exc_info:
            ConfigModel(
                reviewer={
                    "platform": "invalid",
                    "repository": "test/repo",
                    "github_token": "token",
                }
            )
        assert "Platform must be one of" in str(exc_info.value)

        # Missing required fields
        with pytest.raises(ValidationError) as exc_info:
            ConfigModel(
                reviewer={
                    "platform": "github",
                    "repository": "",  # Required field
                    "github_token": "token",
                }
            )
        assert "Repository is required" in str(exc_info.value)
