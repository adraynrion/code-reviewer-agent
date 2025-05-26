"""Pull Request related data models."""
from typing import List, Optional, TypedDict
from dataclasses import dataclass

class FileDiff(TypedDict):
    """Represents a file's diff in a PR."""
    filename: str
    status: str  # 'added', 'modified', 'removed', 'renamed'
    additions: int
    deletions: int
    patch: Optional[str]
    previous_filename: Optional[str]

class ReviewComment(TypedDict):
    """Represents a comment on a PR."""
    path: str
    line: int
    body: str
    side: str = 'RIGHT'  # 'LEFT' or 'RIGHT' for GitHub, 'old' or 'new' for GitLab

@dataclass
class PRDiffResponse:
    """Response model for get_pr_diff."""
    files: List[FileDiff]
    base_sha: str
    head_sha: str
