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
    mcp1_resolve_library_id,
    mcp1_get_library_docs,
    search_web,
)
from agent_prompts import SYSTEM_PROMPT

logfire.configure(send_to_logfire='if-token-present')

@dataclass
class ReviewDeps:
    """Dependency holder for API clients, config for GitHub/GitLab and MCP tools"""
    http_client: httpx.AsyncClient
    platform: str  # 'github' or 'gitlab'
    github_token: str | None
    gitlab_token: str | None
    repository: str
    pr_id: int
    instructions_path: str
    log_level: str
    openai_api_key: str  # OpenAI API key for the agent to use
    agent: Any  # The agent instance that will handle LLM interactions

    # MCP Tool methods
    async def resolve_library_id(self, params: dict) -> dict:
        """Resolve a library name to its Context7 ID"""
        return await mcp1_resolve_library_id(params)

    async def get_library_docs(self, params: dict) -> dict:
        """Retrieve documentation from Context7"""
        return await mcp1_get_library_docs(params)

    async def search_web(self, params: dict) -> dict:
        """Perform a web search using the Brave Search API"""
        return await search_web(params)

# Agent will be created in the main function with the proper dependencies

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
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if not openai_api_key:
            print("Error: OPENAI_API_KEY environment variable is required")
            sys.exit(1)

        # Create the agent instance with the base system prompt
        # The actual system prompt with custom_instructions and best_practices will be set in analyze_with_llm
        agent = Agent(
            "openai:gpt-4.1-mini", # [LLM]: Use OpenAI "Codex" LLM (or similar) for code analysis
            system_prompt=SYSTEM_PROMPT,
            deps_type=ReviewDeps,
            retries=2,
        )

        # Register tools
        agent.add_tool(get_pr_diff)
        agent.add_tool(post_review_comment)
        agent.add_tool(get_review_instructions)
        agent.add_tool(search_best_practices)
        agent.add_tool(detect_languages)
        agent.add_tool(aggregate_review_comments)

        # Create dependencies with the agent
        deps = ReviewDeps(
            http_client=http_client,
            platform=platform,
            github_token=github_token,
            gitlab_token=gitlab_token,
            repository=repository,
            pr_id=pr_id,
            instructions_path=instructions_path,
            log_level=log_level,
            openai_api_key=openai_api_key,
            agent=agent
        )

        # Run the agent
        await agent.run("Review this pull request", deps=deps)

if __name__ == "__main__":
    asyncio.run(main())
