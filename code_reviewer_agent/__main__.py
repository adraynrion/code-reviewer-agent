#!/usr/bin/env python3
"""Main entry point for the code review agent."""

import asyncio

import click


@click.group()
def cli() -> None:
    """Code Reviewer Agent - AI-powered code review assistant."""
    pass


@cli.command()
@click.option('--platform', type=click.Choice(['github', 'gitlab']),
              help="Version control platform (overrides PLATFORM env var)")
@click.option('--repository', type=str,
              help="Repository identifier. For GitHub: 'owner/repo' format. For GitLab: project ID (overrides REPOSITORY env var)")
@click.option('--id', '--pr-id', '--mr-id', 'pr_id', type=int,
              help="Pull request or merge request ID (overrides PR_ID env var)")
@click.option('--instructions-path', type=click.Path(exists=True, file_okay=False, dir_okay=True),
              help="Path to the local directory containing your custom instructions for the code review (overrides LOCAL_FILE_DIR env var)")
def review(platform, repository, pr_id, instructions_path) -> None:
    """Run code review with the current configuration.

    Examples:
      code-reviewer review --platform github --repository owner/repo --id 123
      code-reviewer review --platform gitlab --repository 12345 --id 42 --instructions-path ./docs
    """
    from code_reviewer_agent.services.code_reviewer import main as code_reviewer_main

    asyncio.run(code_reviewer_main(platform=platform, repository=repository, id=pr_id, instructions_path=instructions_path))


@cli.command()
@click.argument('urls', nargs=-1, required=True)
@click.option('--max-pages', type=int, default=5, help='Maximum number of pages to crawl per URL (default: 5)')
@click.option('--max-depth', type=int, default=3, help='Maximum depth of the crawl (default: 3)')
@click.option('--concurrent-tasks', type=int, default=3, help='Maximum number of concurrent crawling tasks (default: 3)')
@click.option('--extraction-type', type=click.Choice(['schema', 'block']), default='schema',
              help="Extraction type: 'schema' for structured, 'block' for freeform (default: schema)")
@click.option('--chunk-token-threshold', type=int, default=1000,
              help='Chunk token threshold for large pages (default: 1000)')
@click.option('--overlap-rate', type=float, default=0.1,
              help='Overlap rate between chunks (default: 0.1)')
@click.option('--temperature', type=float, default=0.1,
              help='Temperature for LLM generation (default: 0.1)')
@click.option('--max-tokens', type=int, default=800,
              help='Maximum tokens for LLM generation (default: 800)')
@click.option('--headless/--no-headless', default=True,
              help='Run browser in headless mode (default: True)')
@click.option('--locale', default='en-US',
              help='Browser locale (default: en-US)')
@click.option('--timezone', default='UTC',
              help='Browser timezone (default: UTC)')
@click.option('--keywords', multiple=True,
              default=['crawl', 'example', 'best practices', 'configuration', 'documentation'],
              help='Keywords for content relevance scoring (can be used multiple times)')
@click.option('--keyword-weight', type=float, default=0.7,
              help='Weight for keyword relevance scoring (default: 0.7)')
def crawl(urls, **kwargs) -> None:
    """Run the web crawler."""
    from code_reviewer_agent.services.crawler import main as crawler_main

    # Convert click's multiple keywords to a list
    kwargs['keywords'] = list(kwargs['keywords'])
    asyncio.run(crawler_main(urls, **kwargs))


if __name__ == "__main__":
    cli()
