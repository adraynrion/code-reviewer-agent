from code_reviewer_agent.config.config import Config
from code_reviewer_agent.models.base_types import (
    InstructionsPath,
    Platform,
    Repository,
    RequestId,
    Token,
    Url,
)


class ConfigurationManager:
    """Manages configuration validation and platform-specific settings.

    This class handles the single responsibility of configuration management, including
    validation of platform-specific credentials and settings. Following the Single
    Responsibility Principle, it only handles configuration concerns and delegates other
    responsibilities to appropriate classes.

    """

    def __init__(
        self,
        config: Config,
        platform: Platform,
        repository: Repository,
        request_id: RequestId,
        instructions_path: InstructionsPath,
    ) -> None:
        """Initialize configuration manager with validation.

        Args:
            config: The main configuration object
            platform: The platform identifier
            repository: The repository identifier
            request_id: The pull/merge request ID
            instructions_path: Path to additional instructions

        Raises:
            ValueError: If configuration validation fails

        """
        self._config = config
        self._validate_and_set_config(
            config, platform, repository, request_id, instructions_path
        )

    def _validate_and_set_config(
        self,
        config: Config,
        platform: Platform,
        repository: Repository,
        request_id: RequestId,
        instructions_path: InstructionsPath,
    ) -> None:
        """Validate and set configuration values.

        Args:
            config: The main configuration object
            platform: The platform identifier
            repository: The repository identifier
            request_id: The pull/merge request ID
            instructions_path: Path to additional instructions

        Raises:
            ValueError: If configuration validation fails

        """
        reviewer_config = config.schema.reviewer

        # Initialize tokens and URLs
        self._github_token = Token(reviewer_config.github_token)
        self._gitlab_token = Token(reviewer_config.gitlab_token)
        self._gitlab_url = Url(reviewer_config.gitlab_api_url)

        # Set platform with validation
        self.platform = Platform(platform or reviewer_config.platform)

        # Set other configuration values
        self._repository = Repository(repository or reviewer_config.repository)
        self._instructions_path = InstructionsPath(
            instructions_path or reviewer_config.instruction_dir_path
        )
        self._request_id = RequestId(request_id)

    @property
    def config(self) -> Config:
        """Get the main configuration object."""
        return self._config

    @property
    def github_token(self) -> Token:
        """Get the GitHub token."""
        return self._github_token

    @github_token.setter
    def github_token(self, value: str) -> None:
        """Set the GitHub token."""
        self._github_token = Token(value)

    @property
    def gitlab_token(self) -> Token:
        """Get the GitLab token."""
        return self._gitlab_token

    @gitlab_token.setter
    def gitlab_token(self, value: str) -> None:
        """Set the GitLab token."""
        self._gitlab_token = Token(value)

    @property
    def gitlab_url(self) -> Url:
        """Get the GitLab URL."""
        return self._gitlab_url

    @gitlab_url.setter
    def gitlab_url(self, value: str) -> None:
        """Set the GitLab URL."""
        self._gitlab_url = Url(value)

    @property
    def platform(self) -> Platform:
        """Get the platform identifier."""
        return self._platform

    @platform.setter
    def platform(self, value: Platform) -> None:
        """Set and validate the platform identifier.

        Args:
            value: The platform identifier

        Raises:
            ValueError: If platform is invalid or required tokens are missing

        """
        formatted_value = value.lower().strip()
        if formatted_value not in ("github", "gitlab"):
            raise ValueError("Invalid platform. Must be either 'github' or 'gitlab'.")

        if formatted_value == "github" and not self.github_token:
            raise ValueError(
                "github_token config variable is required when platform is 'github'."
            )

        if formatted_value == "gitlab" and not self.gitlab_token:
            raise ValueError(
                "gitlab_token config variable is required when platform is 'gitlab'."
            )

        self._platform = Platform(formatted_value)

    @property
    def repository(self) -> Repository:
        """Get the repository identifier."""
        return self._repository

    @repository.setter
    def repository(self, value: str) -> None:
        """Set the repository identifier."""
        self._repository = Repository(value)

    @property
    def instructions_path(self) -> InstructionsPath:
        """Get the instructions path."""
        return self._instructions_path

    @instructions_path.setter
    def instructions_path(self, value: str) -> None:
        """Set the instructions path."""
        self._instructions_path = InstructionsPath(value)

    @property
    def request_id(self) -> RequestId:
        """Get the request ID."""
        return self._request_id

    @request_id.setter
    def request_id(self, value: int) -> None:
        """Set the request ID."""
        self._request_id = RequestId(value)

    def get_platform_credentials(self) -> dict[str, Token]:
        """Get platform-specific credentials.

        Returns:
            Dictionary containing platform-specific credentials

        """
        return {
            "github_token": self.github_token,
            "gitlab_token": self.gitlab_token,
        }

    def validate_platform_config(self) -> None:
        """Validate platform-specific configuration.

        Raises:
            ValueError: If platform configuration is invalid

        """
        if self.platform == "github" and not self.github_token:
            raise ValueError(
                "github_token config variable is required when platform is 'github'."
            )

        if self.platform == "gitlab" and not self.gitlab_token:
            raise ValueError(
                "gitlab_token config variable is required when platform is 'gitlab'."
            )
