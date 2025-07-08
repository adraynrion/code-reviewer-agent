import os
from unittest.mock import Mock, patch

import pytest

from code_reviewer_agent.models.pydantic_config_models import LangfuseConfig
from code_reviewer_agent.utils.langfuse import LangfuseHost, LangfuseKey, LangfuseModel


class TestLangfuseKey:
    """Test LangfuseKey validator."""

    def test_valid_key(self) -> None:
        """Test valid Langfuse key."""
        key = LangfuseKey("pk_test_123")
        assert str(key) == "pk_test_123"

    def test_empty_key(self) -> None:
        """Test empty key raises validation error."""
        with pytest.raises(ValueError, match="Value cannot be empty"):
            LangfuseKey("")


class TestLangfuseHost:
    """Test LangfuseHost validator."""

    def test_valid_host(self) -> None:
        """Test valid Langfuse host."""
        host = LangfuseHost("https://cloud.langfuse.com")
        assert str(host) == "https://cloud.langfuse.com"

    def test_empty_host(self) -> None:
        """Test empty host raises validation error."""
        with pytest.raises(ValueError, match="Value cannot be empty"):
            LangfuseHost("")


class TestLangfuseModel:
    """Test LangfuseModel singleton."""

    def setup_method(self) -> None:
        """Reset singleton for each test."""
        LangfuseModel._instance = None

    def test_singleton_pattern(self) -> None:
        """Test that LangfuseModel follows singleton pattern."""
        config = LangfuseConfig(
            public_key="pk_test_123",
            secret_key="sk_test_123",
            host="https://cloud.langfuse.com",
            enabled=False,
        )

        instance1 = LangfuseModel(config)
        instance2 = LangfuseModel(config)

        assert instance1 is instance2

    def test_initialization(self) -> None:
        """Test LangfuseModel initialization."""
        config = LangfuseConfig(
            public_key="pk_test_123",
            secret_key="sk_test_123",
            host="https://cloud.langfuse.com",
            enabled=False,
        )

        model = LangfuseModel(config)

        assert str(model.public_key) == "pk_test_123"
        assert str(model.secret_key) == "sk_test_123"
        assert str(model.host) == "https://cloud.langfuse.com"
        assert model.enabled is False

    def test_properties(self) -> None:
        """Test LangfuseModel properties."""
        config = LangfuseConfig(
            public_key="pk_test_123",
            secret_key="sk_test_123",
            host="https://cloud.langfuse.com",
            enabled=False,
        )

        model = LangfuseModel(config)

        assert isinstance(model.public_key, LangfuseKey)
        assert isinstance(model.secret_key, LangfuseKey)
        assert isinstance(model.host, LangfuseHost)
        assert isinstance(model.enabled, bool)

    def test_tracer_not_initialized(self) -> None:
        """Test tracer property when not initialized."""
        config = LangfuseConfig(
            public_key="pk_test_123",
            secret_key="sk_test_123",
            host="https://cloud.langfuse.com",
            enabled=False,
        )

        model = LangfuseModel(config)
        # Need to initialize _tracer to None for this test
        model._tracer = None

        with pytest.raises(ValueError, match="Langfuse is not initialized"):
            _ = model.tracer

    @patch("code_reviewer_agent.utils.langfuse.print_warning")
    def test_disable_langfuse(self, mock_print_warning) -> None:
        """Test disabling Langfuse."""
        config = LangfuseConfig(
            public_key="pk_test_123",
            secret_key="sk_test_123",
            host="https://cloud.langfuse.com",
            enabled=True,
        )

        model = LangfuseModel(config)
        model._enabled = True  # Set internal state to true first
        model.enabled = False

        mock_print_warning.assert_called_once_with("Langfuse is now disabled.")
        assert model.enabled is False

    @patch("code_reviewer_agent.utils.langfuse.Langfuse")
    @patch("code_reviewer_agent.utils.langfuse.logfire")
    @patch("code_reviewer_agent.utils.langfuse.print_success")
    @patch.dict(os.environ, {}, clear=True)
    def test_enable_langfuse_success(
        self, mock_print_success, mock_logfire, mock_langfuse
    ) -> None:
        """Test successfully enabling Langfuse."""
        # Setup mocks
        mock_client = Mock()
        mock_tracer = Mock()
        mock_client.trace.return_value = mock_tracer
        mock_langfuse.return_value = mock_client

        config = LangfuseConfig(
            public_key="pk_test_123",
            secret_key="sk_test_123",
            host="https://cloud.langfuse.com",
            enabled=False,
        )

        model = LangfuseModel(config)
        model.enabled = True

        # Verify environment variables were set
        assert "OTEL_EXPORTER_OTLP_ENDPOINT" in os.environ
        assert "OTEL_EXPORTER_OTLP_HEADERS" in os.environ

        # Verify Langfuse was configured
        mock_langfuse.assert_called_once_with(
            public_key=model.public_key, secret_key=model.secret_key, host=model.host
        )

        # Verify logfire was configured
        mock_logfire.configure.assert_called_once()

        mock_print_success.assert_called_once_with("Langfuse initialized successfully!")

    @patch.object(
        LangfuseModel, "public_key", new_callable=lambda: property(lambda self: "")
    )
    def test_enable_langfuse_missing_config(self, mock_public_key) -> None:
        """Test enabling Langfuse with missing configuration."""
        config = LangfuseConfig(
            public_key="valid_key",
            secret_key="sk_test_123",
            host="https://cloud.langfuse.com",
            enabled=False,
        )

        model = LangfuseModel(config)

        with pytest.raises(ValueError, match="Langfuse is not entirely configured"):
            model.enabled = True

    @patch("code_reviewer_agent.utils.langfuse.Langfuse")
    @patch("code_reviewer_agent.utils.langfuse.logfire")
    def test_enable_langfuse_import_error(self, mock_logfire, mock_langfuse) -> None:
        """Test enabling Langfuse with import error."""
        mock_langfuse.side_effect = ImportError("Module not found")

        config = LangfuseConfig(
            public_key="pk_test_123",
            secret_key="sk_test_123",
            host="https://cloud.langfuse.com",
            enabled=False,
        )

        model = LangfuseModel(config)

        with pytest.raises(ImportError, match="Langfuse import failed"):
            model.enabled = True

    @patch("code_reviewer_agent.utils.langfuse.Langfuse")
    @patch("code_reviewer_agent.utils.langfuse.logfire")
    def test_enable_langfuse_general_exception(self, mock_logfire, mock_langfuse) -> None:
        """Test enabling Langfuse with general exception."""
        mock_langfuse.side_effect = Exception("Connection failed")

        config = LangfuseConfig(
            public_key="pk_test_123",
            secret_key="sk_test_123",
            host="https://cloud.langfuse.com",
            enabled=False,
        )

        model = LangfuseModel(config)

        with pytest.raises(Exception, match="Langfuse initialization failed"):
            model.enabled = True

    def test_scrubbing_callback_preserve_session_id(self) -> None:
        """Test scrubbing callback preserves Langfuse session ID."""

        # Mock the match object
        mock_match = Mock()
        mock_match.path = ("attributes", "langfuse.session.id")
        mock_match.pattern_match.group.return_value = "session"
        mock_match.value = "session_123"

        result = LangfuseModel.scrubbing_callback(mock_match)

        assert result == "session_123"

    def test_scrubbing_callback_other_values(self) -> None:
        """Test scrubbing callback returns empty for other values."""
        # Mock the match object for non-session values
        mock_match = Mock()
        mock_match.path = ("attributes", "other.field")
        mock_match.pattern_match.group.return_value = "other"
        mock_match.value = "some_value"

        result = LangfuseModel.scrubbing_callback(mock_match)

        assert result == ""

    def test_scrubbing_callback_none_value(self) -> None:
        """Test scrubbing callback with None value."""
        # Mock the match object with None value
        mock_match = Mock()
        mock_match.path = ("attributes", "langfuse.session.id")
        mock_match.pattern_match.group.return_value = "session"
        mock_match.value = None

        result = LangfuseModel.scrubbing_callback(mock_match)

        assert result == ""
