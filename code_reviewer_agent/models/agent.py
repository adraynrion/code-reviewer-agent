"""Agent models and utilities."""

import os
from typing import Union

from crawl4ai import LLMConfig
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models import Model
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.providers.openrouter import OpenRouterProvider
from supabase import Client, create_client

from ..prompts.cr_agent import SYSTEM_PROMPT
from ..utils.config import config
from ..utils.crawler_utils import search_documents
from ..utils.rich_utils import (
    print_header,
    print_info,
    print_section,
    print_success,
    print_warning,
)


class CodeReviewResponse(BaseModel):
    """Response model for the generated code review response."""

    line_number: int = Field(
        ..., description="The line number where the issue or suggestion applies"
    )

    code_diff: str = Field(
        ...,
        description="A properly formatted code suggestion using `diff` syntax (inside a Markdown fenced code block) showing how the developer should fix the issue",
    )

    comment: str = Field(
        ...,
        description="A clear and detailed explanation of what the issue is, why it matters, and how to fix it. Be educational and constructive.",
    )

    title: str = Field(
        ..., description="A short, descriptive title summarizing the feedback"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "line_number": 1,
                "code_diff": "```diff\n- # Ceci est un commentaire en français\n+ # This is a comment in English\n````\n",
                "comment": "We enforce the use of English in comments and documentation for this project.",
                "title": "Use English in comments and documentation",
            }
        }
    }

    def print_info(self) -> None:
        """Print the code review response information."""
        print_info(f"Line number: {self.line_number}")
        print_info(f"Code diff: {self.code_diff}")
        print_info(f"Comment: {self.comment}")
        print_info(f"Title: {self.title}")


def get_supabase() -> Client:
    """Initialize and return a Supabase client."""
    return create_client(config.SUPABASE_URL, config.SUPABASE_KEY)


def get_embedding_model_str() -> str:
    """Get the embedding model string from environment variables."""
    return config.EMBEDDING_MODEL


def get_model(as_llm_config: bool = False) -> Union[Model, LLMConfig]:
    provider = config.PROVIDER
    llm = config.MODEL_CHOICE
    api_key = config.LLM_API_KEY

    if not as_llm_config:
        if provider == "OpenAI" or provider == "TogetherAI":
            return OpenAIModel(
                llm, provider=OpenAIProvider(base_url=config.BASE_URL, api_key=api_key)
            )
        elif provider == "OpenRouter":
            return OpenAIModel(llm, provider=OpenRouterProvider(api_key=api_key))
        elif provider == "Google":
            return GoogleModel(llm, provider=GoogleProvider(api_key=api_key))
    else:
        if provider == "OpenAI":
            return LLMConfig(provider="openai/" + llm, api_token=api_key)
        elif provider == "TogetherAI":
            return LLMConfig(provider="together_ai/" + llm, api_token=api_key)
        elif provider == "OpenRouter":
            return LLMConfig(provider="openrouter/" + llm, api_token=api_key)
        elif provider == "Google":
            return LLMConfig(provider="gemini/" + llm, api_token=api_key)

    raise ValueError(f"Unsupported provider: {provider}")


def get_code_review_agent() -> Agent:
    """Build and return an agent with the merged system prompt + custom user
    instructions, and the crawling search tool."""

    print_header("Generating the CR Agent")

    # ========== Retrieving filesystem instructions ==========
    print_section("Retrieving Filesystem Instructions")
    print_info(f"Looking for instructions in: {config.LOCAL_FILE_DIR}")

    filesystem_instructions = []
    try:
        # List all files in the instructions directory using direct filesystem access
        instructions_files = [
            f
            for f in os.listdir(config.LOCAL_FILE_DIR)
            if os.path.isfile(os.path.join(config.LOCAL_FILE_DIR, f))
        ]

        for file in instructions_files:
            file_path = os.path.join(config.LOCAL_FILE_DIR, file)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    filesystem_instructions.append(content)
                    print_success(f"  - Loaded: {file} ({len(content)} bytes)")
            except Exception as file_error:
                print_warning(f"  - Failed to load {file}: {str(file_error)}")

        if not filesystem_instructions:
            print_warning("No instruction files found or loaded successfully")
            print_warning("Continuing without filesystem instructions")
        else:
            print_success(
                f"Successfully loaded {len(filesystem_instructions)} instruction file(s)"
            )

    except Exception as e:
        print_warning(f"Error while retrieving filesystem instructions: {str(e)}")
        print_warning("Continuing without filesystem instructions")

    # ========== Building system prompt ==========
    print_section("Building System Prompt")
    system_prompt = SYSTEM_PROMPT.format(
        custom_user_instructions="\n".join(filesystem_instructions)
    )
    print_success("System prompt built successfully!")

    # ========== Building tools ==========
    print_section("Building Tools")
    tools = [search_documents]
    print_success("Tools built successfully!")

    # ========== Building agent ==========
    print_success("Returning fully configured CR Agent")
    model = get_model()
    if config.DEBUG:
        print_info(f"System prompt length: {len(system_prompt)}")
        print_info(f"Tools length: {len(tools)}")
        print_info(f"Provider: {config.PROVIDER}")
        print_info(f"Model: {config.MODEL_CHOICE}")

    return Agent(
        model=model,
        # temperature=ai_config.temperature,
        # max_tokens=ai_config.max_tokens,
        # top_p=ai_config.top_p,
        system_prompt=system_prompt,
        retries=5,
        output_retries=5,
        tools=tools,
        instrument=True,
    )
