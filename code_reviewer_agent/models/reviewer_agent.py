import os

from pydantic_ai import Agent
from pydantic_ai.settings import ModelSettings

from code_reviewer_agent.config.config import Config
from code_reviewer_agent.models.base_agent import AiModel, AiModelType
from code_reviewer_agent.models.base_types import ConfigArgs
from code_reviewer_agent.prompts.cr_agent import SYSTEM_PROMPT
from code_reviewer_agent.services.crawler_read import CrawlerReader
from code_reviewer_agent.utils.rich_utils import (
    print_debug,
    print_header,
    print_info,
    print_section,
    print_success,
    print_warning,
)


class InstructionPath(tuple):
    def __new__(cls, value: str) -> "InstructionPath":
        print_section("Retrieving additional filesystem instructions")

        if not os.path.exists(value) and not os.path.isdir(value):
            print_warning(
                "Additional filesystem instructions folder invalid or not found! "
                "Continuing without any filesystem instructions."
            )
            return super().__new__(cls, [])

        print_info(f"Looking for instructions in: {value}")
        filesystem_instructions = []
        try:
            # List all files in the instructions directory using direct filesystem access
            instructions_files = (
                f for f in os.listdir(value) if os.path.isfile(os.path.join(value, f))
            )

            for file in instructions_files:
                file_path = os.path.join(value, file)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        filesystem_instructions.append(content)
                        print_success(f"  - Loaded: {file} ({len(content)} chars)")
                except Exception as file_error:
                    print_warning(f"  - Failed to load {file}: {str(file_error)}")

            if not filesystem_instructions:
                raise Exception("No instruction files found or loaded successfully")

            print_success(
                f"Successfully loaded {len(filesystem_instructions)} instruction file(s)"
            )
            return super().__new__(cls, filesystem_instructions)
        except Exception as e:
            print_warning(f"Error while retrieving filesystem instructions: {str(e)}")
            print_warning("Continuing without filesystem instructions")
            return super().__new__(cls, [])


class ReviewerAgent(AiModel, metaclass=AiModelType):
    def __init__(self, config: Config) -> None:
        AiModel.__init__(self, config)

        self._instruction_path = InstructionPath(
            config.schema.reviewer.instruction_dir_path
        )
        self._setup_agent()

    @property
    def embedding_model(self) -> str:
        return self._config.schema.crawler.embedding_model

    @property
    def agent(self) -> Agent[None, str]:
        return self._agent

    def _setup_agent(self) -> None:
        print_header("Generating the CR Agent")

        system_prompt = SYSTEM_PROMPT.format(
            custom_user_instructions="\n".join(self._instruction_path)
        )

        config_args = ConfigArgs(
            supabase_url=self._config.schema.supabase.url,
            supabase_key=self._config.schema.supabase.key,
            embedding_model=self.embedding_model,
            debug=self.debug,
        )
        crawler_reader = CrawlerReader(config_args)
        tools = [crawler_reader.search_documents]

        print_debug(f"System prompt length: {len(system_prompt)}")
        print_debug(f"Tools length: {len(tools)}")

        model_settings = ModelSettings(
            max_tokens=self.llm_config.max_tokens,
            temperature=self.llm_config.temperature,
            top_p=self.llm_config.top_p,
        )

        print_success("Returning fully configured CR Agent")
        self._agent = Agent(
            model=self.model,
            system_prompt=system_prompt,
            name="Code Reviewer Agent",
            model_settings=model_settings,
            retries=self.llm_config.max_attempts,
            output_retries=self.llm_config.max_attempts,
            tools=tools,
            instrument=True,
        )
