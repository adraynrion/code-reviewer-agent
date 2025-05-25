from __future__ import annotations as _annotations

import argparse
import asyncio
import os
import sys
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

def parse_arguments():
    parser = argparse.ArgumentParser(description='AI Code Review Agent')
    parser.add_argument(
        '--pr-id',
        type=int,
        required=True,
        help='Pull/Merge Request ID to review'
    )
    parser.add_argument(
        '--repository',
        type=str,
        help='Repository in format owner/repo (overrides REPOSITORY env var)'
    )
    parser.add_argument(
        '--platform',
        type=str,
        choices=['github', 'gitlab'],
        help='Platform: github or gitlab (overrides PLATFORM env var)'
    )
    parser.add_argument(
        '--instructions',
        type=str,
        default='review_instructions.md',
        help='Path to custom review instructions file (default: review_instructions.md)'
    )
    parser.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help='Logging level (default: INFO)'
    )
    return parser.parse_args()

async def main():
    args = parse_arguments()
    
    github_token = os.getenv('GITHUB_TOKEN')
    gitlab_token = os.getenv('GITLAB_TOKEN')
    platform = args.platform or os.getenv('PLATFORM', 'github').lower()
    repository = args.repository or os.getenv('REPOSITORY')
    pr_id = args.pr_id
    instructions_path = args.instructions
    log_level = args.log_level

    if not repository:
        print("Error: Repository not specified. Use --repository or set REPOSITORY environment variable")
        sys.exit(1)
        
    if platform not in ('github', 'gitlab'):
        print("Error: Invalid platform. Must be either 'github' or 'gitlab'")
        sys.exit(1)
        
    if platform == 'github' and not github_token:
        print("Error: GITHUB_TOKEN environment variable is required when platform is 'github'")
        sys.exit(1)
        
    if platform == 'gitlab' and not gitlab_token:
        print("Error: GITLAB_TOKEN environment variable is required when platform is 'gitlab'")
        sys.exit(1)
        
    print(f"Starting code review for {platform.upper()} PR #{pr_id} in {repository}")

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
