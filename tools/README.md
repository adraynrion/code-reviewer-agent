# Code Review Agent Tools

This package contains various tools used by the code review agent, organized into logical modules for better maintainability.

## Package Structure

- `__init__.py` - Package initialization and public API exports
- `diff_parsing.py` - Utilities for parsing and processing unified diffs
- `git_operations.py` - Functions for interacting with Git and PR/MR systems
- `llm_utils.py` - LLM-related functionality for code analysis
- `rate_limiting.py` - Rate limiting utilities for API calls
- `utils.py` - General utility functions

## Usage

Import the tools you need from the package:

```python
from tools import (
    parse_unified_diff,
    get_pr_diff,
    post_review_comment,
    analyze_with_llm,
    aggregate_review_comments,
    detect_languages,
    search_best_practices,
    get_review_instructions
)
```

## Adding New Tools

1. Add new tools to the appropriate module based on their functionality.
2. Update the `__init__.py` file to expose any new public functions/classes.
3. Add comprehensive docstrings and type hints to all new functions/classes.
4. Add unit tests for new functionality.
