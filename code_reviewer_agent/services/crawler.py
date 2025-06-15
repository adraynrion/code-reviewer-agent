import sys
from typing import List

from rich.table import Table

from code_reviewer_agent.config.config import Config
from code_reviewer_agent.models.base_types import (
    PositiveFloatValidator,
    PositiveIntegerValidator,
)
from code_reviewer_agent.models.crawler_agents import CrawlerAgents
from code_reviewer_agent.services.base_service import BaseService
from code_reviewer_agent.utils.rich_utils import (
    console,
    print_debug,
    print_error,
    print_header,
    print_success,
)


class ApiKey(StringValidator):
    pass


class EmbeddingModel(StringValidator):
    pass


class Urls(List[str]):
    def __set__(self, instance, value: List[str]) -> None:
        if not value or len(value) == 0:
            raise ValueError("At least one URL is required")
        super().__set__(instance, value)


class MaxPages(PositiveIntegerValidator):
    pass


class MaxDepth(PositiveIntegerValidator):
    pass


class ConcurrentTasks(PositiveIntegerValidator):
    pass


class ExtractionType(StringValidator):
    pass


class ChunkTokenThreshold(PositiveIntegerValidator):
    pass


class OverlapRate(PositiveFloatValidator):
    pass


class Temperature(PositiveFloatValidator):
    pass


class MaxTokens(PositiveIntegerValidator):
    pass


class Headless(bool):
    pass


class Locale(StringValidator):
    def __set__(self, instance, value: str) -> None:
        formated_value = value.lower().strip()

        from babel import Locale

        try:
            Locale.parse(formated_value, sep="-")
        except ValueError:
            raise ValueError(
                f"Invalid locale. Must be a valid BCP 47 language tag. Got {formated_value}"
            )

        super().__set__(instance, formated_value)


class Timezone(StringValidator):
    def __set__(self, instance, value: str) -> None:
        formated_value = value.lower().strip()

        from dateutil.tz import gettz

        if gettz(formated_value) is None:
            raise ValueError(
                f"Invalid timezone. Must be a valid timezone string. Got {formated_value}"
            )

        super().__set__(instance, formated_value)


class Keywords(List[str]):
    pass


class KeywordWeight(PositiveFloatValidator):
    pass


class CrawlService(BaseService):
    _agents = None
    _enabled = False
    _openai_api_key = ApiKey()
    _embedding_model = EmbeddingModel()
    _urls = Urls()
    _max_pages = MaxPages()
    _max_depth = MaxDepth()
    _concurrent_tasks = ConcurrentTasks()
    _extraction_type = ExtractionType()
    _chunk_token_threshold = ChunkTokenThreshold()
    _overlap_rate = OverlapRate()
    _temperature = Temperature()
    _max_tokens = MaxTokens()
    _headless = Headless()
    _locale = Locale()
    _timezone = Timezone()
    _keywords = Keywords()
    _keyword_weight = KeywordWeight()

    def __init__(self, **kwargs) -> None:
        super().__init__(Config())

        crawler_config = self.config.schema.crawler
        self._enabled = crawler_config.enabled
        self._openai_api_key = crawler_config.openai_api_key
        self._embedding_model = crawler_config.embedding_model

        self._urls = kwargs.get("urls")
        self._max_pages = kwargs.get("max_pages") or crawler_config.max_pages
        self._max_depth = kwargs.get("max_depth") or crawler_config.max_depth
        self._concurrent_tasks = (
            kwargs.get("concurrent_tasks") or crawler_config.concurrent_tasks
        )
        self._extraction_type = (
            kwargs.get("extraction_type") or crawler_config.extraction_type
        )
        self._chunk_token_threshold = (
            kwargs.get("chunk_token_threshold") or crawler_config.chunk_token_threshold
        )
        self._overlap_rate = kwargs.get("overlap_rate") or crawler_config.overlap_rate
        self._temperature = kwargs.get("temperature") or crawler_config.temperature
        self._max_tokens = kwargs.get("max_tokens") or crawler_config.max_tokens
        self._headless = kwargs.get("headless") or crawler_config.headless
        self._locale = kwargs.get("locale") or crawler_config.locale
        self._timezone = kwargs.get("timezone") or crawler_config.timezone
        self._keywords = (
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
        self._keyword_weight = (
            kwargs.get("keyword_weight") or crawler_config.keyword_weight
        )

        self._agents = CrawlerAgents(self.config, self.urls)

    def __dict__(self) -> dict:
        return {
            "enabled": self._enabled,
            "openai_api_key": self._openai_api_key,
            "embedding_model": self._embedding_model,
            "urls": self._urls,
            "max_pages": self._max_pages,
            "max_depth": self._max_depth,
            "concurrent_tasks": self._concurrent_tasks,
            "extraction_type": self._extraction_type,
            "chunk_token_threshold": self._chunk_token_threshold,
            "overlap_rate": self._overlap_rate,
            "temperature": self._temperature,
            "max_tokens": self._max_tokens,
            "headless": self._headless,
            "locale": self._locale,
            "timezone": self._timezone,
            "keywords": self._keywords,
            "keyword_weight": self._keyword_weight,
        }

    def __repr__(self) -> str:
        table = Table(title="Current Configuration", show_header=False, show_lines=True)
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")

        for key, value in self.__dict__().items():
            table.add_row(key, value)

        return table

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
        Urls.__set__(self._urls, value)

    @property
    def max_pages(self) -> MaxPages:
        return self._max_pages

    @max_pages.setter
    def max_pages(self, value: int) -> None:
        MaxPages.__set__(self._max_pages, value)

    @property
    def max_depth(self) -> MaxDepth:
        return self._max_depth

    @max_depth.setter
    def max_depth(self, value: int) -> None:
        MaxDepth.__set__(self._max_depth, value)

    @property
    def concurrent_tasks(self) -> ConcurrentTasks:
        return self._concurrent_tasks

    @concurrent_tasks.setter
    def concurrent_tasks(self, value: int) -> None:
        ConcurrentTasks.__set__(self._concurrent_tasks, value)

    @property
    def extraction_type(self) -> ExtractionType:
        return self._extraction_type

    @extraction_type.setter
    def extraction_type(self, value: str):
        formated_value = value.lower().strip()
        if formated_value not in ("schema", "block"):
            raise ValueError(
                "Invalid extraction type. Must be either 'schema' or 'block'."
            )
        ExtractionType.__set__(self._extraction_type, formated_value)

    @property
    def chunk_token_threshold(self) -> ChunkTokenThreshold:
        return self._chunk_token_threshold

    @chunk_token_threshold.setter
    def chunk_token_threshold(self, value: int) -> None:
        ChunkTokenThreshold.__set__(self._chunk_token_threshold, value)

    @property
    def overlap_rate(self) -> OverlapRate:
        return self._overlap_rate

    @overlap_rate.setter
    def overlap_rate(self, value: float) -> None:
        OverlapRate.__set__(self._overlap_rate, value)

    @property
    def temperature(self) -> Temperature:
        return self._temperature

    @temperature.setter
    def temperature(self, value: float) -> None:
        Temperature.__set__(self._temperature, value)

    @property
    def max_tokens(self) -> MaxTokens:
        return self._max_tokens

    @max_tokens.setter
    def max_tokens(self, value: int) -> None:
        MaxTokens.__set__(self._max_tokens, value)

    @property
    def headless(self) -> Headless:
        return self._headless

    @headless.setter
    def headless(self, value: bool) -> None:
        Headless.__set__(self._headless, value)

    @property
    def locale(self) -> Locale:
        return self._locale

    @locale.setter
    def locale(self, value: str) -> None:
        Locale.__set__(self._locale, value)

    @property
    def timezone(self) -> Timezone:
        return self._timezone

    @timezone.setter
    def timezone(self, value: str) -> None:
        Timezone.__set__(self._timezone, value)

    @property
    def keywords(self) -> Keywords:
        return self._keywords

    @keywords.setter
    def keywords(self, value: List[str]) -> None:
        Keywords.__set__(self._keywords, value)

    @property
    def keyword_weight(self) -> KeywordWeight:
        return self._keyword_weight

    @keyword_weight.setter
    def keyword_weight(self, value: float) -> None:
        KeywordWeight.__set__(self._keyword_weight, value)

    async def main(self) -> None:
        console.clear()
        print_header("Starting Web Crawler Service process")
        print_debug(self)

        results = await self.agents.writter.crawl_urls(
            urls=self.urls,
            max_pages=self.max_pages,
            max_depth=self.max_depth,
            concurrent_tasks=self.concurrent_tasks,
            extraction_type=self.extraction_type,
            chunk_token_threshold=self.chunk_token_threshold,
            overlap_rate=self.overlap_rate,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            headless=self.headless,
            locale=self.locale,
            timezone=self.timezone,
            keywords=self.keywords,
            keyword_weight=self.keyword_weight,
        )

        if not results:
            print_error(
                (
                    "No documents were crawled. "
                    "Check the URLs and try again.\n"
                    "For more information, check the logs or enable debug."
                )
            )
            sys.exit(1)

        print_success(
            f"Successfully crawled {len(results)} documents from {len(self.urls)} URLs!"
        )
        sys.exit(0)
