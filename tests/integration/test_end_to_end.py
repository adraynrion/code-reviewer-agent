from typing import Any
from unittest.mock import Mock, patch

import pytest

from code_reviewer_agent.config.config import Config
from code_reviewer_agent.models.base_types import CodeDiff, Repository, RequestId
from code_reviewer_agent.models.pydantic_config_models import ReviewerConfig
from code_reviewer_agent.models.reviewer_agent import ReviewerAgent
from code_reviewer_agent.services.github import GitHubReviewerService
from code_reviewer_agent.services.gitlab import GitLabReviewerService


class TestEndToEndIntegration:
    """Integration tests for complete workflow scenarios."""

    def test_config_to_reviewer_agent_flow(self, mock_config: Config) -> None:
        """Test complete flow from config to reviewer agent creation."""
        with patch(
            "code_reviewer_agent.models.reviewer_agent.InstructionPath"
        ) as mock_instruction_path:
            mock_instruction_path.return_value = ["Test instruction"]

            with patch("code_reviewer_agent.models.reviewer_agent.CrawlerReader"):
                with patch("code_reviewer_agent.models.reviewer_agent.print_header"):
                    with patch("code_reviewer_agent.models.reviewer_agent.print_debug"):
                        with patch(
                            "code_reviewer_agent.models.reviewer_agent.print_success"
                        ):
                            with patch(
                                "code_reviewer_agent.models.supabase.SupabaseModel"
                            ):
                                # Create reviewer agent from config
                                reviewer_agent = ReviewerAgent(mock_config)

        # Verify agent was created successfully
        assert reviewer_agent is not None
        assert reviewer_agent.agent is not None
        assert reviewer_agent._config == mock_config

    def test_github_service_initialization_flow(
        self, mock_reviewer_config: ReviewerConfig
    ) -> None:
        """Test GitHub service initialization with proper configuration."""
        repository = Repository("test/repo")
        request_id = RequestId(123)

        # Create GitHub service
        github_service = GitHubReviewerService(
            repository, request_id, mock_reviewer_config
        )

        # Verify initialization
        assert github_service.repository == repository
        assert github_service.request_id == request_id
        assert github_service.github_token == "test_github_token"

    def test_gitlab_service_initialization_flow(
        self, mock_reviewer_config: ReviewerConfig
    ) -> None:
        """Test GitLab service initialization with proper configuration."""
        # Update config for GitLab
        mock_reviewer_config.gitlab_token = "test_gitlab_token"
        mock_reviewer_config.gitlab_api_url = "https://gitlab.com/api/v4"

        repository = Repository("project/repo")
        request_id = RequestId(123)

        # Create GitLab service
        gitlab_service = GitLabReviewerService(
            repository, request_id, mock_reviewer_config
        )

        # Verify initialization
        assert gitlab_service.repository == repository
        assert gitlab_service.request_id == request_id
        assert gitlab_service.gitlab_token == "test_gitlab_token"
        assert gitlab_service.gitlab_api_url == "https://gitlab.com/api/v4"

    @pytest.mark.asyncio
    async def test_mock_review_workflow(
        self, mock_config: Config, mock_reviewer_config: ReviewerConfig
    ) -> None:
        """Test a complete mock review workflow."""
        repository = Repository("test/repo")
        request_id = RequestId(123)

        # Create services
        with patch(
            "code_reviewer_agent.models.reviewer_agent.InstructionPath"
        ) as mock_instruction_path:
            mock_instruction_path.return_value = []

            with patch("code_reviewer_agent.models.reviewer_agent.CrawlerReader"):
                with patch("code_reviewer_agent.models.reviewer_agent.print_header"):
                    with patch("code_reviewer_agent.models.reviewer_agent.print_debug"):
                        with patch(
                            "code_reviewer_agent.models.reviewer_agent.print_success"
                        ):
                            with patch(
                                "code_reviewer_agent.models.supabase.SupabaseModel"
                            ):
                                reviewer_agent = ReviewerAgent(mock_config)

        github_service = GitHubReviewerService(
            repository, request_id, mock_reviewer_config
        )

        # Mock the entire flow
        with patch.object(
            github_service, "request_files_analysis_from_api"
        ) as mock_fetch:
            with patch.object(github_service, "post_review_comments") as mock_post:
                mock_fetch.return_value = None
                mock_post.return_value = None

                # Simulate workflow
                github_service.request_files_analysis_from_api()
                await github_service.post_review_comments(CodeDiff(), Mock())

                # Verify calls were made
                mock_fetch.assert_called_once()
                mock_post.assert_called_once()

    def test_configuration_validation_flow(
        self, mock_config_data: dict[str, Any]
    ) -> None:
        """Test configuration validation across the system."""
        # Test that config models validate properly
        from code_reviewer_agent.models.pydantic_config_models import ConfigModel

        config_model = ConfigModel(**mock_config_data)

        # Verify all required fields are present
        assert config_model.reviewer.github_token == "test_github_token"
        assert config_model.reviewer.llm.api_key == "test_api_key"
        assert config_model.supabase.url == "https://test.supabase.co"
        assert config_model.langfuse.enabled is False

    def test_language_detection_integration(self) -> None:
        """Test language detection integration with file processing."""
        from code_reviewer_agent.models.base_types import FilesPath
        from code_reviewer_agent.utils.language_utils import LanguageUtils

        files = FilesPath(("src/main.py", "frontend/app.js", "styles/main.css"))

        with patch("os.path.basename", side_effect=lambda x: x.split("/")[-1]):
            languages = LanguageUtils.get_file_languages(files)

        # Verify language detection works end-to-end
        assert "src/main.py" in languages
        assert "frontend/app.js" in languages
        assert "styles/main.css" in languages
        assert languages["src/main.py"] == {"python"}
        assert languages["frontend/app.js"] == {"javascript"}
        assert languages["styles/main.css"] == {"css"}

    def test_rich_utils_integration(self) -> None:
        """Test Rich utilities integration."""
        from code_reviewer_agent.utils.rich_utils import (
            print_error,
            print_info,
            print_success,
        )

        with patch("code_reviewer_agent.utils.rich_utils.console.print") as mock_print:
            print_success("Test success")
            print_error("Test error")
            print_info("Test info")

            # Verify all calls were made with proper formatting
            assert mock_print.call_count == 3
            calls = [str(call) for call in mock_print.call_args_list]
            assert any("✓" in call for call in calls)  # Success symbol
            assert any("✗" in call for call in calls)  # Error symbol
            assert any("ℹ" in call for call in calls)  # Info symbol

    def test_base_types_integration(self) -> None:
        """Test base types validation integration."""
        from code_reviewer_agent.models.base_types import (
            ApiKey,
            GitHubToken,
            Repository,
            RequestId,
        )

        # Test that all base types work together
        github_token = GitHubToken("test_token")
        repository = Repository("test/repo")
        request_id = RequestId(123)
        api_key = ApiKey("test_api_key")

        # Verify they maintain their values and types
        assert github_token == "test_token"
        assert repository == "test/repo"
        assert request_id == 123
        assert api_key == "test_api_key"

        # Verify they're proper instances
        assert isinstance(github_token, str)
        assert isinstance(repository, str)
        assert isinstance(request_id, int)
        assert isinstance(api_key, str)

    def test_error_propagation_flow(
        self, mock_reviewer_config: ReviewerConfig, mock_requests_get: Mock
    ) -> None:
        """Test that errors propagate correctly through the system."""
        repository = Repository("test/repo")
        request_id = RequestId(123)

        # Mock a 404 error
        error_response = Mock()
        error_response.status_code = 404
        error_response.text = "Not Found"
        mock_requests_get.return_value = error_response

        github_service = GitHubReviewerService(
            repository, request_id, mock_reviewer_config
        )

        with patch("code_reviewer_agent.services.github.print_section"):
            with patch("code_reviewer_agent.services.github.print_info"):
                with patch("code_reviewer_agent.services.github.print_error"):
                    with pytest.raises(Exception) as exc_info:
                        github_service.request_files_analysis_from_api()

        # Verify error propagation
        assert "Failed to fetch pull request commits" in str(exc_info.value)

    def test_system_components_compatibility(self) -> None:
        """Test that all system components are compatible with each other."""
        # This test verifies that major components can be instantiated together
        # without conflicts

        from code_reviewer_agent.models.base_types import (
            GitHubToken,
            Repository,
            RequestId,
        )
        from code_reviewer_agent.models.pydantic_config_models import (
            LLMConfig,
            ReviewerConfig,
        )

        # Create components
        token = GitHubToken("test_token")
        repo = Repository("test/repo")
        req_id = RequestId(123)

        llm_config = LLMConfig(api_key="test_key")
        reviewer_config = ReviewerConfig(
            github_token=str(token), repository=str(repo), llm=llm_config
        )

        # Verify compatibility
        assert reviewer_config.github_token == token
        assert reviewer_config.repository == repo
        assert reviewer_config.llm.api_key == "test_key"
