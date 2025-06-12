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
from pydantic_ai.settings import ModelSettings
from supabase import Client, create_client

from code_reviewer_agent.config.config import config
from code_reviewer_agent.prompts.cr_agent import SYSTEM_PROMPT
from code_reviewer_agent.utils.crawler_utils import search_documents
from code_reviewer_agent.utils.rich_utils import (
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
    return create_client(config.supabase.url, config.supabase.key)


def get_model(as_llm_config: bool = False) -> Union[Model, LLMConfig]:
    provider = config.reviewer.llm.provider
    llm = config.reviewer.llm.model_name
    api_key = config.reviewer.llm.api_key

    if not as_llm_config:
        if provider == "OpenAI" or provider == "TogetherAI":
            return OpenAIModel(
                llm,
                provider=OpenAIProvider(
                    base_url=config.reviewer.llm.base_url, api_key=api_key
                ),
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


def get_code_review_agent() -> Agent[None, str]:
    """Build and return an agent with the merged system prompt + custom user
    instructions, and the crawling search tool."""

    print_header("Generating the CR Agent")
    instruction_path = config.reviewer.instruction_dir_path

    # ========== Retrieving additional filesystem instructions ==========
    print_section("Retrieving additional filesystem instructions")

    if os.path.exists(instruction_path) and os.path.isdir(instruction_path):
        print_info(f"Looking for instructions in: {instruction_path}")

        filesystem_instructions = []
        try:
            # List all files in the instructions directory using direct filesystem access
            instructions_files = [
                f
                for f in os.listdir(instruction_path)
                if os.path.isfile(os.path.join(instruction_path, f))
            ]

            for file in instructions_files:
                file_path = os.path.join(instruction_path, file)
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

    else:
        print_warning(
            "Additional filesystem instructions folder invalid or not found! "
            "Continuing without any filesystem instructions."
        )

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
    if config.logging.debug:
        print_info(f"System prompt length: {len(system_prompt)}")
        print_info(f"Tools length: {len(tools)}")
        print_info(f"Provider: {config.reviewer.llm.provider}")
        print_info(f"Model: {config.reviewer.llm.model_name}")

    model_settings = ModelSettings(
        max_tokens=config.reviewer.llm.max_tokens,
        temperature=config.reviewer.llm.temperature,
        top_p=config.reviewer.llm.top_p,
    )

    return Agent(
        model=model,
        system_prompt=system_prompt,
        name="Code Reviewer Agent",
        model_settings=model_settings,
        retries=config.reviewer.llm.max_attempts,
        output_retries=config.reviewer.llm.max_attempts,
        tools=tools,
        instrument=True,
    )
