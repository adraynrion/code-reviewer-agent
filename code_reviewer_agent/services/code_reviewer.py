import sys
import time
from typing import List

from pydantic_ai import Agent

from code_reviewer_agent.config.config import Config
from code_reviewer_agent.models.base_types import (
    CodeDiff,
    InstructionsPath,
    Platform,
    Repository,
    RequestId,
    Token,
    Url,
)
from code_reviewer_agent.models.pydantic_reviewer_models import CodeReviewResponse
from code_reviewer_agent.models.reviewer_agent import ReviewerAgent
from code_reviewer_agent.prompts.cr_agent import USER_PROMPT
from code_reviewer_agent.services.base_service import BaseService
from code_reviewer_agent.services.github import GitHubReviewerService
from code_reviewer_agent.services.gitlab import GitLabReviewerService
from code_reviewer_agent.utils.rich_utils import (
    console,
    print_debug,
    print_diff,
    print_error,
    print_exception,
    print_header,
    print_info,
    print_section,
    print_success,
    print_warning,
)


class CodeReviewService(BaseService):
    _repository_service: GitHubReviewerService | GitLabReviewerService

    def __init__(
        self,
        platform: Platform,
        repository: Repository,
        request_id: RequestId,
        instructions_path: InstructionsPath,
    ) -> None:
        super().__init__(Config())
        self._reviewer_agent = ReviewerAgent(self.config)

        reviewer_config = self.config.schema.reviewer
        self._github_token = Token(reviewer_config.github_token)
        self._gitlab_token = Token(reviewer_config.gitlab_token)
        self._gitlab_url = Url(reviewer_config.gitlab_api_url)
        self._platform = Platform(platform or reviewer_config.platform)
        self._repository = Repository(repository or reviewer_config.repository)
        self._instructions_path = InstructionsPath(
            instructions_path or reviewer_config.instruction_dir_path
        )
        self._request_id = RequestId(request_id)

        # Initialize with the correct service based on platform
        self.repository_service = self.platform

    @property
    def agent(self) -> Agent[None, str]:
        return self._reviewer_agent.agent

    @property
    def debug(self) -> bool:
        return self._reviewer_agent.debug

    @property
    def github_token(self) -> Token:
        return self._github_token

    @github_token.setter
    def github_token(self, value: str) -> None:
        self._github_token = Token(value)

    @property
    def gitlab_token(self) -> Token:
        return self._gitlab_token

    @gitlab_token.setter
    def gitlab_token(self, value: str) -> None:
        self._gitlab_token = Token(value)

    @property
    def gitlab_url(self) -> Url:
        return self._gitlab_url

    @gitlab_url.setter
    def gitlab_url(self, value: str) -> None:
        self._gitlab_url = Url(value)

    @property
    def platform(self) -> Platform:
        return self._platform

    @platform.setter
    def platform(self, value: Platform) -> None:
        formated_value = value.lower().strip()
        if formated_value not in ("github", "gitlab"):
            raise ValueError("Invalid platform. Must be either 'github' or 'gitlab'.")

        if formated_value == "github" and not self.github_token:
            raise ValueError(
                "github_token config variable is required when platform is 'github'."
            )

        if formated_value == "gitlab" and not self.gitlab_token:
            raise ValueError(
                "gitlab_token config variable is required when platform is 'gitlab'."
            )
        self._platform = Platform(formated_value)

    @property
    def repository(self) -> Repository:
        return self._repository

    @repository.setter
    def repository(self, value: str) -> None:
        self._repository = Repository(value)

    @property
    def instructions_path(self) -> InstructionsPath:
        return self._instructions_path

    @instructions_path.setter
    def instructions_path(self, value: str) -> None:
        self._instructions_path = InstructionsPath(value)

    @property
    def request_id(self) -> RequestId:
        return self._request_id

    @request_id.setter
    def request_id(self, value: int) -> None:
        self._request_id = RequestId(value)

    @property
    def repository_service(self) -> GitHubReviewerService | GitLabReviewerService:
        return self._repository_service

    @repository_service.setter
    def repository_service(self, platform: Platform) -> None:
        if platform == "github":
            self._repository_service = GitHubReviewerService(
                self.repository, self.request_id, self._config.schema.reviewer
            )
        elif platform == "gitlab":
            self._repository_service = GitLabReviewerService(
                self.repository, self.request_id, self._config.schema.reviewer
            )
        else:
            raise ValueError("Invalid platform. Must be either 'github' or 'gitlab'.")

    async def _file_code_review_without_langfuse(
        self, diff: CodeDiff, user_input: str
    ) -> CodeReviewResponse:
        start_time = time.perf_counter()
        reviewer_output: CodeReviewResponse

        try:
            reviewer_response = await self.agent.run(
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
            await self.repository_service.post_review_comments(diff, reviewer_output)
            return reviewer_output
        except Exception as post_error:
            raise Exception(f"Failed to post review: {str(post_error)}")

    async def _file_code_review(
        self, diff: CodeDiff, filename: str, languages: List[str], user_input: str
    ) -> None:
        with self.langfuse.tracer.start_as_current_span(
            "CR-Agent-Review"
        ) as file_review_span:
            file_review_span.set_attribute(
                "langfuse.user.id", f"cr-request-{self.request_id}"
            )
            file_review_span.set_attribute(
                "langfuse.session.id", f"cr-{self.platform}-{self.repository}"
            )
            file_review_span.set_attribute("filename", filename)
            file_review_span.set_attribute("languages", languages)

            reviewer_output = await self._file_code_review_without_langfuse(
                diff, user_input
            )

            file_review_span.set_attribute("input.value", user_input)
            file_review_span.set_attribute("output.value", str(reviewer_output))

    async def _review_files_without_langfuse(self) -> int:
        files_reviewed = 0
        for diff in self.repository_service.diffs:
            try:
                filename = diff.get("filename", "unknown")
                languages = diff.get("languages", ["unknown"])
                patch = diff.get("patch", "")

                if not patch:
                    print_warning(f"No changes found for file: {filename}")
                    continue

                if self.debug:
                    print_info(f"Reviewing file: {filename}")
                    print_info(f"  - Languages: {', '.join(languages)}")
                    print_diff(patch)

                # Prepare the User input for the code review
                user_input = USER_PROMPT.format(
                    diff=patch,
                )
                print_debug(f"User input length: {len(user_input)}")

                print_info(f"Starting code review for file: {filename}")

                if self.langfuse.enabled:
                    await self._file_code_review(
                        CodeDiff(**diff), filename, languages, user_input
                    )
                else:
                    await self._file_code_review_without_langfuse(
                        CodeDiff(**diff), user_input
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

    async def _review_files(self) -> None:
        with self.langfuse.tracer.start_as_current_span(
            "CR-Agent-Main-Trace"
        ) as main_span:
            main_span.set_attribute("langfuse.user.id", f"cr-request-{self.request_id}")
            main_span.set_attribute(
                "langfuse.session.id", f"cr-{self.platform}-{self.repository}"
            )

            files_reviewed = await self._review_files_without_langfuse()

            main_span.set_attribute("input.value", str(self.repository_service.diffs))
            main_span.set_attribute(
                "output.value",
                f"Reviewed {files_reviewed}/{len(self.repository_service.diffs)} files successfully",
            )

    async def main(self) -> None:
        console.clear()
        print_header("Starting Code Reviewer Agent process")

        if self.debug:
            print_section("[DEBUG] Final Configuration retrieved:", "⚙️")
            print_info(f"Platform: {self.platform.upper()}")
            print_info(f"Repository: {self.repository}")
            print_info(f"Instructions path: {self.instructions_path}")
            print_info(f"Request ID: {self.request_id}")

        try:
            self.repository_service.request_files_analysis_from_api()
        except Exception as e:
            print_error(
                f"Error fetching {'PR' if self.platform == 'github' else 'MR'} files diffs: {str(e)}"
            )
            print_exception()
            sys.exit(1)

        # ========== Reviewer Agent: loop on each file diff ==========
        print_section("Starting Code Review process", "🤖")
        print_debug(
            f"Reviewing {len(self.repository_service.diffs)} file(s) with changes"
        )

        try:
            if self.langfuse.enabled:
                await self._review_files()
            else:
                await self._review_files_without_langfuse()
        except Exception as e:
            print_error(f"An unexpected error occurred: {str(e)}")
            print_exception()
            sys.exit(1)

        print_section("Review Complete", "✅")
        print_success("Code review process finished successfully")
        sys.exit(0)
