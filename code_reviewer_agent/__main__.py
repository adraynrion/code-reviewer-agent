#!/usr/bin/env python3
"""Main entry point for the code review agent."""

import asyncio

import click


@click.group()
@click.version_option()
def cli() -> None:
    """Code Reviewer Agent - AI-powered code review assistant."""
    pass


@cli.command()
def review() -> None:
    """Run code review with the current configuration."""
    from code_reviewer_agent.services.code_reviewer import main as code_reviewer_main

    asyncio.run(code_reviewer_main())


@cli.command()
def crawl() -> None:
    """Run the web crawler."""
    from code_reviewer_agent.services.crawler import main as crawler_main

    asyncio.run(crawler_main())


if __name__ == "__main__":
    cli()
