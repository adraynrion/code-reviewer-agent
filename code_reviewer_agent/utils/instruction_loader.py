import os

from code_reviewer_agent.utils.rich_utils import (
    print_info,
    print_section,
    print_success,
    print_warning,
)


class InstructionPath(tuple):
    """Utility class for loading filesystem instructions.

    This class handles the single responsibility of loading instruction files from the
    filesystem, including error handling and console output. Following the Single
    Responsibility Principle, it only handles instruction loading concerns and provides
    a clean interface for instruction retrieval.

    """

    def __new__(cls, value: str) -> "InstructionPath":
        """Create a new InstructionPath by loading instructions from filesystem.

        Args:
            value: The path to the instructions directory

        Returns:
            An InstructionPath instance containing loaded instructions

        """
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
