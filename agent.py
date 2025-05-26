from __future__ import annotations as _annotations

import argparse
import asyncio
import os
import sys
import httpx
import logfire
from agent_init import create_agent
from models import ReviewDeps

logfire.configure(send_to_logfire='if-token-present')

def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Code Review Agent')
    parser.add_argument('--platform', type=str, choices=['github', 'gitlab'],
                       help='Platform: github or gitlab (overrides PLATFORM env var)')
    parser.add_argument('--repository', type=str,
                       help='Repository in format owner/repo (overrides REPOSITORY env var')
    parser.add_argument('--pr-id', type=int, required=True,
                       help='Pull/Merge Request ID to review')
    parser.add_argument('--instructions-path', type=str, default='review_instructions.md',
                       help='Path to custom review instructions file (default: review_instructions.md)')
    parser.add_argument('--log-level', type=str, default='INFO',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help='Logging level (default: INFO)')
    return parser.parse_args()

async def main():
    """Main entry point for the code review agent."""
    args = parse_arguments()

    # Get environment variables
    github_token = os.getenv('GITHUB_TOKEN')
    gitlab_token = os.getenv('GITLAB_TOKEN')
    platform = args.platform or os.getenv('PLATFORM', 'github').lower()
    repository = args.repository or os.getenv('REPOSITORY')
    pr_id = args.pr_id
    instructions_path = args.instructions_path
    log_level = args.log_level

    if not repository:
        print("Error: Repository not specified. Use --repository or set REPOSITORY environment variable")
        sys.exit(1)

    if platform not in ('github', 'gitlab'):
        print("Error: Invalid platform. Must be either 'github' or 'gitlab'")
        sys.exit(1)

    # Validate tokens based on platform
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

        # Create the agent with all tools registered
        agent = create_agent("openai:gpt-4.1-mini") # [LLM]: Use OpenAI "Codex" LLM (or similar) for code analysis

        # Create dependencies with ReviewDeps for better type safety
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
            agent=agent  # Pass the agent instance to the deps
        )

        # Run the agent with the task
        await agent.run(
            f"Review pull request #{pr_id} in {repository}",
            deps=deps,
            deps_type=ReviewDeps,
            tool_choice="auto"
        )

if __name__ == "__main__":
    asyncio.run(main())
