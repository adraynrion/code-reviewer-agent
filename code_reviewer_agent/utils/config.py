"""Configuration management for the code review agent."""

import os
from pathlib import Path

from dotenv import load_dotenv

from ..utils.rich_utils import print_error, print_info, print_section

# Load environment variables from .env file if it exists
load_dotenv()


class Config:
    """Configuration class for the code review agent."""

    # LLM Provider Configuration
    PROVIDER: str = os.getenv("PROVIDER", "OpenAI")
    MODEL_CHOICE: str = os.getenv("MODEL_CHOICE", "gpt-4-turbo-preview")
    BASE_URL: str = os.getenv("BASE_URL", "https://api.openai.com/v1")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")

    # Supabase Configuration
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")

    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

    # Local File Storage
    LOCAL_FILE_DIR: str = os.getenv("LOCAL_FILE_DIR", str(Path.cwd() / "instructions"))

    # Logging Settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # Git Provider Configuration
    PLATFORM: str = os.getenv("PLATFORM", "github")
    REPOSITORY: str = os.getenv("REPOSITORY", "")
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")
    GITLAB_TOKEN: str = os.getenv("GITLAB_TOKEN", "")
    GITLAB_API_URL: str = os.getenv("GITLAB_API_URL", "https://gitlab.com/api/v4")

    # Langfuse Configuration (Optional)
    LANGFUSE_PUBLIC_KEY: str = os.getenv("LANGFUSE_PUBLIC_KEY", "")
    LANGFUSE_SECRET_KEY: str = os.getenv("LANGFUSE_SECRET_KEY", "")
    LANGFUSE_HOST: str = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

    def validate(self) -> bool:
        """Validate that all required configuration is present.

        Returns:
            bool: True if all required configuration is present, False otherwise

        """
        required_vars = [
            ("PROVIDER", self.PROVIDER),
            ("MODEL_CHOICE", self.MODEL_CHOICE),
            ("BASE_URL", self.BASE_URL),
            ("LLM_API_KEY", self.LLM_API_KEY),
            ("SUPABASE_URL", self.SUPABASE_URL),
            ("SUPABASE_KEY", self.SUPABASE_KEY),
            ("OPENAI_API_KEY", self.OPENAI_API_KEY),
            ("EMBEDDING_MODEL", self.EMBEDDING_MODEL),
            ("LOG_LEVEL", self.LOG_LEVEL),
            ("LANGFUSE_PUBLIC_KEY", self.LANGFUSE_PUBLIC_KEY),
            ("LANGFUSE_SECRET_KEY", self.LANGFUSE_SECRET_KEY),
            ("LANGFUSE_HOST", self.LANGFUSE_HOST),
        ]

        missing = [name for name, value in required_vars if not value]
        if missing:
            print_error(
                f"Error: Missing required environment variables: {', '.join(missing)}"
            )
            return False
        return True

    def validate_code_review_process(self) -> bool:
        """Validate that all required configuration for the code review process is
        present.

        Returns:
            bool: True if all required configuration is present, False otherwise

        """
        required_vars = [
            ("LOCAL_FILE_DIR", self.LOCAL_FILE_DIR),
            ("PLATFORM", self.PLATFORM),
            ("REPOSITORY", self.REPOSITORY),
            ("GITHUB_TOKEN", self.GITHUB_TOKEN),
            ("GITLAB_TOKEN", self.GITLAB_TOKEN),
            ("GITLAB_API_URL", self.GITLAB_API_URL),
        ]

        missing = [name for name, value in required_vars if not value]
        if missing:
            print_error(
                f"Error: Missing required environment variables for code review process: {', '.join(missing)}"
            )
            return False
        return self.validate() and True

    def print_config(self) -> None:
        """Print the current configuration (without sensitive data)."""
        print_section("Current Configuration:", "⚙️")
        print_info(f"  Provider: {self.PROVIDER}")
        print_info(f"  Base URL: {self.BASE_URL}")
        print_info(f"  Model: {self.MODEL_CHOICE}")
        print_info(f"  Embedding Model: {self.EMBEDDING_MODEL}")
        print_info(f"  Local File Directory: {self.LOCAL_FILE_DIR}")
        print_info(f"  Log Level: {self.LOG_LEVEL}")
        print_info(f"  Debug Mode: {self.DEBUG}")


# Create a global config instance
config = Config()
