"""AI Code Review Agent.

An intelligent code review agent that analyzes pull requests on GitHub and GitLab,
providing detailed feedback based on custom review instructions and language-specific best practices.

This package provides the following main components:
- `code_reviewer_agent`: Main entry point for the code review agent
- `crawler_agent`: Web crawler for documentation processing
- `setup-code-reviewer`: Interactive setup script for configuration

"""

__version__ = "1.0.0"
__author__ = "Adraynrion"
__email__ = "adraynrion@citizenofai.com"

# Import main functionality to make it available at the package level
from .services.code_reviewer import review_code
from .services.crawler import crawl_urls

# Export the main functions
__all__ = [
    "review_code",
    "crawl_urls",
    "__version__",
]


def get_version() -> str:
    """Return the current version of the package."""
    return __version__
