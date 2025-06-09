"""Configuration management for the code review agent."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()


class Config:
    """Configuration class for the code review agent."""

    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")

    # Supabase Configuration
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")

    # Langfuse Configuration (Optional)
    LANGFUSE_PUBLIC_KEY: str = os.getenv("LANGFUSE_PUBLIC_KEY", "")
    LANGFUSE_SECRET_KEY: str = os.getenv("LANGFUSE_SECRET_KEY", "")
    LANGFUSE_HOST: str = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

    # Application Settings
    LOCAL_FILE_DIR: str = os.getenv("LOCAL_FILE_DIR", str(Path.cwd() / "data"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    @classmethod
    def validate(cls) -> bool:
        """Validate that all required configuration is present.

        Returns:
            bool: True if all required configuration is present, False otherwise

        """
        required_vars = [
            ("OPENAI_API_KEY", cls.OPENAI_API_KEY),
            ("SUPABASE_URL", cls.SUPABASE_URL),
            ("SUPABASE_KEY", cls.SUPABASE_KEY),
        ]

        missing = [name for name, value in required_vars if not value]
        if missing:
            print(
                f"Error: Missing required environment variables: {', '.join(missing)}"
            )
            return False
        return True

    @classmethod
    def print_config(cls) -> None:
        """Print the current configuration (without sensitive data)."""
        print("Current Configuration:")
        print(f"  OpenAI Model: {cls.OPENAI_MODEL}")
        print(f"  Local File Directory: {cls.LOCAL_FILE_DIR}")
        print(f"  Log Level: {cls.LOG_LEVEL}")
        print(f"  Debug Mode: {cls.DEBUG}")


# Create a global config instance
config = Config()
