from __future__ import annotations as _annotations

import asyncio
import os
from dataclasses import dataclass

import httpx
import logfire
from pydantic_ai import Agent

from agent_tools import (
    get_pr_diff,
    post_review_comment,
    get_review_instructions,
    search_best_practices,
    detect_languages,
    aggregate_review_comments,
)
from agent_prompts import SYSTEM_PROMPT

logfire.configure(send_to_logfire='if-token-present')

@dataclass
class ReviewDeps:
    """Dependency holder for API clients and config for GitHub/GitLab"""
    http_client: httpx.AsyncClient
    platform: str  # 'github' or 'gitlab'
    github_token: str | None
    gitlab_token: str | None
    repository: str
    pr_id: int
    instructions_path: str
    log_level: str

code_review_agent = Agent(
    "openai:gpt-4o-mini",
    system_prompt=SYSTEM_PROMPT,
    deps_type=ReviewDeps,
    retries=2,
)

# Tool registrations
code_review_agent.add_tool(get_pr_diff)
code_review_agent.add_tool(post_review_comment)
code_review_agent.add_tool(get_review_instructions)
code_review_agent.add_tool(search_best_practices)
code_review_agent.add_tool(detect_languages)
code_review_agent.add_tool(aggregate_review_comments)

async def main():
    github_token = os.getenv('GITHUB_TOKEN')
    gitlab_token = os.getenv('GITLAB_TOKEN')
    platform = os.getenv('PLATFORM', 'github').lower()
    repository = os.getenv('REPOSITORY')
    pr_id = int(os.getenv('PR_ID', '0')) # TODO: Get PR ID from command line args
    instructions_path = os.getenv('INSTRUCTIONS_PATH', 'review_instructions.md')
    log_level = os.getenv('LOG_LEVEL', 'INFO')

    if not repository:
        raise ValueError("REPOSITORY environment variable is required")
    if not pr_id:
        raise ValueError("PR_ID environment variable is required")
    if platform not in ('github', 'gitlab'):
        raise ValueError("PLATFORM must be either 'github' or 'gitlab'")
    if platform == 'github' and not github_token:
        raise ValueError("GITHUB_TOKEN is required when PLATFORM is 'github'")
    if platform == 'gitlab' and not gitlab_token:
        raise ValueError("GITLAB_TOKEN is required when PLATFORM is 'gitlab'")

    async with httpx.AsyncClient() as http_client:
        deps = ReviewDeps(
            http_client=http_client,
            platform=platform,
            github_token=github_token,
            gitlab_token=gitlab_token,
            repository=repository,
            pr_id=pr_id,
            instructions_path=instructions_path,
            log_level=log_level,
        )

        # Run the agent
        await code_review_agent.run("Review this pull request", deps=deps)

if __name__ == "__main__":
    asyncio.run(main())
