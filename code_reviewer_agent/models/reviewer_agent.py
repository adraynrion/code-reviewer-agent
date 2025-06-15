import os
from weakref import WeakKeyDictionary

from pydantic_ai import Agent
from pydantic_ai.settings import ModelSettings

from code_reviewer_agent.config.config import Config
from code_reviewer_agent.models.base_agent import AiModel, AiModelType
from code_reviewer_agent.prompts.cr_agent import SYSTEM_PROMPT
from code_reviewer_agent.services.crawler_read import search_documents
from code_reviewer_agent.utils.rich_utils import (
    print_debug,
    print_header,
    print_info,
    print_section,
    print_success,
    print_warning,
)


class InstructionPath:
    """Instruction path validator."""

    def __init__(self) -> None:
        self._valeurs = WeakKeyDictionary()

    def __get__(self, instance, owner) -> tuple[str]:
        return self._valeurs.get(instance, tuple())

    def __set__(self, instance, instruction_path: str) -> None:
        print_section("Retrieving additional filesystem instructions")

        if not os.path.exists(instruction_path) and not os.path.isdir(instruction_path):
            print_warning(
                "Additional filesystem instructions folder invalid or not found! "
                "Continuing without any filesystem instructions."
            )
            return

        print_info(f"Looking for instructions in: {instruction_path}")
        filesystem_instructions = []
        try:
            # List all files in the instructions directory using direct filesystem access
            instructions_files = (
                f
                for f in os.listdir(instruction_path)
                if os.path.isfile(os.path.join(instruction_path, f))
            )

            for file in instructions_files:
                file_path = os.path.join(instruction_path, file)
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
            self._valeurs[instance] = tuple(filesystem_instructions)
        except Exception as e:
            print_warning(f"Error while retrieving filesystem instructions: {str(e)}")
            print_warning("Continuing without filesystem instructions")

    def __delete__(self, instance):
        if instance in self._valeurs:
            del self._valeurs[instance]
        else:
            raise AttributeError("Instruction path not set")


class ReviewerAgent(AiModel, metaclass=AiModelType):
    _instruction_path = InstructionPath()

    def __init__(self, config: Config) -> None:
        AiModel.__init__(self, config)

        self._instruction_path = config.schema.reviewer.instruction_dir_path
        self._setup_agent()

    @property
    def agent(self) -> Agent[None, str]:
        return self._agent

    def _setup_agent(self) -> None:
        print_header("Generating the CR Agent")

        system_prompt = SYSTEM_PROMPT.format(
            custom_user_instructions="\n".join(self._instruction_path)
        )
        tools = [search_documents]

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
