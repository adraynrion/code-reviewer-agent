"""Git and PR operations for the code review agent."""

import asyncio
import logging
import random
from typing import List, Optional
from langfuse_decorators import track_tool
from pydantic_ai import RunContext
from models import PRDiffResponse, ReviewComment
from models.deps import ReviewDeps
from .utils import log_info, log_error
from .diff_parsing import parse_unified_diff

# Configure logger
logger = logging.getLogger(__name__)

@track_tool(name="get_pr_diff", metadata={"component": "git_client"})
async def get_pr_diff(
    context: RunContext[ReviewDeps],
    repository: str,
    pr_id: int,
    max_files: int = 20,
    max_chunk_size: int = 5000,
    deps: Optional[ReviewDeps] = None,
) -> PRDiffResponse:
    """
    Get the diff for a pull request, handling large PRs by processing in chunks.

    Args:
        context: The dependency injection container
        repository: The repository in format 'owner/repo' or 'group/project' for GitLab
        pr_id: The pull/merge request number
        max_files: Maximum number of files to process in one go (reduced to 20 to avoid rate limits)
        max_chunk_size: Maximum diff size in characters per chunk (reduced to 5000 to avoid rate limits)
        deps: Optional dependencies (will be extracted from context if not provided)

    Returns:
        PRDiffResponse containing the diff information
    """
    try:
        # Use deps from context if not provided directly
        if deps is None and hasattr(context, 'deps'):
            deps = context.deps

        log_info(f"Fetching PR diff for repository: {repository}, PR: {pr_id}")

        if deps is None:
            raise ValueError("No dependencies provided. Please ensure the agent is initialized with the correct dependencies.")

        platform = deps.platform if hasattr(deps, 'platform') else 'github'  # Default to github if not specified

        # Add delay to respect rate limits
        await asyncio.sleep(random.uniform(0.5, 1.5))

        # Get the diff from the appropriate platform client
        if platform == 'gitlab':
            if not hasattr(deps, 'gitlab_client') or deps.gitlab_client is None:
                if not deps.gitlab_token:
                    raise ValueError("GitLab token is required but not provided")
                # Initialize GitLab client here if needed
                # deps.gitlab_client = GitLabClient(deps.gitlab_token)
                raise NotImplementedError("GitLab integration is not implemented yet")
            diff = await deps.gitlab_client.get_merge_request_diff(repository, pr_id)
        else:  # Default to GitHub
            if not hasattr(deps, 'github_client') or deps.github_client is None:
                if not deps.github_token:
                    raise ValueError("GitHub token is required but not provided")
                # Initialize GitHub client here if needed
                # For now, we'll use a simple HTTP client to fetch the diff
                headers = {
                    "Authorization": f"token {deps.github_token}",
                    "Accept": "application/vnd.github.v3.diff"
                }
                url = f"https://api.github.com/repos/{repository}/pulls/{pr_id}.diff"
                response = await deps.http_client.get(url, headers=headers)
                response.raise_for_status()
                diff = response.text
            else:
                diff = await deps.github_client.get_pull_request_diff(repository, pr_id)

        # Parse the diff
        parsed_files = parse_unified_diff(diff)

        # Limit the number of files to process
        if len(parsed_files) > max_files:
            log_info(f"PR contains {len(parsed_files)} files, limiting to first {max_files} files")
            parsed_files = parsed_files[:max_files]

        # For now, we'll use empty strings for base_sha and head_sha
        # In a real implementation, we would get these from the PR details
        response = PRDiffResponse(
            files=parsed_files,
            base_sha="",  # We'll need to get this from the PR details
            head_sha=""   # We'll need to get this from the PR details
        )

        return response

    except Exception as e:
        log_error(f"Error getting PR diff: {str(e)}", exc_info=e)
        raise

@track_tool(name="post_review_comment", metadata={"component": "git_client"})
async def post_review_comment(
    context: RunContext[ReviewDeps],
    repository: str,
    pr_id: int,
    comments: List[ReviewComment],
    deps: ReviewDeps = None,
) -> None:
    """
    Post review comments to a pull/merge request.

    Args:
        context: The dependency injection container
        repository: The repository in format 'owner/repo' or 'group/project' for GitLab
        pr_id: The pull/merge request number
        comments: List of ReviewComment objects to post
        deps: Optional dependencies (will be extracted from context if not provided)
    """
    try:
        # Use deps from context if not provided directly
        if deps is None and hasattr(context, 'deps'):
            deps = context.deps

        if deps is None:
            raise ValueError("No dependencies provided. Please ensure the agent is initialized with the correct dependencies.")

        platform = deps.platform if hasattr(deps, 'platform') else 'github'  # Default to github if not specified

        # Convert comments to the format expected by the platform
        formatted_comments = []
        for comment in comments:
            formatted_comment = {
                'path': comment.file_path,
                'line': comment.line_number,
                'body': f"**{comment.comment_type.upper()}**: {comment.comment}"
            }
            if comment.suggestion:
                formatted_comment['body'] += f"\n\n**Suggestion**:\n```suggestion\n{comment.suggestion}\n```"
            formatted_comments.append(formatted_comment)

        # Post comments to the appropriate platform
        if platform == 'gitlab':
            await deps.gitlab_client.create_merge_request_comment(
                repository,
                pr_id,
                "\n\n---\n\n".join([c['body'] for c in formatted_comments])
            )
        else:  # Default to GitHub
            # Group comments by file and line to create review threads
            comments_by_file_line = {}
            for comment in formatted_comments:
                key = (comment['path'], comment['line'])
                if key not in comments_by_file_line:
                    comments_by_file_line[key] = []
                comments_by_file_line[key].append(comment['body'])

            # Create review with comments
            review_comments = [
                {
                    'path': path,
                    'position': line,
                    'body': "\n\n---\n\n".join(comments)
                }
                for (path, line), comments in comments_by_file_line.items()
            ]

            await deps.github_client.create_pull_request_review(
                repository,
                pr_id,
                {
                    'event': 'COMMENT',
                    'body': 'Code review completed',
                    'comments': review_comments
                }
            )

    except Exception as e:
        log_error(f"Error posting review comment: {str(e)}", exc_info=e)
        raise
