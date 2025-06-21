import os
from pathlib import Path
from typing import Any, Dict

import yaml
from rich.table import Table

from code_reviewer_agent.models.pydantic_config_models import ConfigModel
from code_reviewer_agent.utils.rich_utils import console, print_debug


class ConfigFilePath:
    """Configuration definition."""

    def __init__(self) -> None:
        self.find_file()

    def find_file(self) -> None:
        for path in self.default_paths:
            if path.exists():
                self.file = path
                return

        raise SystemExit(
            "Could not find config file in standard locations! Refer to README for instructions."
        )

    @property
    def default_paths(self) -> list[Path]:
        return [
            Path.cwd() / "config.yaml",  # ./config.yaml
            Path.home()
            / ".config"
            / "code-reviewer"
            / "config.yaml",  # ~/.config/code-reviewer/config.yaml
            Path("/etc/code-reviewer/config.yaml"),  # /etc/code-reviewer/config.yaml
        ]

    @property
    def file(self) -> Path:
        return self._file

    @file.setter
    def file(self, value: Path) -> None:
        self._file = value


class Config:
    """Configuration singleton."""

    _instance = None

    def __new__(cls, *args: Any, **kwargs: Any) -> "Config":
        if not cls._instance:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance

    def __init__(self, **kwargs: Any) -> None:
        self._file = ConfigFilePath()
        self._load_config_from_file()
        self._update_config(**kwargs)

        os.environ["DEBUG"] = self.debug.__str__()
        console.print(self.to_table())

    @property
    def file(self) -> Path:
        return self._file.file

    @property
    def schema(self) -> ConfigModel:
        return self._schema

    @property
    def debug(self) -> bool:
        return self._debug

    def to_table(self) -> Table:
        """Print the current configuration schema (without sensitive data)."""

        table = Table(title="Current Configuration", show_header=False, show_lines=True)
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")

        # ===== Add non-sensitive configuration =====
        # Crawler
        for field_name in self.schema.crawler.__class__.model_fields:
            if field_name in ("openai_api_key"):
                # Mask sensitive fields
                value = (
                    "*" * 8 if getattr(self.schema.crawler, field_name, None) else ""
                )
            else:
                value = str(getattr(self.schema.crawler, field_name, ""))

            table.add_row(field_name, value)

        # Reviewer
        for field_name in self.schema.reviewer.__class__.model_fields:
            if field_name in ("github_token", "gitlab_token", "llm"):
                # Mask sensitive fields
                value = (
                    "*" * 8 if getattr(self.schema.reviewer, field_name, None) else ""
                )
            else:
                value = str(getattr(self.schema.reviewer, field_name, ""))

            table.add_row(field_name, value)

        # Reviewer - LLM
        for field_name in self.schema.reviewer.llm.__class__.model_fields:
            if field_name in ("api_key"):
                # Mask sensitive fields
                value = (
                    "*" * 8
                    if getattr(self.schema.reviewer.llm, field_name, None)
                    else ""
                )
            else:
                value = str(getattr(self.schema.reviewer.llm, field_name, ""))
            table.add_row(field_name, value)

        # Supabase
        for field_name in self.schema.supabase.__class__.model_fields:
            if field_name in ("key"):
                # Mask sensitive fields
                value = (
                    "*" * 8 if getattr(self.schema.supabase, field_name, None) else ""
                )
            else:
                value = str(getattr(self.schema.supabase, field_name, ""))

            table.add_row(field_name, value)

        # Langfuse
        for field_name in self.schema.langfuse.__class__.model_fields:
            if field_name in ("public_key", "secret_key"):
                # Mask sensitive fields
                value = (
                    "*" * 8 if getattr(self.schema.langfuse, field_name, None) else ""
                )
            else:
                value = str(getattr(self.schema.langfuse, field_name, ""))

            table.add_row(field_name, value)

        # Logging
        for field_name in self.schema.logging.__class__.model_fields:
            value = str(getattr(self.schema.logging, field_name, ""))
            table.add_row(field_name, value)

        return table

    def _load_config_from_file(self) -> None:
        try:
            # Start with defaults
            config_data: Dict[str, Any] = {}

            # Load from YAML
            with open(self.file, "r", encoding="utf-8") as f:
                config_data.update(yaml.safe_load(f) or {})
        except Exception as e:
            raise SystemExit(f"Error loading config from {self.file}: {e}")

        print_debug(f"Loaded config: {config_data}")

        self._schema = ConfigModel(**config_data)
        self._debug = self._schema.logging.debug

    def _update_config(self, **kwargs: Any) -> None:
        args = kwargs

        ##### Crawler #####
        if args.get("max_pages", None):
            self._schema.crawler.max_pages = args["max_pages"]
        if args.get("max_depth", None):
            self._schema.crawler.max_depth = args["max_depth"]
        if args.get("concurrent_tasks", None):
            self._schema.crawler.concurrent_tasks = args["concurrent_tasks"]
        if args.get("extraction_type", None):
            self._schema.crawler.extraction_type = args["extraction_type"]
        if args.get("chunk_token_threshold", None):
            self._schema.crawler.chunk_token_threshold = args["chunk_token_threshold"]
        if args.get("overlap_rate", None):
            self._schema.crawler.overlap_rate = args["overlap_rate"]
        if args.get("temperature", None):
            self._schema.crawler.temperature = args["temperature"]
        if args.get("max_tokens", None):
            self._schema.crawler.max_tokens = args["max_tokens"]
        if args.get("headless", None):
            self._schema.crawler.headless = args["headless"]
        if args.get("locale", None):
            self._schema.crawler.locale = args["locale"]
        if args.get("timezone", None):
            self._schema.crawler.timezone = args["timezone"]
        if args.get("keywords", None):
            self._schema.crawler.keywords = args["keywords"]
        if args.get("keyword_weight", None):
            self._schema.crawler.keyword_weight = args["keyword_weight"]

        ##### Reviewer #####
        if args.get("platform", None):
            self._schema.reviewer.platform = args["platform"]
        if args.get("repository", None):
            self._schema.reviewer.repository = args["repository"]
        if args.get("instructions_path", None):
            self._schema.reviewer.instruction_dir_path = args["instructions_path"]
