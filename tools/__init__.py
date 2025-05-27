"""Tools package for the code review agent.

This package contains various tools for interacting with Git, parsing diffs,
and other code review related functionality.
"""

# Re-export models for backward compatibility
from models import PRDiffResponse, ReviewComment, FileDiff

# Import functions to make them available at the package level
from .diff_parsing import parse_unified_diff
from .git_operations import get_pr_diff, post_review_comment
from .llm_utils import analyze_with_llm, aggregate_review_comments
from .rate_limiting import TokenBucket, process_file_with_retry
from .utils import (
    log_info,
    log_error,
    _truncate_text,
    count_tokens,
    chunk_text,
    detect_languages,
    search_best_practices,
    get_review_instructions
)

__all__ = [
    'PRDiffResponse',
    'ReviewComment',
    'FileDiff',
    'parse_unified_diff',
    'get_pr_diff',
    'post_review_comment',
    'analyze_with_llm',
    'aggregate_review_comments',
    'TokenBucket',
    'process_file_with_retry',
    'log_info',
    'log_error',
    '_truncate_text',
    'count_tokens',
    'chunk_text',
    'detect_languages',
    'search_best_practices',
    'get_review_instructions'
]
