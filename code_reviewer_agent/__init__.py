"""AI Code Review Agent.

An intelligent code review agent that analyzes pull requests on GitHub and GitLab,
providing detailed feedback based on custom review instructions and language-specific best practices.

This package provides the following main components:
- `review`: Main entry point for the code review agent
- `crawl`: Web crawler for documentation processing

"""

__version__ = "2.0.0"
__author__ = "Adraynrion"
__email__ = "adraynrion@citizenofai.com"

# Import main functionality to make it available at the package level
from code_reviewer_agent.services.code_reviewer import main as code_reviewer_main
from code_reviewer_agent.services.crawler import crawl_urls

# Export the main functions
review = code_reviewer_main
crawl = crawl_urls
__all__ = [
    "review",
    "crawl",
    "__version__",
]


def get_version() -> str:
    """Return the current version of the package."""
    return __version__
