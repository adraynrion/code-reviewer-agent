"""Web crawler service for the code review agent."""

import argparse
import asyncio
import json
from typing import Any, Dict, List, Optional

import nest_asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai.deep_crawling import BestFirstCrawlingStrategy
from crawl4ai.deep_crawling.scorers import KeywordRelevanceScorer
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from openai import OpenAI
from pydantic import BaseModel, Field
from supabase import Client

from ..models.agent import get_embedding_model_str, get_model, get_supabase

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


class CrawledDocument(BaseModel):
    """Model for crawled document data."""

    title: str = Field(..., description="Page title")
    url: str = Field(..., description="Page URL")
    content: str = Field(..., description="Page content")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


async def store_doc(doc_data: dict, supabase: Client) -> None:
    """Store a document in the database.

    Args:
        doc_data: Document data to store
        supabase: Supabase client instance

    """
    try:
        # Ensure we have content to process
        if not doc_data.get("content"):
            print("\033[93mWarning: No content found in document\033[0m")
            return

        # Generate embedding
        embeddings_response = openai_client.embeddings.create(
            input=doc_data["content"], model=get_embedding_model_str()
        )

        # Safely extract the embedding
        if hasattr(embeddings_response, "data") and len(embeddings_response.data) > 0:
            embedding = embeddings_response.data[0].embedding
        else:
            print("\033[91mError: Unexpected embeddings response format\033[0m")
            return

        # Insert into Supabase
        supabase.table("documents").insert(
            {
                "title": doc_data.get("title", ""),
                "content": doc_data["content"],
                "embedding": embedding,
                "metadata": doc_data.get("metadata", {}),
            }
        ).execute()
    except Exception as e:
        print(f"\033[91mError in store_doc: {str(e)}\033[0m")
        raise


async def crawl_urls(
    urls: List[str],
    max_pages: int = 5,
    max_depth: int = 3,
    concurrent_tasks: int = 3,
    extraction_type: str = "schema",
    chunk_token_threshold: int = 1000,
    overlap_rate: float = 0.1,
    temperature: float = 0.1,
    max_tokens: int = 800,
    headless: bool = True,
    locale: str = "en-US",
    timezone: str = "UTC",
    keywords: Optional[List[str]] = None,
    keyword_weight: float = 0.7,
) -> List[Dict[str, Any]]:
    """Crawl a list of URLs and return the extracted content.

    Args:
        urls: List of URLs to crawl
        max_pages: Maximum number of pages to crawl per URL

    Returns:
        List of dictionaries containing crawled data

    """
    supabase_client = get_supabase()
    all_documents = []

    # Set up LLM strategy
    llm_strategy = LLMExtractionStrategy(
        llm_config=get_model(as_llm_config=True),
        schema=CrawledDocument.model_json_schema(),
        extraction_type=extraction_type,
        instruction="Extract all best practices and/or the documentation on the latest version of the tool or programming language.",
        chunk_token_threshold=chunk_token_threshold,
        overlap_rate=overlap_rate,
        apply_chunking=True,
        input_format="markdown",
        extra_args={"temperature": temperature, "max_tokens": max_tokens},
        verbose=True,
    )

    # Set default keywords if none provided
    if keywords is None:
        keywords = [
            "crawl",
            "example",
            "best practices",
            "configuration",
            "documentation",
        ]

    # Create a scorer for relevant content
    scorer = KeywordRelevanceScorer(keywords=keywords, weight=keyword_weight)

    # Configure the crawling strategy
    crawl_strategy = BestFirstCrawlingStrategy(
        max_depth=max_depth,
        include_external=False,
        url_scorer=scorer,
        max_pages=max_pages,
    )

    # Set up crawler config
    crawl_config = CrawlerRunConfig(
        extraction_strategy=llm_strategy,
        deep_crawl_strategy=crawl_strategy,
        locale=locale,
        timezone_id=timezone,
        stream=True,
    )

    # Browser config
    browser_cfg = BrowserConfig(headless=headless)

    async with AsyncWebCrawler(
        max_concurrent_tasks=concurrent_tasks, config=browser_cfg
    ) as crawler:
        for url in urls:
            async for result in await crawler.arun(url=url, config=crawl_config):
                if result.success:
                    try:
                        documents = json.loads(result.extracted_content)
                        if not isinstance(documents, list):
                            documents = [documents]

                        for doc in documents:
                            try:
                                await store_doc(doc, supabase_client)
                                all_documents.append(doc)
                                print(
                                    f"\033[92mStored document from: {result.url}\033[0m"
                                )
                            except Exception as e:
                                print(
                                    f"\033[93mError storing document from {result.url}: {str(e)}\033[0m"
                                )
                    except json.JSONDecodeError as e:
                        print(
                            f"\033[91mFailed to parse JSON from {result.url}: {str(e)}\033[0m"
                        )
                else:
                    print(
                        f"\033[91mFailed: {result.url} ({result.error_message})\033[0m"
                    )

    return all_documents


async def main() -> List[Dict[str, Any]]:
    """Main entry point for the crawler service."""
    args = parse_arguments()

    print(f"Starting crawler for {len(args.urls)} URLs...")

    results = await crawl_urls(
        urls=args.urls,
        max_pages=args.max_pages,
        max_depth=args.max_depth,
        concurrent_tasks=args.concurrent_tasks,
        extraction_type=args.extraction_type,
        chunk_token_threshold=args.chunk_token_threshold,
        overlap_rate=args.overlap_rate,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        headless=args.headless,
        locale=args.locale,
        timezone=args.timezone,
        keywords=args.keywords,
        keyword_weight=args.keyword_weight,
    )

    print(f"Crawling completed. Processed {len(results)} documents.")
    return results


if __name__ == "__main__":
    asyncio.run(main())
