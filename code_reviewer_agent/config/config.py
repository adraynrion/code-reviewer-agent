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
            cls._instance = super(Config, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self) -> None:
        self._file = ConfigFilePath()
        self._load_config_from_file()

        os.environ["DEBUG"] = self.debug.__str__()
        console.print(self.to_table())

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
                value = "*" * 8 if getattr(self, field_name, None) else ""
            else:
                value = str(getattr(self, field_name, ""))

            table.add_row(field_name, value)

        # Reviewer
        for field_name in self.schema.reviewer.__class__.model_fields:
            if field_name in ("github_token", "gitlab_token", "llm"):
                # Mask sensitive fields
                value = "*" * 8 if getattr(self, field_name, None) else ""
            else:
                value = str(getattr(self, field_name, ""))

            table.add_row(field_name, value)

        # Reviewer - LLM
        for field_name in self.schema.reviewer.llm.__class__.model_fields:
            if field_name in ("api_key"):
                # Mask sensitive fields
                value = "*" * 8 if getattr(self, field_name, None) else ""
            else:
                value = str(getattr(self, field_name, ""))
            table.add_row(field_name, value)

        # Supabase
        for field_name in self.schema.supabase.__class__.model_fields:
            if field_name in ("key"):
                # Mask sensitive fields
                value = "*" * 8 if getattr(self, field_name, None) else ""
            else:
                value = str(getattr(self, field_name, ""))

            table.add_row(field_name, value)

        # Langfuse
        for field_name in self.schema.langfuse.__class__.model_fields:
            if field_name in ("public_key", "secret_key"):
                # Mask sensitive fields
                value = "*" * 8 if getattr(self, field_name, None) else ""
            else:
                value = str(getattr(self, field_name, ""))

            table.add_row(field_name, value)

        # Logging
        for field_name in self.schema.logging.__class__.model_fields:
            value = str(getattr(self, field_name, ""))
            table.add_row(field_name, value)

        return table

    @property
    def file(self) -> Path:
        return self._file.file

    @property
    def schema(self) -> ConfigModel:
        return self._schema

    @property
    def debug(self) -> bool:
        return self._debug

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
