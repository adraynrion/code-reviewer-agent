"""AI Code Review Agent.

An intelligent code review agent that analyzes pull requests on GitHub and GitLab,
providing detailed feedback based on custom review instructions and language-specific
best practices.

"""

__version__ = "2.0.0"
__author__ = "Adraynrion"
__email__ = "adraynrion@citizenofai.com"


def get_version() -> str:
    """Return the current version of the package."""
    return __version__
