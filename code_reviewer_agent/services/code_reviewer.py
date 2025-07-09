from pydantic_ai import Agent

from code_reviewer_agent.config.config import Config
from code_reviewer_agent.models.base_types import (
    InstructionsPath,
    Platform,
    Repository,
    RequestId,
    Token,
    Url,
)
from code_reviewer_agent.models.reviewer_agent import ReviewerAgent
from code_reviewer_agent.services.base_service import BaseService
from code_reviewer_agent.services.configuration_manager import ConfigurationManager
from code_reviewer_agent.services.platform_factory import PlatformServiceFactory
from code_reviewer_agent.services.repository import RepositoryService
from code_reviewer_agent.services.review_orchestrator import ReviewOrchestrator


class CodeReviewService(BaseService):
    """Facade for code review operations.

    This class provides a thin facade that maintains backward compatibility with the
    existing CLI interface while delegating actual work to the SOLID-compliant classes.
    Following the Facade pattern, it simplifies the interface to the underlying
    subsystem.

    """

    def __init__(
        self,
        platform: Platform,
        repository: Repository,
        request_id: RequestId,
        instructions_path: InstructionsPath,
    ) -> None:
        super().__init__(Config())

        # Initialize dependencies following SOLID principles
        self._config_manager = ConfigurationManager(
            self.config, platform, repository, request_id, instructions_path
        )
        self._platform_factory = PlatformServiceFactory()
        self._reviewer_agent = ReviewerAgent(self.config)

        # Create orchestrator with dependencies
        self._orchestrator = ReviewOrchestrator(
            self._config_manager,
            self._platform_factory,
            self._reviewer_agent,
        )

    @property
    def agent(self) -> Agent[None, str]:
        """Get the AI agent for code review."""
        return self._reviewer_agent.agent

    @property
    def debug(self) -> bool:
        """Get debug mode status."""
        return self._reviewer_agent.debug

    @property
    def github_token(self) -> Token:
        """Get the GitHub token."""
        return self._config_manager.github_token

    @github_token.setter
    def github_token(self, value: str) -> None:
        """Set the GitHub token."""
        self._config_manager.github_token = value

    @property
    def gitlab_token(self) -> Token:
        """Get the GitLab token."""
        return self._config_manager.gitlab_token

    @gitlab_token.setter
    def gitlab_token(self, value: str) -> None:
        """Set the GitLab token."""
        self._config_manager.gitlab_token = value

    @property
    def gitlab_url(self) -> Url:
        """Get the GitLab URL."""
        return self._config_manager.gitlab_url

    @gitlab_url.setter
    def gitlab_url(self, value: str) -> None:
        """Set the GitLab URL."""
        self._config_manager.gitlab_url = value

    @property
    def platform(self) -> Platform:
        """Get the platform identifier."""
        return self._config_manager.platform

    @platform.setter
    def platform(self, value: Platform) -> None:
        """Set the platform identifier."""
        self._config_manager.platform = value

    @property
    def repository(self) -> Repository:
        """Get the repository identifier."""
        return self._config_manager.repository

    @repository.setter
    def repository(self, value: str) -> None:
        """Set the repository identifier."""
        self._config_manager.repository = value

    @property
    def instructions_path(self) -> InstructionsPath:
        """Get the instructions path."""
        return self._config_manager.instructions_path

    @instructions_path.setter
    def instructions_path(self, value: str) -> None:
        """Set the instructions path."""
        self._config_manager.instructions_path = value

    @property
    def request_id(self) -> RequestId:
        """Get the request ID."""
        return self._config_manager.request_id

    @request_id.setter
    def request_id(self, value: int) -> None:
        """Set the request ID."""
        self._config_manager.request_id = value

    @property
    def repository_service(self) -> RepositoryService:
        """Get the repository service."""
        return self._orchestrator.repository_service

    @repository_service.setter
    def repository_service(self, platform: Platform) -> None:
        """Set the repository service based on platform."""
        # This setter is maintained for compatibility but delegates to the factory
        self._orchestrator._repository_service = self._platform_factory.create_service(
            platform,
            self._config_manager.repository,
            self._config_manager.request_id,
            self._config_manager.config.schema.reviewer,
        )

    async def main(self) -> None:
        """Main entry point for code review process.

        This method maintains backward compatibility with the existing CLI interface
        while delegating the actual work to the orchestrator.

        """
        await self._orchestrator.orchestrate_review()
