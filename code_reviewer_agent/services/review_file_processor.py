import time
from typing import List

from pydantic_ai import Agent

from code_reviewer_agent.models.base_types import CodeDiff, RequestId
from code_reviewer_agent.models.pydantic_reviewer_models import CodeReviewResponse
from code_reviewer_agent.services.repository import RepositoryService
from code_reviewer_agent.utils.langfuse import LangfuseModel
from code_reviewer_agent.utils.rich_utils import print_debug, print_success


class ReviewFileProcessor:
    """Processes individual files for code review.

    This class handles the single responsibility of processing individual files through
    the review workflow, including AI agent interaction and result posting. Following
    the Single Responsibility Principle, it only handles file-level review processing
    and delegates other concerns to appropriate services.

    """

    def __init__(self, langfuse: LangfuseModel, request_id: RequestId) -> None:
        """Initialize the review file processor.

        Args:
            langfuse: The langfuse model for observability
            request_id: The pull/merge request ID

        """
        self._langfuse = langfuse
        self._request_id = request_id

    async def process_file_without_langfuse(
        self,
        diff: CodeDiff,
        user_input: str,
        agent: Agent[None, str],
        repository_service: RepositoryService,
    ) -> CodeReviewResponse:
        """Process a single file for code review without langfuse tracing.

        Args:
            diff: The code diff to review
            user_input: The formatted user input for the agent
            agent: The AI agent to use for review
            repository_service: The repository service for posting comments

        Returns:
            The code review response from the agent

        Raises:
            ValueError: If the AI returns an invalid response
            Exception: If agent run or comment posting fails

        """
        start_time = time.perf_counter()
        reviewer_output: CodeReviewResponse

        try:
            reviewer_response = await agent.run(
                user_input,
                output_type=CodeReviewResponse,
            )
            reviewer_output = reviewer_response.output

            if not reviewer_output or not hasattr(reviewer_output, "comment"):
                raise ValueError("The AI did not return a valid code review response!")
        except ValueError:
            raise
        except Exception as agent_error:
            raise Exception(f"Agent run failed: {str(agent_error)}")

        duration = time.perf_counter() - start_time
        print_debug(f"Code review completed in {duration:.2f} seconds")
        print_success(f"Code review response successfully retrieved from Agent")

        print_debug(str(reviewer_output))

        # Post review comments to the PR/MR
        try:
            await repository_service.post_review_comments(diff, reviewer_output)
            return reviewer_output
        except Exception as post_error:
            raise Exception(f"Failed to post review: {str(post_error)}")

    async def process_file_with_langfuse(
        self,
        diff: CodeDiff,
        filename: str,
        languages: List[str],
        user_input: str,
        agent: Agent[None, str],
        repository_service: RepositoryService,
        platform: str,
        repository: str,
    ) -> None:
        """Process a single file for code review with langfuse tracing.

        Args:
            diff: The code diff to review
            filename: The filename being reviewed
            languages: List of programming languages in the file
            user_input: The formatted user input for the agent
            agent: The AI agent to use for review
            repository_service: The repository service for posting comments
            platform: The platform identifier (github/gitlab)
            repository: The repository identifier

        """
        with self._langfuse.tracer.start_as_current_span(
            "CR-Agent-Review"
        ) as file_review_span:
            file_review_span.set_attribute(
                "langfuse.user.id", f"cr-request-{self._request_id}"
            )
            file_review_span.set_attribute(
                "langfuse.session.id", f"cr-{platform}-{repository}"
            )
            file_review_span.set_attribute("filename", filename)
            file_review_span.set_attribute("languages", languages)

            reviewer_output = await self.process_file_without_langfuse(
                diff, user_input, agent, repository_service
            )

            file_review_span.set_attribute("input.value", user_input)
            file_review_span.set_attribute("output.value", str(reviewer_output))

    async def process_file(
        self,
        diff: CodeDiff,
        filename: str,
        languages: List[str],
        user_input: str,
        agent: Agent[None, str],
        repository_service: RepositoryService,
        platform: str,
        repository: str,
    ) -> CodeReviewResponse:
        """Process a single file for code review.

        Args:
            diff: The code diff to review
            filename: The filename being reviewed
            languages: List of programming languages in the file
            user_input: The formatted user input for the agent
            agent: The AI agent to use for review
            repository_service: The repository service for posting comments
            platform: The platform identifier (github/gitlab)
            repository: The repository identifier

        Returns:
            The code review response from the agent

        """
        if self._langfuse.enabled:
            await self.process_file_with_langfuse(
                diff,
                filename,
                languages,
                user_input,
                agent,
                repository_service,
                platform,
                repository,
            )
            # Re-run without langfuse to get the return value
            return await self.process_file_without_langfuse(
                diff, user_input, agent, repository_service
            )
        else:
            return await self.process_file_without_langfuse(
                diff, user_input, agent, repository_service
            )
