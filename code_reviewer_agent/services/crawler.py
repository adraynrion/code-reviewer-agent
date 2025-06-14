"""Web crawler service for the code review agent."""

import argparse
import asyncio
import sys

import nest_asyncio
from openai import OpenAI

from code_reviewer_agent.config.config import config
from code_reviewer_agent.services.crawler_write import crawl_urls
from code_reviewer_agent.utils.rich_utils import (
    console,
    print_error,
    print_header,
    print_info,
    print_section,
    print_success,
)

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

# Initialize OpenAI client
openai_client = OpenAI()


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments for the crawler service."""
    parser = argparse.ArgumentParser(
        description="Crawl websites and store content in Supabase."
    )

    # Required arguments
    parser.add_argument(
        "--urls", nargs="+", required=True, help="List of URLs to crawl"
    )

    # Crawling configuration
    parser.add_argument(
        "--max-pages",
        type=int,
        default=5,
        help="Maximum number of pages to crawl per URL (default: 5)",
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=3,
        help="Maximum depth of the crawl (default: 3)",
    )
    parser.add_argument(
        "--concurrent-tasks",
        type=int,
        default=3,
        help="Maximum number of concurrent crawling tasks (default: 3)",
    )

    # LLM extraction settings
    parser.add_argument(
        "--extraction-type",
        type=str,
        default="schema",
        choices=["schema", "block"],
        help="Extraction type: 'schema' for structured, 'block' for freeform (default: schema)",
    )
    parser.add_argument(
        "--chunk-token-threshold",
        type=int,
        default=1000,
        help="Chunk token threshold for large pages (default: 1000)",
    )
    parser.add_argument(
        "--overlap-rate",
        type=float,
        default=0.1,
        help="Overlap rate between chunks (default: 0.1)",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.1,
        help="Temperature for LLM generation (default: 0.1)",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=800,
        help="Maximum tokens for LLM generation (default: 800)",
    )

    # Browser configuration
    parser.add_argument(
        "--headless",
        action="store_true",
        default=True,
        help="Run browser in headless mode (default: True)",
    )
    parser.add_argument(
        "--locale", type=str, default="en-US", help="Browser locale (default: en-US)"
    )
    parser.add_argument(
        "--timezone", type=str, default="UTC", help="Browser timezone (default: UTC)"
    )

    # Keywords for content relevance scoring
    parser.add_argument(
        "--keywords",
        nargs="+",
        default=[
            "crawl",
            "example",
            "best practices",
            "configuration",
            "documentation",
        ],
        help="Keywords for content relevance scoring",
    )
    parser.add_argument(
        "--keyword-weight",
        type=float,
        default=0.7,
        help="Weight for keyword relevance scoring (default: 0.7)",
    )

    return parser.parse_args()


async def main(urls, **kwargs) -> None:
    """Main entry point for the crawler service."""
    console.clear()
    print_header("Starting Web Crawler Service")

    if config.logging.debug:
        config.print_config()

    # Parse command line arguments
    args = argparse.Namespace(urls=urls, **kwargs)
    urls = args.urls
    max_pages = args.max_pages
    max_depth = args.max_depth
    concurrent_tasks = args.concurrent_tasks
    extraction_type = args.extraction_type
    chunk_token_threshold = args.chunk_token_threshold
    overlap_rate = args.overlap_rate
    temperature = args.temperature
    max_tokens = args.max_tokens
    headless = args.headless
    locale = args.locale
    timezone = args.timezone
    keywords = args.keywords or [
        "crawl",
        "example",
        "best practices",
        "configuration",
        "documentation",
    ]
    keyword_weight = args.keyword_weight

    # Ensure we have at least one URL
    if not urls:
        print_error("Error: At least one URL is required")
        sys.exit(1)

    # Print configuration summary if DEBUG
    if config.logging.debug:
        print_section(f"Crawling with the following settings:", "🕷️")
        print_info(f"  • URLs: {', '.join(urls)}")
        print_info(f"  • Max pages per URL: {max_pages}")
        print_info(f"  • Max depth: {max_depth}")
        print_info(f"  • Concurrent tasks: {concurrent_tasks}")
        print_info(f"  • Extraction type: {extraction_type}")
        print_info(f"  • Chunk token threshold: {chunk_token_threshold}")
        print_info(f"  • Overlap rate: {overlap_rate}")
        print_info(f"  • Temperature: {temperature}")
        print_info(f"  • Max tokens: {max_tokens}")
        print_info(f"  • Headless mode: {'enabled' if headless else 'disabled'}")
        print_info(f"  • Locale: {locale}")
        print_info(f"  • Timezone: {timezone}")
        print_info(f"  • Keywords: {', '.join(keywords)}")
        print_info(f"  • Keyword weight: {keyword_weight}")

    # Run the crawler
    results = await crawl_urls(
        urls=urls,
        max_pages=max_pages,
        max_depth=max_depth,
        concurrent_tasks=concurrent_tasks,
        extraction_type=extraction_type,
        chunk_token_threshold=chunk_token_threshold,
        overlap_rate=overlap_rate,
        temperature=temperature,
        max_tokens=max_tokens,
        headless=headless,
        locale=locale,
        timezone=timezone,
        keywords=keywords,
        keyword_weight=keyword_weight,
    )

    # Print summary
    if not results:
        print_error("No documents were crawled. Check the URLs and try again.")
        sys.exit(1)
    print_success(
        f"Successfully crawled {len(results)} documents from {len(urls)} URLs"
    )


if __name__ == "__main__":
    asyncio.run(main())
