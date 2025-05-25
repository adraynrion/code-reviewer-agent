"""Tools for the code review agent to interact with GitHub/GitLab and analyze code."""

from typing import Any, Dict, List, Optional, TypedDict

from pydantic import BaseModel

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

class PRDiffResponse(BaseModel):
    """Response model for get_pr_diff."""
    files: List[FileDiff]
    base_sha: str
    head_sha: str

async def get_pr_diff(
    deps: Any,
    repository: str,
    pr_id: int,
) -> PRDiffResponse:
    """
    Get the diff for a pull request.

    Args:
        deps: The dependency injection container
        repository: The repository in format 'owner/repo' or 'group/project' for GitLab
        pr_id: The pull/merge request number

    Returns:
        PRDiffResponse containing the diff information
    """
    if deps.platform == 'github':
        url = f"https://api.github.com/repos/{repository}/pulls/{pr_id}"
        headers = {
            "Authorization": f"token {deps.github_token}",
            "Accept": "application/vnd.github.v3.diff"
        }
        async with deps.http_client.get(url, headers=headers) as response:
            response.raise_for_status()
            diff_text = response.text
            # Parse diff text into structured format
            # (simplified - in practice you'd want a proper diff parser)
            # TODO: Implement diff parsing
            files = []
            current_file = None
            for line in diff_text.split('\n'):
                if line.startswith('diff --git'):
                    if current_file:
                        files.append(current_file)
                    filename = line.split(' b/')[-1]
                    current_file = {
                        'filename': filename,
                        'status': 'modified',  # Simplified
                        'additions': 0,
                        'deletions': 0,
                        'patch': '',
                        'previous_filename': None
                    }
                elif current_file and line.startswith('+'):
                    current_file['additions'] += 1
                    current_file['patch'] += line + '\n'
                elif current_file and line.startswith('-'):
                    current_file['deletions'] += 1
                    current_file['patch'] += line + '\n'

            if current_file:
                files.append(current_file)

            return PRDiffResponse(
                files=files,
                base_sha='',  # Would come from API in real implementation
                head_sha='',   # Would come from API in real implementation
            )
    else:  # GitLab
        # TODO: Similar implementation for GitLab
        pass

    return PRDiffResponse(files=[], base_sha='', head_sha='')

async def post_review_comment(
    deps: Any,
    repository: str,
    pr_id: int,
    comments: List[ReviewComment],
) -> bool:
    """
    Post review comments to a pull request.

    Args:
        deps: The dependency injection container
        repository: The repository in format 'owner/repo' or 'group/project' for GitLab
        pr_id: The pull/merge request number
        comments: List of comments to post

    Returns:
        bool: True if comments were posted successfully
    """
    if deps.platform == 'github':
        url = f"https://api.github.com/repos/{repository}/pulls/{pr_id}/reviews"
        headers = {
            "Authorization": f"token {deps.github_token}",
            "Accept": "application/vnd.github.v3+json"
        }

        # Convert comments to GitHub format
        github_comments = [
            {
                "path": comment["path"],
                "position": comment["line"],
                "body": comment["body"]
            }
            for comment in comments
        ]

        payload = {
            "event": "COMMENT",
            "comments": github_comments
        }

        async with deps.http_client.post(url, headers=headers, json=payload) as response:
            response.raise_for_status()
            return True
    else:  # GitLab
        # TODO: Similar implementation for GitLab
        pass

    return False

async def get_review_instructions(
    deps: Any,
    instructions_path: str,
) -> str:
    """
    Load custom review instructions from a markdown file.

    Args:
        deps: The dependency injection container
        instructions_path: Path to the markdown file with review instructions

    Returns:
        str: The contents of the instructions file
    """
    try:
        with open(instructions_path, 'r') as f:
            return f.read()
    except Exception as e:
        print(f"Warning: Could not load review instructions: {e}")
        return ""

async def search_best_practices(
    deps: Any,
    language: str,
    framework: Optional[str] = None,
) -> str:
    """
    Search for language/framework specific best practices.

    Args:
        deps: The dependency injection container
        language: The programming language to search for
        framework: Optional framework (e.g., 'django', 'react')

    Returns:
        str: Best practices information
    """
    # In a real implementation, this would search the web or a knowledge base
    # For now, return some placeholder text
    # TODO: Implement best practices search
    return f"Best practices for {language}{' with ' + framework if framework else ''} would be retrieved here."

async def detect_languages(
    deps: Any,
    files: List[FileDiff],
) -> List[str]:
    """
    Detect programming languages from file extensions in the diff.

    Args:
        deps: The dependency injection container
        files: List of files in the diff

    Returns:
        List of detected programming languages
    """
    extensions = set()
    for file in files:
        if '.' in file['filename']:
            ext = file['filename'].split('.')[-1].lower()
            extensions.add(ext)

    # Map extensions to languages
    ext_to_lang = {
        'py': 'Python',
        'js': 'JavaScript',
        'jsx': 'JavaScript',
        'ts': 'TypeScript',
        'tsx': 'TypeScript',
        'java': 'Java',
        'go': 'Go',
        'rb': 'Ruby',
        'php': 'PHP',
        'cs': 'C#',
        'c': 'C',
        'cpp': 'C++',
        'h': 'C/C++',
        'hpp': 'C++',
        'swift': 'Swift',
        'kt': 'Kotlin',
        'rs': 'Rust',
        'sh': 'Shell',
        'sql': 'SQL',
        'html': 'HTML',
        'css': 'CSS',
        'scss': 'SCSS',
        'json': 'JSON',
        'yaml': 'YAML',
        'yml': 'YAML',
        'toml': 'TOML',
        'md': 'Markdown',
        # TODO : Add vuejs
    }

    languages = set()
    for ext in extensions:
        if ext in ext_to_lang:
            languages.add(ext_to_lang[ext])

    return list(languages)

async def aggregate_review_comments(
    deps: Any,
    diff: PRDiffResponse,
    custom_instructions: str,
    best_practices: Dict[str, str],
) -> List[ReviewComment]:
    """
    Generate review comments based on the diff, custom instructions, and best practices.

    This is where the AI would analyze the code and generate comments.
    In a real implementation, this would use an LLM to analyze the code.

    Args:
        deps: The dependency injection container
        diff: The PR diff
        custom_instructions: Custom review instructions
        best_practices: Language-specific best practices

    Returns:
        List of review comments
    """
    # This is a placeholder implementation
    # In a real implementation, you would use an LLM to analyze the code
    # and generate meaningful comments based on the diff, custom instructions, and best practices

    comments = []

    # TODO: Implement review comment generation + replace prompt keywords

    # Example: Add a comment for each file with changes
    for file in diff.files:
        if file['additions'] > 100:
            comments.append({
                'path': file['filename'],
                'line': 1,
                'body': 'This file has a large number of changes. Consider breaking it into smaller, more focused changes.',
                'side': 'RIGHT'
            })

    return comments
