from __future__ import annotations as _annotations

import argparse
import asyncio
import logging
import os
import sys
import time
import httpx
import logfire
from agent_init import create_agent
from models import ReviewDeps

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
    ]
)
logger = logging.getLogger(__name__)

# Configure logfire
logfire.configure(send_to_logfire='if-token-present')

def setup_logging(log_level: str = 'INFO') -> None:
    """Set up logging configuration.

    Args:
        log_level: Logging level as a string (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    level = getattr(logging, log_level.upper(), logging.INFO)
    logging.basicConfig(level=level)
    logging.getLogger().setLevel(level)
    logger.setLevel(level)

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
    setup_logging(args.log_level)

    platform = args.platform or os.getenv('PLATFORM', 'github')
    logger.info(f"Starting code review for {platform.upper()} PR #{args.pr_id} in {args.repository or os.getenv('REPOSITORY', '')}")

    try:
        # Set up dependencies first
        deps = ReviewDeps(
            http_client=httpx.AsyncClient(timeout=60.0),
            platform=args.platform or os.getenv('PLATFORM', 'github'),
            github_token=os.getenv('GITHUB_TOKEN', ''),
            gitlab_token=os.getenv('GITLAB_TOKEN', ''),
            repository=args.repository or os.getenv('REPOSITORY', ''),
            pr_id=args.pr_id,
            instructions_path=args.instructions_path,
            log_level=args.log_level,
            openai_api_key=os.getenv('OPENAI_API_KEY', ''),
            agent=None  # Will be set after agent creation
        )

        # Create the agent with dependencies
        agent = create_agent("openai:gpt-4o-mini", deps=deps)
        deps.agent = agent  # Set the agent in deps after creation

        # Validate tokens based on platform
        if deps.platform == 'github' and not deps.github_token:
            logger.error("GITHUB_TOKEN environment variable is required when platform is 'github'")
            return 1

        if deps.platform == 'gitlab' and not deps.gitlab_token:
            logger.error("GITLAB_TOKEN environment variable is required when platform is 'gitlab'")
            return 1

        if not deps.repository:
            logger.error("Repository not specified. Use --repository or set REPOSITORY environment variable")
            return 1

        if deps.platform not in ('github', 'gitlab'):
            logger.error("Invalid platform. Must be either 'github' or 'gitlab'")
            return 1

        if not deps.openai_api_key:
            logger.error("OPENAI_API_KEY environment variable is required")
            return 1

        # Run the agent with the task
        result = await agent.run(
            f"Review pull request #{args.pr_id} in {deps.repository}",
            repository=deps.repository,
            pr_id=args.pr_id,
            instructions_path=args.instructions_path
        )

        logger.info("Code review completed successfully!")
        return result

    except Exception as e:
        logger.error(f"Error in agent run: {e}", exc_info=True)
        return 1
    finally:
        # Clean up resources
        if 'deps' in locals() and hasattr(deps, 'http_client'):
            try:
                await deps.http_client.aclose()
            except Exception as e:
                logger.error(f"Error closing HTTP client: {e}", exc_info=True)
        # Ensure Langfuse events are flushed
        if 'logfire' in sys.modules:
            import logfire
            if hasattr(logfire, 'flush'):
                logfire.flush()

if __name__ == "__main__":
    asyncio.run(main())
