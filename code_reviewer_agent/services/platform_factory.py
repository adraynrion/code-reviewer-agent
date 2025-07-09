from code_reviewer_agent.models.base_types import Platform, Repository, RequestId
from code_reviewer_agent.models.pydantic_config_models import ReviewerConfig
from code_reviewer_agent.services.github import GitHubReviewerService
from code_reviewer_agent.services.gitlab import GitLabReviewerService
from code_reviewer_agent.services.repository import RepositoryService


class PlatformServiceFactory:
    """Factory for creating platform-specific repository services.

    This factory implements the Factory pattern to create platform-specific services
    without exposing the creation logic to clients, following the Open/Closed Principle
    by allowing new platforms to be added without modifying existing code.

    """

    @staticmethod
    def create_service(
        platform: Platform,
        repository: Repository,
        request_id: RequestId,
        config: ReviewerConfig,
    ) -> RepositoryService:
        """Create a platform-specific repository service.

        Args:
            platform: The platform identifier ('github' or 'gitlab')
            repository: The repository identifier
            request_id: The pull/merge request ID
            config: The reviewer configuration

        Returns:
            A platform-specific repository service instance

        Raises:
            ValueError: If the platform is not supported

        """
        if platform == "github":
            return GitHubReviewerService(repository, request_id, config)
        elif platform == "gitlab":
            return GitLabReviewerService(repository, request_id, config)
        else:
            raise ValueError("Invalid platform. Must be either 'github' or 'gitlab'.")
