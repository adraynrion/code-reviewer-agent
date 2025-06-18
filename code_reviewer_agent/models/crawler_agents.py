from typing import Any, Dict

from code_reviewer_agent.config.config import Config
from code_reviewer_agent.services.crawler import Urls
from code_reviewer_agent.services.crawler_read import CrawlerReader
from code_reviewer_agent.services.crawler_write import CrawlerWritter
from supabase import Client as SupabaseClient


class CrawlerAgents:
    _config: Config
    _supabase_client: SupabaseClient
    _writter = None
    _reader = None

    def __init__(self, config: Config, urls: Urls) -> None:
        self._config = config
        self._supabase_client = SupabaseClient()
        args: Dict[str, Any] = {
            "urls": urls,
            "supabase_client": self._supabase_client,
            "supabase_table": self.supabase_table,
            "max_pages": config.schema.crawler.max_pages,
            "max_depth": config.schema.crawler.max_depth,
            "concurrent_tasks": config.schema.crawler.concurrent_tasks,
            "extraction_type": self.extraction_type,
            "chunk_token_threshold": config.schema.crawler.chunk_token_threshold,
            "overlap_rate": config.schema.crawler.overlap_rate,
            "temperature": config.schema.crawler.temperature,
            "max_tokens": config.schema.crawler.max_tokens,
            "headless": config.schema.crawler.headless,
            "locale": config.schema.crawler.locale,
            "timezone": config.schema.crawler.timezone,
            "keywords": config.schema.crawler.keywords,
            "keyword_weight": config.schema.crawler.keyword_weight,
            "prefixed_provider": self.prefixed_provider,
            "base_url": self.base_url,
            "api_token": config.schema.crawler.openai_api_key,
            "embedding_model": self.embedding_model,
            "debug": config.schema.logging.debug,
        }

        self._writter = CrawlerWritter(args)
        self._reader = CrawlerReader(args)

    @property
    def supabase_table(self):
        return self._supabase_client.table("documents")

    @property
    def writter(self) -> CrawlerWritter:
        return self._writter

    @property
    def reader(self) -> CrawlerReader:
        return self._reader

    @property
    def extraction_type(self) -> str:
        """Always use schema extraction for now."""
        return "schema"

    @property
    def provider(self) -> str:
        """OpenAI is the only supported Provider for now."""
        return "openai"

    @property
    def embedding_model(self) -> str:
        return self._config.schema.crawler.embedding_model

    @property
    def prefixed_provider(self) -> str:
        return f"{self.provider}/{self.embedding_model}"

    @property
    def base_url(self) -> str:
        """OpenAI is the only supported Provider for now."""
        return "https://api.openai.com/v1"
