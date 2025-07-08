from typing import Any, Dict, cast

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, LLMConfig
from crawl4ai.deep_crawling import BestFirstCrawlingStrategy
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from openai import OpenAI
from postgrest._sync.request_builder import SyncRequestBuilder
from pydantic import BaseModel, Field
from rich.progress import Progress, SpinnerColumn, TaskID, TextColumn

from code_reviewer_agent.models.base_types import NbUrlsCrawled
from code_reviewer_agent.models.crawler_agents import ConfigArgs
from code_reviewer_agent.utils.rich_utils import print_debug, print_error, print_section


class CrawledDocumentModel(BaseModel):
    title: str = Field(..., description="Page title")
    url: str = Field(..., description="Page URL")
    content: str = Field(..., description="Page content")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class CrawlerWriter:
    def __init__(self, args: ConfigArgs) -> None:
        self.openai_client = cast(OpenAI, args.get("openai_client"))
        self.supabase_table = cast(
            SyncRequestBuilder[Dict[str, Any]],
            args.get("supabase_table"),
        )

        self.urls = tuple(args.get("urls", []))
        self.max_pages = int(args.get("max_pages", 10))
        self.max_depth = int(args.get("max_depth", 2))
        self.concurrent_tasks = int(args.get("concurrent_tasks", 5))
        self.chunk_token_threshold = int(args.get("chunk_token_threshold", 1000))
        self.overlap_rate = float(args.get("overlap_rate", 0.2))
        self.temperature = float(args.get("temperature", 0.2))
        self.max_tokens = int(args.get("max_tokens", 500))
        self.headless = bool(args.get("headless", True))
        self.locale = str(args.get("locale", "en"))
        self.timezone = str(args.get("timezone", "UTC"))
        self.keywords = list(args.get("keywords", []))
        self.keyword_weight = float(args.get("keyword_weight", 1.0))
        self.prefixed_provider = str(args.get("prefixed_provider", "openai"))
        self.base_url = str(args.get("base_url", "https://api.openai.com"))
        self.api_token = str(args.get("api_token", ""))
        self.embedding_model = str(
            args.get("embedding_model", "text-embedding-3-small")
        )

        self.extraction_type = str(args.get("extraction_type", "schema"))

    @property
    def extraction_type(self) -> str:
        return self._extraction_type

    @extraction_type.setter
    def extraction_type(self, value: str) -> None:
        if value not in ["schema", "block"]:
            raise ValueError("Extraction type must be 'schema' or 'block'")
        self._extraction_type = value

        try:
            self.extraction_strategy = LLMExtractionStrategy(
                llm_config=LLMConfig(
                    provider=self.prefixed_provider,
                    api_token=self.api_token,
                    base_url=self.base_url,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                ),
                schema=CrawledDocumentModel,
                extraction_type=self._extraction_type,
                chunk_token_threshold=self.chunk_token_threshold,
                overlap_rate=self.overlap_rate,
            )
        except Exception as e:
            raise ValueError(f"Failed to initialize extraction strategy: {e}")

    @property
    def extraction_strategy(self) -> LLMExtractionStrategy:
        return self._extraction_strategy

    @extraction_strategy.setter
    def extraction_strategy(self, extraction_strategy: LLMExtractionStrategy) -> None:
        if not isinstance(extraction_strategy, LLMExtractionStrategy):
            raise ValueError(
                "Extraction strategy must be an instance of LLMExtractionStrategy"
            )
        self._extraction_strategy = extraction_strategy

    @property
    def crawler(self) -> AsyncWebCrawler:
        return self._crawler

    async def crawl_urls(self) -> NbUrlsCrawled:
        if not self.urls or len(self.urls) == 0:
            raise ValueError("At least one URL is required")

        print_section("Starting Web Crawler", "🌐")
        print_debug(
            f"Crawling {len(self.urls)} URLs with max {self.max_pages} pages each"
        )
        print_debug(
            f"Using keywords for relevance: {', '.join(self.keywords) if self.keywords else 'None'}"
        )

        # Set up the crawler with progress tracking
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            # Create a task for overall progress
            main_task = progress.add_task(
                "[cyan]Initializing crawler...",
                total=len(self.urls),
            )

            results = []
            successful_crawls = 0
            try:
                # Set up the browser configuration
                browser_config = BrowserConfig(
                    headless=self.headless,
                    # locale=self.locale,
                    # timezone=self.timezone,
                )

                # Configure the crawling strategy with keywords if provided
                strategy = BestFirstCrawlingStrategy(
                    max_pages=self.max_pages,
                    max_depth=self.max_depth,
                    # max_concurrent_tasks=self.concurrent_tasks,
                )

                # if self.keywords:
                #     strategy.scorer = KeywordRelevanceScorer(
                #         keywords=self.keywords,
                #         weight=self.keyword_weight,
                #     )

                # Create the crawler
                self._crawler = AsyncWebCrawler(
                    config=browser_config,
                    # crawler_strategy=strategy,
                    # extraction_strategy=extraction_strategy,
                )

                config = CrawlerRunConfig(
                    stream=True,
                    # max_pages=self.max_pages,
                    # max_depth=self.max_depth,
                    # max_concurrent_tasks=self.concurrent_tasks,
                )
                async for result in await self.crawler.arun_many(
                    urls=self.urls,
                    config=config,
                ):
                    url = result.url
                    progress.update(
                        main_task,
                        description=f"[cyan]Processing URL {url}",
                    )

                    if not result or not result.success:
                        # Update main progress
                        print_error(
                            f"Failed to crawl URL {url}: {getattr(result, 'error_message', 'Unknown error')}"
                        )
                        continue

                    try:
                        # Process each extracted document
                        for doc in result:
                            doc_data = (
                                doc.model_dump()
                                if hasattr(doc, "model_dump")
                                else dict(doc)
                            )
                            print(type(doc_data))
                            print(doc_data.keys())
                            print(type(doc_data["extracted_content"]))
                            print(len(doc_data["extracted_content"]))
                            doc_data["url"] = url
                            document_title = doc_data.get("title", "Untitled")

                            try:
                                # Create a task for each document
                                doc_task_id = progress.add_task(
                                    f"[cyan]Processing document: {document_title}",
                                    total=1,
                                )
                                # Store the document with progress tracking
                                success = await self.store_doc(
                                    doc_data,
                                    progress,
                                    doc_task_id,
                                )
                                if success:
                                    results.append(doc_data)
                                    successful_crawls += 1
                                    description = (
                                        f"[green]✓ Correctly stored: {document_title}"
                                    )
                                else:
                                    description = (
                                        f"[yellow]! Failed to store: {document_title}"
                                    )
                                progress.update(doc_task_id, description=description)
                            except Exception as e:
                                print_error(f"! Storing document failed: {str(e)}")
                                raise
                            finally:
                                progress.update(doc_task_id, completed=float(1))
                    except Exception as e:
                        print_error(f"Error storing document: {str(e)}")
                        raise
                    finally:
                        # Update main progress
                        progress.update(main_task, advance=1)
            except Exception as e:
                print_error(f"Error crawling {url}: {str(e)}")
            finally:
                if successful_crawls == len(self.urls):
                    description = "[green]✓ "
                else:
                    description = "[yellow]! "
                description += (
                    f"Successfully crawled {successful_crawls}/{len(self.urls)} URLs"
                )
                progress.update(
                    main_task,
                    completed=float(successful_crawls),
                    description=description,
                )

        return NbUrlsCrawled(successful_crawls)

    async def store_doc(
        self, doc_data: dict, progress: Progress, task_id: TaskID
    ) -> bool:
        document_title = doc_data.get("title", "Untitled")
        content = doc_data.get("content", "")
        url = doc_data.get("url", "unknown")
        try:
            # Ensure we have content to process
            if not content:
                raise ValueError("No content found in document")

            progress.update(task_id, description=f"Embedding: {document_title}")

            resp = self.openai_client.embeddings.create(
                input=content, model=self.embedding_model
            )

            # Safely extract the embedding
            if hasattr(resp, "data") and len(resp.data) > 0:
                embedding = resp.data[0].embedding
            else:
                raise ValueError("Unexpected embeddings response format")

            progress.update(task_id, description="Storing in database...")

            # Store in Supabase
            self.supabase_table.insert(
                {
                    "url": url,
                    "title": document_title,
                    "content": content,
                    "embedding": embedding,
                    "metadata": doc_data.get(
                        "metadata",
                        {
                            "content_length": len(content),
                        },
                    ),
                }
            ).execute()

            return True
        except ValueError as e:
            raise Exception(f"Error while checking document content: {str(e)}")
        except Exception as e:
            raise Exception(f"Error while storing document: {str(e)}")
