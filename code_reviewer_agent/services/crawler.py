import sys
from typing import Any, List

from rich.table import Table

from code_reviewer_agent.config.config import Config
from code_reviewer_agent.models.base_types import (
    ApiKey,
    ChunkTokenThreshold,
    ConcurrentTasks,
    EmbeddingModel,
    ExtractionType,
    Keywords,
    KeywordWeight,
    Locale,
    MaxDepth,
    MaxPages,
    MaxTokens,
    OverlapRate,
    Temperature,
    Timezone,
    Urls,
)
from code_reviewer_agent.models.crawler_agents import CrawlerAgents
from code_reviewer_agent.services.base_service import BaseService
from code_reviewer_agent.utils.rich_utils import (
    console,
    print_error,
    print_header,
    print_success,
)


class CrawlService(BaseService):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(Config())

        crawler_config = self.config.schema.crawler
        self._enabled = crawler_config.enabled
        self._openai_api_key = ApiKey(crawler_config.openai_api_key)
        self._embedding_model = EmbeddingModel(crawler_config.embedding_model)

        urls = kwargs.get("urls")
        if not urls:
            raise ValueError("URLs are required")
        elif not isinstance(urls, list):
            raise ValueError("URLs must be a list")
        self._urls = Urls(urls)
        self._max_pages = MaxPages(kwargs.get("max_pages") or crawler_config.max_pages)
        self._max_depth = MaxDepth(kwargs.get("max_depth") or crawler_config.max_depth)
        self._concurrent_tasks = ConcurrentTasks(
            kwargs.get("concurrent_tasks") or crawler_config.concurrent_tasks
        )
        self._extraction_type = ExtractionType(
            kwargs.get("extraction_type") or crawler_config.extraction_type
        )
        self._chunk_token_threshold = ChunkTokenThreshold(
            kwargs.get("chunk_token_threshold") or crawler_config.chunk_token_threshold
        )
        self._overlap_rate = OverlapRate(
            kwargs.get("overlap_rate") or crawler_config.overlap_rate
        )
        self._temperature = Temperature(
            kwargs.get("temperature") or crawler_config.temperature
        )
        self._max_tokens = MaxTokens(
            kwargs.get("max_tokens") or crawler_config.max_tokens
        )
        self._headless = bool(kwargs.get("headless") or crawler_config.headless)
        self._locale = Locale(kwargs.get("locale") or crawler_config.locale)
        self._timezone = Timezone(kwargs.get("timezone") or crawler_config.timezone)
        self._keywords = Keywords(
            kwargs.get("keywords")
            or crawler_config.keywords
            or (
                "crawl",
                "example",
                "best practices",
                "configuration",
                "documentation",
            )
        )
        self._keyword_weight = KeywordWeight(
            kwargs.get("keyword_weight") or crawler_config.keyword_weight
        )

        self._agents = CrawlerAgents(self.config, self.urls)

    def __dir__(self) -> list[str]:
        return [
            "enabled",
            "openai_api_key",
            "embedding_model",
            "urls",
            "max_pages",
            "max_depth",
            "concurrent_tasks",
            "extraction_type",
            "chunk_token_threshold",
            "overlap_rate",
            "temperature",
            "max_tokens",
            "headless",
            "locale",
            "timezone",
            "keywords",
            "keyword_weight",
        ]

    @property
    def debug(self) -> bool:
        return self._config.schema.logging.debug

    @property
    def agents(self) -> CrawlerAgents:
        return self._agents

    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def openai_api_key(self) -> str:
        return self._openai_api_key

    @property
    def embedding_model(self) -> str:
        return self._embedding_model

    @property
    def urls(self) -> Urls:
        return self._urls

    @urls.setter
    def urls(self, value: List[str]) -> None:
        self._urls = Urls(value)

    @property
    def max_pages(self) -> MaxPages:
        return self._max_pages

    @max_pages.setter
    def max_pages(self, value: int) -> None:
        self._max_pages = MaxPages(value)

    @property
    def max_depth(self) -> MaxDepth:
        return self._max_depth

    @max_depth.setter
    def max_depth(self, value: int) -> None:
        self._max_depth = MaxDepth(value)

    @property
    def concurrent_tasks(self) -> ConcurrentTasks:
        return self._concurrent_tasks

    @concurrent_tasks.setter
    def concurrent_tasks(self, value: int) -> None:
        self._concurrent_tasks = ConcurrentTasks(value)

    @property
    def extraction_type(self) -> ExtractionType:
        return self._extraction_type

    @extraction_type.setter
    def extraction_type(self, value: str) -> None:
        formated_value = value.lower().strip()
        if formated_value not in ("schema", "block"):
            raise ValueError(
                "Invalid extraction type. Must be either 'schema' or 'block'."
            )
        self._extraction_type = ExtractionType(formated_value)

    @property
    def chunk_token_threshold(self) -> ChunkTokenThreshold:
        return self._chunk_token_threshold

    @chunk_token_threshold.setter
    def chunk_token_threshold(self, value: int) -> None:
        self._chunk_token_threshold = ChunkTokenThreshold(value)

    @property
    def overlap_rate(self) -> OverlapRate:
        return self._overlap_rate

    @overlap_rate.setter
    def overlap_rate(self, value: float) -> None:
        self._overlap_rate = OverlapRate(value)

    @property
    def temperature(self) -> Temperature:
        return self._temperature

    @temperature.setter
    def temperature(self, value: float) -> None:
        self._temperature = Temperature(value)

    @property
    def max_tokens(self) -> MaxTokens:
        return self._max_tokens

    @max_tokens.setter
    def max_tokens(self, value: int) -> None:
        self._max_tokens = MaxTokens(value)

    @property
    def headless(self) -> bool:
        return self._headless

    @headless.setter
    def headless(self, value: bool) -> None:
        self._headless = bool(value)

    @property
    def locale(self) -> Locale:
        return self._locale

    @locale.setter
    def locale(self, value: str) -> None:
        self._locale = Locale(value)

    @property
    def timezone(self) -> Timezone:
        return self._timezone

    @timezone.setter
    def timezone(self, value: str) -> None:
        self._timezone = Timezone(value)

    @property
    def keywords(self) -> Keywords:
        return self._keywords

    @keywords.setter
    def keywords(self, value: List[str]) -> None:
        self._keywords = Keywords(value)

    @property
    def keyword_weight(self) -> KeywordWeight:
        return self._keyword_weight

    @keyword_weight.setter
    def keyword_weight(self, value: float) -> None:
        self._keyword_weight = KeywordWeight(value)

    async def main(self) -> None:
        console.clear()
        print_header("Starting Web Crawler Service process")

        if self.debug:
            table = Table(
                title="Current Configuration", show_header=False, show_lines=True
            )
            table.add_column("Setting", style="cyan")
            table.add_column("Value", style="green")

            for key in dir(self):
                table.add_row(key, getattr(self, key))

            console.print(table)

        successful_crawls = await self.agents.writter.crawl_urls()

        if not successful_crawls:
            print_error(
                (
                    "No documents were crawled. "
                    "Check the URLs and try again.\n"
                    "For more information, check the logs or enable debug."
                )
            )
            sys.exit(1)

        print_success(
            f"Successfully crawled {successful_crawls} documents from {len(self.urls)} URLs!"
        )
        sys.exit(0)
