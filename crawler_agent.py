import argparse
import asyncio
import nest_asyncio
import json

from dotenv import load_dotenv

from pydantic import BaseModel, Field
from openai import OpenAI

from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CrawlerRunConfig
)
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from crawl4ai.deep_crawling import BestFirstCrawlingStrategy
from crawl4ai.deep_crawling.scorers import KeywordRelevanceScorer

from supabase import Client

from agent_model import get_supabase, get_embedding_model_str, get_model

load_dotenv()
nest_asyncio.apply()
openai_client = OpenAI()

# ========== Classes ==========

class CrawledDocument(BaseModel):
    title: str = Field(..., description="Page title")
    url: str = Field(..., description="Page URL")
    content: str = Field(..., description="Main content")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")

# ========== Utils functions ==========

def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Crawl a website and store results in Supabase vector DB.")
    parser.add_argument("--doc-url", type=str, required=True,
                       help="URL of the documentation to crawl")
    parser.add_argument("--max-depth", type=int, default=3,
                       help="Maximum depth of the crawl (Default: 3)")
    parser.add_argument("--max-pages", type=int, default=None,
                       help="Maximum number of pages to crawl (Default: infinite)")
    return parser.parse_args()

async def store_doc(doc_data: dict, supabase: Client):
    try:
        # Ensure we have content to process
        if not doc_data.get("content"):
            print("\033[93mWarning: No content found in document\033[0m")
            return

        # Generate embedding
        embeddings_response = openai_client.embeddings.create(
            input=doc_data["content"],
            model=get_embedding_model_str()
        )

        # Safely extract the embedding
        if hasattr(embeddings_response, 'data') and len(embeddings_response.data) > 0:
            embedding = embeddings_response.data[0].embedding
        else:
            print("\033[91mError: Unexpected embeddings response format: {embeddings_response}\033[0m")
            return

        # Insert into Supabase
        supabase.table("documents").insert({
            "title": doc_data.get("title", ""),
            "content": doc_data["content"],
            "embedding": embedding,
            "metadata": doc_data.get("metadata", {})
        }).execute()
    except Exception as e:
        print(f"\033[91mError in store_doc: {str(e)}\033[0m")
        raise

# ========== Main execution function ==========

async def main():
    """Main entry point for the crawler agent."""
    # Init Supabase client
    supabase_client = get_supabase()

    # Parse arguments
    args = parse_arguments()
    doc_url = args.doc_url
    max_depth = args.max_depth
    max_pages = float("inf") if args.max_pages is None else args.max_pages

    print(f"\033[94mStarting crawler agent for {doc_url}.\033[0m")

    # -------- Set up Crawl4AI strategy and config --------

    # Set up LLM strategy
    llm_strategy = LLMExtractionStrategy(
        llm_config=get_model(as_llm_config=True),
        schema=CrawledDocument.model_json_schema(),
        extraction_type="schema",      # "schema" for structured, "block" for freeform
        instruction="Extract all best practices and/or the documentation on the latest version of the tool or programming language.",
        chunk_token_threshold=1000,    # Chunking for large pages (optional)
        overlap_rate=0.1,              # Overlap between chunks (optional)
        apply_chunking=True,           # Enable chunking (recommended for long pages)
        input_format="markdown",       # "markdown" (default), "html", or "fit_markdown"
        extra_args={"temperature": 0.1, "max_tokens": 800},  # LLM params
        verbose=True
    )

    # Create a scorer
    scorer = KeywordRelevanceScorer(
        keywords=[
            "crawl",
            "example",
            "best practices",
            "configuration",
            "documentation"
        ],
        weight=0.7
    )
    # Configure the strategy
    crawl_strategy = BestFirstCrawlingStrategy(
        max_depth=max_depth,
        include_external=False,
        url_scorer=scorer,
        max_pages=max_pages,
    )

    # Set up crawler config
    crawl_config = CrawlerRunConfig(
        extraction_strategy=llm_strategy,     # determine how to processe the content of each page
        deep_crawl_strategy=crawl_strategy,   # determines which pages to visit
        locale="fr-FR",                       # Set browser locale (language and region formatting)
        timezone_id="Europe/Paris",           # Set browser timezone
        stream=True,                          # Enable streaming
    )

    # (Optional) Browser config for headless operation
    browser_cfg = BrowserConfig(headless=True)

    # -------- Run crawler --------

    async with AsyncWebCrawler(max_concurrent_tasks=3, config=browser_cfg) as crawler:
        # Run the crawler and get the result
        async for result in await crawler.arun(url=doc_url, config=crawl_config):
            if result.success:
                try:
                    # The extracted content should be a JSON string containing a list of documents
                    documents = json.loads(result.extracted_content)

                    if not isinstance(documents, list):
                        documents = [documents]  # Convert single document to a list for consistent processing

                    # Store each document in the list
                    for doc in documents:
                        try:
                            await store_doc(doc, supabase_client)
                            print(f"\033[92mStored document from: {result.url} (depth {result.metadata.get('depth', 0)})\033[0m")
                        except Exception as e:
                            print(f"\033[93mError storing document from {result.url}: {str(e)}\033[0m")
                except json.JSONDecodeError as e:
                    print(f"\033[91mFailed to parse JSON from {result.url}: {str(e)}\033[0m")
                    print(f"Content type: {type(result.extracted_content)}")
                    print(f"Content: {result.extracted_content[:500]}...")
            else:
                print(f"\033[91mFailed: {result.url} ({result.error_message})\033[0m")

if __name__ == "__main__":
    asyncio.run(main())
