import sys

from code_reviewer_agent.models.base_types import CodeDiff
from code_reviewer_agent.models.reviewer_agent import ReviewerAgent
from code_reviewer_agent.prompts.cr_agent import USER_PROMPT
from code_reviewer_agent.services.base_service import BaseService
from code_reviewer_agent.services.configuration_manager import ConfigurationManager
from code_reviewer_agent.services.platform_factory import PlatformServiceFactory
from code_reviewer_agent.services.repository import RepositoryService
from code_reviewer_agent.services.review_file_processor import ReviewFileProcessor
from code_reviewer_agent.utils.rich_utils import (
    print_debug,
    print_error,
    print_exception,
    print_header,
    print_info,
    print_section,
    print_success,
    print_warning,
)


class ReviewOrchestrator(BaseService):
    """Orchestrates the code review process.

    This class handles the single responsibility of orchestrating the entire review
    workflow, coordinating between different services and managing the overall process
    flow. Following the Single Responsibility Principle, it only handles orchestration
    concerns and delegates specific tasks to appropriate services.

    """

    def __init__(
        self,
        config_manager: ConfigurationManager,
        platform_factory: PlatformServiceFactory,
        reviewer_agent: ReviewerAgent,
    ) -> None:
        """Initialize the review orchestrator.

        Args:
            config_manager: The configuration manager
            platform_factory: The platform service factory
            reviewer_agent: The reviewer agent

        """
        super().__init__(config_manager.config)
        self._config_manager = config_manager
        self._platform_factory = platform_factory
        self._reviewer_agent = reviewer_agent
        self._file_processor = ReviewFileProcessor(
            self.langfuse, config_manager.request_id
        )

        # Create repository service using factory
        self._repository_service = platform_factory.create_service(
            config_manager.platform,
            config_manager.repository,
            config_manager.request_id,
            config_manager.config.schema.reviewer,
        )

    @property
    def repository_service(self) -> RepositoryService:
        """Get the repository service."""
        return self._repository_service

    async def _review_files_without_langfuse(self) -> int:
        """Review all files without langfuse tracing.

        Returns:
            The number of files successfully reviewed

        """
        files_reviewed = 0
        for diff in self.repository_service.diffs:
            try:
                filename = diff.get("filename", "unknown")
                languages = diff.get("languages", ["unknown"])
                patch = diff.get("patch", "")

                if not patch:
                    print_warning(f"No changes found for file: {filename}")
                    continue

                if self._reviewer_agent.debug:
                    print_info(f"Reviewing file: {filename}")
                    print_info(f"  - Languages: {', '.join(languages)}")
                    from code_reviewer_agent.utils.rich_utils import print_diff

                    print_diff(patch)

                # Prepare the User input for the code review
                user_input = USER_PROMPT.format(
                    diff=patch,
                )
                print_debug(f"User input length: {len(user_input)}")

                print_info(f"Starting code review for file: {filename}")

                await self._file_processor.process_file(
                    CodeDiff(**diff),
                    filename,
                    languages,
                    user_input,
                    self._reviewer_agent.agent,
                    self.repository_service,
                    self._config_manager.platform,
                    self._config_manager.repository,
                )

                files_reviewed += 1

            except Exception as file_error:
                print_warning(
                    f"Skipping review of file {filename} due to error: {str(file_error)}"
                )
                continue  # Continue with the next file even if one fails

        print_success(
            f"{files_reviewed}/{len(self.repository_service.diffs)} reviews done and posted successfully!"
        )

        if files_reviewed > 0:
            await self.repository_service._assign_reviewed_label()
        else:
            print_warning(
                "No files reviewed, please check the logs for more information. "
                "Skipping request updates."
            )

        return files_reviewed

    async def _review_files_with_langfuse(self) -> None:
        """Review all files with langfuse tracing."""
        with self.langfuse.tracer.start_as_current_span(
            "CR-Agent-Main-Trace"
        ) as main_span:
            main_span.set_attribute(
                "langfuse.user.id", f"cr-request-{self._config_manager.request_id}"
            )
            main_span.set_attribute(
                "langfuse.session.id",
                f"cr-{self._config_manager.platform}-{self._config_manager.repository}",
            )

            files_reviewed = await self._review_files_without_langfuse()

            main_span.set_attribute("input.value", str(self.repository_service.diffs))
            main_span.set_attribute(
                "output.value",
                f"Reviewed {files_reviewed}/{len(self.repository_service.diffs)} files successfully",
            )

    async def _review_files(self) -> None:
        """Review all files in the repository."""
        if self.langfuse.enabled:
            await self._review_files_with_langfuse()
        else:
            await self._review_files_without_langfuse()

    async def orchestrate_review(self) -> None:
        """Orchestrate the complete code review process.

        This method coordinates the entire review workflow including:
        1. Configuration validation and setup
        2. File analysis and retrieval
        3. Review processing for each file
        4. Error handling and reporting

        """
        print_header("Starting Code Reviewer Agent process")

        if self._reviewer_agent.debug:
            print_section("[DEBUG] Final Configuration retrieved:", "⚙️")
            print_info(f"Platform: {self._config_manager.platform.upper()}")
            print_info(f"Repository: {self._config_manager.repository}")
            print_info(f"Instructions path: {self._config_manager.instructions_path}")
            print_info(f"Request ID: {self._config_manager.request_id}")

        try:
            self.repository_service.request_files_analysis_from_api()
        except Exception as e:
            print_error(
                f"Error fetching {'PR' if self._config_manager.platform == 'github' else 'MR'} files diffs: {str(e)}"
            )
            print_exception()
            sys.exit(1)

        # ========== Reviewer Agent: loop on each file diff ==========
        print_section("Starting Code Review process", "🤖")
        print_debug(
            f"Reviewing {len(self.repository_service.diffs)} file(s) with changes"
        )

        try:
            await self._review_files()
        except Exception as e:
            print_error(f"An unexpected error occurred: {str(e)}")
            print_exception()
            sys.exit(1)

        print_section("Review Complete", "✅")
        print_success("Code review process finished successfully")
        sys.exit(0)
