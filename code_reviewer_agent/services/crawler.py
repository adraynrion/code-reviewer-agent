import sys
from typing import Any, cast

from code_reviewer_agent.config.config import Config
from code_reviewer_agent.models.base_types import Urls
from code_reviewer_agent.models.crawler_agents import CrawlerAgents
from code_reviewer_agent.services.base_service import BaseService
from code_reviewer_agent.utils.rich_utils import (
    print_error,
    print_header,
    print_success,
)


class CrawlService(BaseService):
    def __init__(self, urls: Urls, **kwargs: Any) -> None:
        super().__init__(Config(kwargs=kwargs))

        self.urls = urls
        self._agents = CrawlerAgents(self.config, self.urls)

    @property
    def urls(self) -> Urls:
        return self._urls

    @urls.setter
    def urls(self, value: Urls) -> None:
        if not value:
            raise ValueError("URLs are required")
        elif not isinstance(value, tuple):
            raise ValueError("URLs must be a tuple")
        self._urls = value

    @property
    def agents(self) -> CrawlerAgents:
        return self._agents

    @property
    def debug(self) -> bool:
        return self.config.schema.logging.debug

    @property
    def enabled(self) -> bool:
        return self.config.schema.crawler.enabled

    @property
    def openai_api_key(self) -> str:
        return self.config.schema.crawler.openai_api_key

    @property
    def embedding_model(self) -> str:
        return self.config.schema.crawler.embedding_model

    @property
    def max_pages(self) -> int:
        return self.config.schema.crawler.max_pages

    @property
    def max_depth(self) -> int:
        return self.config.schema.crawler.max_depth

    @property
    def concurrent_tasks(self) -> int:
        return self.config.schema.crawler.concurrent_tasks

    @property
    def extraction_type(self) -> str:
        return self.config.schema.crawler.extraction_type

    @property
    def chunk_token_threshold(self) -> int:
        return self.config.schema.crawler.chunk_token_threshold

    @property
    def overlap_rate(self) -> float:
        return self.config.schema.crawler.overlap_rate

    @property
    def temperature(self) -> float:
        return self.config.schema.crawler.temperature

    @property
    def max_tokens(self) -> int:
        return self.config.schema.crawler.max_tokens

    @property
    def headless(self) -> bool:
        return self.config.schema.crawler.headless

    @property
    def locale(self) -> str:
        return self.config.schema.crawler.locale

    @property
    def timezone(self) -> str:
        return self.config.schema.crawler.timezone

    @property
    def keywords(self) -> list[str]:
        return self.config.schema.crawler.keywords

    @property
    def keyword_weight(self) -> float:
        return self.config.schema.crawler.keyword_weight

    async def main(self) -> None:
        print_header("Starting Web Crawler Service process")

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
