import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Generator
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
import yaml
from pydantic_ai.models.test import TestModel

from code_reviewer_agent.config.config import Config
from code_reviewer_agent.models.base_agent import AiModel
from code_reviewer_agent.models.base_types import GitHubToken, GitLabToken
from code_reviewer_agent.models.pydantic_config_models import (
    ConfigModel,
    CrawlerConfig,
    LangfuseConfig,
    LLMConfig,
    LoggingConfig,
    ReviewerConfig,
    SupabaseConfig,
)


@pytest.fixture
def mock_config_data() -> Dict[str, Any]:
    """Mock configuration data for testing."""
    return {
        "reviewer": {
            "github_token": "test_github_token",
            "gitlab_token": "test_gitlab_token",
            "platform": "github",
            "repository": "test/repo",
            "request_id": "123",
            "reviewed_label": "ai-reviewed",
            "instruction_dir_path": "instructions",
            "llm": {
                "provider": "OpenAI",
                "model_name": "gpt-4",
                "api_key": "test_api_key",
                "base_url": "https://api.openai.com/v1",
                "temperature": 0.7,
                "max_tokens": 1000,
                "top_p": 1.0,
                "max_attempts": 3,
            },
        },
        "crawler": {
            "openai_api_key": "test_openai_key",
            "max_pages": 10,
            "max_depth": 2,
            "concurrent_tasks": 5,
            "extraction_type": "markdown",
            "chunk_token_threshold": 1000,
            "overlap_rate": 0.1,
            "temperature": 0.7,
            "max_tokens": 1000,
            "headless": True,
            "locale": "en-US",
            "timezone": "UTC",
            "keywords": ["test"],
            "keyword_weight": 1.0,
        },
        "supabase": {
            "url": "https://test.supabase.co",
            "key": "test_supabase_key",
            "table": "documents",
        },
        "langfuse": {
            "enabled": False,
            "public_key": "test_public_key",
            "secret_key": "test_secret_key",
            "host": "https://cloud.langfuse.com",
        },
        "logging": {"debug": False, "level": "INFO"},
    }


@pytest.fixture
def mock_config_model(mock_config_data: Dict[str, Any]) -> ConfigModel:
    """Create a mock ConfigModel for testing."""
    return ConfigModel(**mock_config_data)


@pytest.fixture
def temp_config_file(mock_config_data: Dict[str, Any]) -> Generator[Path, None, None]:
    """Create a temporary config file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(mock_config_data, f)
        temp_path = Path(f.name)

    try:
        yield temp_path
    finally:
        temp_path.unlink()


@pytest.fixture
def temp_config_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for config files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def mock_github_token() -> GitHubToken:
    """Mock GitHub token for testing."""
    return GitHubToken("test_github_token")


@pytest.fixture
def mock_gitlab_token() -> GitLabToken:
    """Mock GitLab token for testing."""
    return GitLabToken("test_gitlab_token")


@pytest.fixture
def mock_reviewer_config() -> ReviewerConfig:
    """Mock reviewer configuration for testing."""
    return ReviewerConfig(
        github_token="test_github_token",
        gitlab_token="test_gitlab_token",
        platform="github",
        repository="test/repo",
        instruction_dir_path="instructions",
        llm=LLMConfig(
            provider="OpenAI",
            model_name="gpt-4",
            api_key="test_api_key",
            base_url="https://api.openai.com/v1",
            temperature=0.7,
            max_tokens=1000,
            top_p=1.0,
            max_attempts=3,
        ),
    )


@pytest.fixture
def mock_crawler_config() -> CrawlerConfig:
    """Mock crawler configuration for testing."""
    return CrawlerConfig(
        openai_api_key="test_openai_key",
        max_pages=10,
        max_depth=2,
        concurrent_tasks=5,
        extraction_type="markdown",
        chunk_token_threshold=1000,
        overlap_rate=0.1,
        temperature=0.7,
        max_tokens=1000,
        headless=True,
        locale="en-US",
        timezone="UTC",
        keywords=["test"],
        keyword_weight=1.0,
    )


@pytest.fixture
def mock_supabase_config() -> SupabaseConfig:
    """Mock Supabase configuration for testing."""
    return SupabaseConfig(
        url="https://test.supabase.co",
        key="test_supabase_key",
    )


@pytest.fixture
def mock_langfuse_config() -> LangfuseConfig:
    """Mock Langfuse configuration for testing."""
    return LangfuseConfig(
        enabled=False,
        public_key="test_public_key",
        secret_key="test_secret_key",
        host="https://cloud.langfuse.com",
    )


@pytest.fixture
def mock_logging_config() -> LoggingConfig:
    """Mock logging configuration for testing."""
    return LoggingConfig(level="INFO")


@pytest.fixture
def mock_llm_config() -> LLMConfig:
    """Mock LLM configuration for testing."""
    return LLMConfig(
        provider="OpenAI",
        model_name="gpt-4",
        api_key="test_api_key",
        base_url="https://api.openai.com/v1",
        temperature=0.7,
        max_tokens=1000,
        top_p=1.0,
        max_attempts=3,
    )


@pytest.fixture
def mock_config(mock_config_model: ConfigModel) -> Generator[Config, None, None]:
    """Mock Config instance for testing."""
    with patch("code_reviewer_agent.config.config.ConfigFilePath") as mock_config_path:
        with patch("code_reviewer_agent.config.config.Config._load_config_from_file"):
            with patch("code_reviewer_agent.config.config.Config._update_config"):
                with patch("code_reviewer_agent.config.config.console.print"):
                    with patch("code_reviewer_agent.models.supabase.create_client"):
                        config = Config.__new__(Config)
                        config._schema = mock_config_model
                        config._debug = False
                        config._file = MagicMock()
                        config._file.file = Path("/tmp/test_config.yaml")
                        yield config


@pytest.fixture
def mock_ai_model(mock_config: Config) -> AiModel:
    """Mock AI model for testing."""
    return AiModel(mock_config)


@pytest.fixture
def test_model() -> TestModel:
    """Test model for AI agent testing without LLM API calls."""
    return TestModel()


@pytest.fixture
def mock_github_api_response() -> Dict[str, Any]:
    """Mock GitHub API response for testing."""
    return {
        "number": 123,
        "title": "Test PR",
        "body": "Test description",
        "state": "open",
        "user": {"login": "testuser"},
        "head": {"sha": "abc123"},
        "base": {"sha": "def456"},
    }


@pytest.fixture
def mock_gitlab_api_response() -> Dict[str, Any]:
    """Mock GitLab API response for testing."""
    return {
        "iid": 123,
        "title": "Test MR",
        "description": "Test description",
        "state": "opened",
        "author": {"username": "testuser"},
        "sha": "abc123",
        "target_branch": "main",
    }


@pytest.fixture
def mock_pull_request_files() -> list[Dict[str, Any]]:
    """Mock pull request files for testing."""
    return [
        {
            "filename": "test.py",
            "status": "modified",
            "additions": 10,
            "deletions": 5,
            "changes": 15,
            "patch": "@@ -1,5 +1,10 @@\n+test content",
            "sha": "abc123",
        }
    ]


@pytest.fixture
def mock_requests_get() -> Generator[Mock, None, None]:
    """Mock requests.get for HTTP API testing."""
    with patch("requests.get") as mock_get:
        yield mock_get


@pytest.fixture
def mock_requests_post() -> Generator[Mock, None, None]:
    """Mock requests.post for HTTP API testing."""
    with patch("requests.post") as mock_post:
        yield mock_post


@pytest.fixture
def mock_requests_put() -> Generator[Mock, None, None]:
    """Mock requests.put for HTTP API testing."""
    with patch("requests.put") as mock_put:
        yield mock_put


@pytest.fixture
def mock_async_function() -> Generator[AsyncMock, None, None]:
    """Mock async function for testing."""
    return AsyncMock()


@pytest.fixture
def mock_supabase_client() -> Generator[Mock, None, None]:
    """Mock Supabase client for testing."""
    return MagicMock()


@pytest.fixture
def mock_vecs_client() -> Generator[Mock, None, None]:
    """Mock vecs client for testing."""
    return MagicMock()


@pytest.fixture
def mock_rich_console() -> Generator[Mock, None, None]:
    """Mock Rich console for testing."""
    return MagicMock()


@pytest.fixture(autouse=True)
def disable_env_loading() -> Generator[None, None, None]:
    """Disable environment variable loading in tests."""
    with patch.dict(os.environ, {}, clear=True):
        yield


@pytest.fixture
def mock_file_system() -> Generator[Dict[str, Mock], None, None]:
    """Mock file system operations for testing."""
    with patch("pathlib.Path.exists") as mock_exists:
        with patch("pathlib.Path.read_text") as mock_read_text:
            with patch("pathlib.Path.write_text") as mock_write_text:
                mock_exists.return_value = True
                mock_read_text.return_value = "test content"
                yield {
                    "exists": mock_exists,
                    "read_text": mock_read_text,
                    "write_text": mock_write_text,
                }


@pytest.fixture
def mock_yaml_load() -> Generator[Mock, None, None]:
    """Mock YAML loading for testing."""
    with patch("yaml.safe_load") as mock_load:
        yield mock_load


@pytest.fixture
def mock_yaml_dump() -> Generator[Mock, None, None]:
    """Mock YAML dumping for testing."""
    with patch("yaml.dump") as mock_dump:
        yield mock_dump
