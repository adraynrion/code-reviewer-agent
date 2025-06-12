"""Web crawler service for the code review agent."""

from typing import Any, Dict, List, Optional

import nest_asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai.deep_crawling import BestFirstCrawlingStrategy
from crawl4ai.deep_crawling.scorers import KeywordRelevanceScorer
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from openai import OpenAI
from pydantic import BaseModel, Field
from rich.progress import Progress, SpinnerColumn, TaskID, TextColumn
from supabase import Client

from code_reviewer_agent.config.config import config
from code_reviewer_agent.models.base_agent import get_model, get_supabase
from code_reviewer_agent.utils.rich_utils import (
    print_error,
    print_exception,
    print_info,
    print_section,
    print_success,
    print_warning,
)

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

# Initialize OpenAI client
openai_client = OpenAI()
# Initialize Supabase client
supabase_client = get_supabase()


class CrawledDocument(BaseModel):
    """Model for crawled document data."""

    title: str = Field(..., description="Page title")
    url: str = Field(..., description="Page URL")
    content: str = Field(..., description="Page content")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


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
        max_depth: Maximum depth of the crawl
        concurrent_tasks: Maximum number of concurrent crawling tasks
        extraction_type: Type of content extraction ('schema' or 'block')
        chunk_token_threshold: Token threshold for content chunking
        overlap_rate: Overlap rate between chunks
        temperature: Temperature for LLM generation
        max_tokens: Maximum tokens for LLM generation
        headless: Whether to run browser in headless mode
        locale: Browser locale
        timezone: Browser timezone
        keywords: List of keywords for content relevance scoring
        keyword_weight: Weight for keyword relevance scoring

    Returns:
        List of dictionaries containing crawled data

    """
    print_section("Starting Web Crawler", "")
    print_info(f"Crawling {len(urls)} URLs with max {max_pages} pages each")

    if keywords:
        print_info(
            f"Using keywords for relevance: {', '.join(keywords[:3])}{'...' if len(keywords) > 3 else ''}"
        )

    # Set up the crawler with progress tracking
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        # Create a task for overall progress
        main_task = progress.add_task("[cyan]Initializing crawler...", total=len(urls))

        # Set up the browser configuration
        browser_config = BrowserConfig(
            headless=headless,
            locale=locale,
            timezone=timezone,
        )

        # Configure the crawling strategy with keywords if provided
        strategy = BestFirstCrawlingStrategy(
            max_pages=max_pages,
            max_depth=max_depth,
            max_concurrent_tasks=concurrent_tasks,
        )

        if keywords:
            strategy.scorer = KeywordRelevanceScorer(
                keywords=keywords, weight=keyword_weight
            )

        # Set up the extraction strategy
        progress.update(main_task, description="[cyan]Setting up extraction...")

        try:
            if extraction_type == "schema":
                extraction_strategy = LLMExtractionStrategy.with_auto_schema(
                    model=get_model(),
                    schema=CrawledDocument,
                    chunk_token_threshold=chunk_token_threshold,
                    overlap_rate=overlap_rate,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                print_success(f"Using schema-based extraction with {get_model()}")
            else:
                extraction_strategy = LLMExtractionStrategy.with_auto_chunking(
                    model=get_model(),
                    chunk_token_threshold=chunk_token_threshold,
                    overlap_rate=overlap_rate,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                print_success(f"Using block-based extraction with {get_model()}")

        except Exception as e:
            print_error(f"Failed to initialize extraction strategy: {str(e)}")
            return []

        # Create the crawler
        crawler = AsyncWebCrawler(
            browser_config=browser_config,
            crawling_strategy=strategy,
            extraction_strategy=extraction_strategy,
        )

        # Run the crawler for each URL
        results = []
        successful_crawls = 0

        for i, url in enumerate(urls, 1):
            url_task = progress.add_task(
                f"[green]Crawling URL {i}/{len(urls)}", total=1
            )
            progress.update(
                main_task, description=f"[cyan]Processing URL {i}/{len(urls)}"
            )

            try:
                # Crawl the URL
                progress.update(url_task, description=f"[green]Crawling: {url}")
                result = await crawler.crawl(
                    url,
                    config=CrawlerRunConfig(
                        max_pages=max_pages,
                        max_depth=max_depth,
                        max_concurrent_tasks=concurrent_tasks,
                    ),
                )

                if result and hasattr(result, "extracted_contents"):
                    # Process each extracted document
                    docs = result.extracted_contents
                    doc_tasks: List[TaskID] = []

                    # Create tasks for processing documents
                    for doc in docs:
                        doc_data = (
                            doc.model_dump()
                            if hasattr(doc, "model_dump")
                            else dict(doc)
                        )
                        doc_data["url"] = url

                        # Create a task for each document
                        task_id = progress.add_task(
                            f"[cyan]Processing document: {doc_data.get('title', 'Untitled')[:30]}...",
                            total=1,
                        )
                        doc_tasks.append(task_id)

                        try:
                            # Store the document with progress tracking
                            success = await store_doc(
                                doc_data, supabase_client, progress, task_id
                            )
                            if success:
                                results.append(doc_data)
                                successful_crawls += 1
                                progress.update(
                                    task_id,
                                    completed=True,
                                    description=f"[green]✓ Processed: {doc_data.get('title', 'Untitled')[:30]}...",
                                )
                            else:
                                progress.update(
                                    task_id,
                                    description=f"[yellow]! Failed to store: {doc_data.get('title', 'Untitled')[:30]}...",
                                )

                        except Exception as e:
                            progress.update(
                                task_id, description=f"[red]! Error: {str(e)[:50]}..."
                            )
                            print_error(f"Error processing document: {str(e)}")
                            print_exception()

                    progress.update(
                        url_task, completed=1, description=f"[green]✓ Crawled: {url}"
                    )

                else:
                    progress.update(
                        url_task, description=f"[yellow]! No content found at: {url}"
                    )
                    print_warning(f"No content found at: {url}")

            except Exception as e:
                progress.update(url_task, description=f"[red]! Error crawling: {url}")
                print_error(f"Error crawling {url}: {str(e)}")
                print_exception()

            # Update main progress
            progress.update(main_task, advance=1)

        # Print summary
        progress.update(main_task, completed=len(urls))

        if successful_crawls > 0:
            print_success(
                f"Successfully processed {successful_crawls} documents from {len(urls)} URLs"
            )
        else:
            print_warning("No content was extracted from the provided URLs")

        return results


async def store_doc(
    doc_data: dict,
    supabase: Client,
    progress: Optional[Progress] = None,
    task_id: Optional[TaskID] = None,
) -> bool:
    """Store a document in the database.

    Args:
        doc_data: Document data to store
        supabase: Supabase client instance
        progress: Optional Rich Progress instance for tracking
        task_id: Optional task ID for progress tracking

    Returns:
        bool: True if storage was successful, False otherwise

    """
    try:
        # Update progress if provided
        if progress is not None and task_id is not None:
            progress.update(
                task_id, description=f"Processing: {doc_data.get('title', 'Untitled')}"
            )

        # Ensure we have content to process
        if not doc_data.get("content"):
            print_warning("No content found in document")
            return False

        # Generate embedding with progress feedback
        if progress is not None and task_id is not None:
            progress.update(task_id, description="Generating embeddings...")

        try:
            embeddings_response = openai_client.embeddings.create(
                input=doc_data["content"], model=config.crawler.embedding_model
            )

            # Safely extract the embedding
            if (
                hasattr(embeddings_response, "data")
                and len(embeddings_response.data) > 0
            ):
                embedding = embeddings_response.data[0].embedding
            else:
                print_error("Unexpected embeddings response format")
                return False

        except Exception as e:
            print_error(f"Error generating embeddings: {str(e)}")
            return False

        # Store in Supabase
        if progress is not None and task_id is not None:
            progress.update(task_id, description="Storing in database...")

        try:
            supabase.table("documents").insert(
                {
                    "title": doc_data.get("title", "Untitled"),
                    "content": doc_data["content"],
                    "embedding": embedding,
                    "metadata": doc_data.get(
                        "metadata",
                        {
                            "source": doc_data.get("url", "unknown"),
                            "content_length": len(doc_data["content"]),
                        },
                    ),
                }
            ).execute()

            if progress is not None and task_id is not None:
                progress.update(task_id, description="Document stored successfully")

            return True

        except Exception as e:
            print_error(f"Database error: {str(e)}")
            return False

    except Exception as e:
        print_error(f"Error in store_doc: {str(e)}")
        print_exception()
        return False
    finally:
        # Ensure progress is updated even if an error occurs
        if progress is not None and task_id is not None:
            progress.update(task_id, completed=True)
