from abc import ABC, abstractmethod

from code_reviewer_agent.models.base_types import (
    CodeDiff,
    CommitSha,
    Files,
    FilesDiff,
    Label,
    Languages,
    Repository,
    RequestId,
)
from code_reviewer_agent.models.pydantic_reviewer_models import CodeReviewResponse
from code_reviewer_agent.utils.language_utils import FilesPath, LanguageUtils
from code_reviewer_agent.utils.rich_utils import (
    print_debug,
    print_info,
    print_section,
    print_success,
    print_warning,
)


class RepositoryService(ABC):
    def __init__(self, repository: Repository, request_id: RequestId) -> None:
        self._repository = repository
        self._request_id = request_id

    @property
    def repository(self) -> Repository:
        return self._repository

    @property
    def request_id(self) -> RequestId:
        return self._request_id

    @property
    def diffs(self) -> FilesDiff:
        return self._diffs

    @diffs.setter
    def diffs(self, files: Files) -> None:
        """Transform given Files to a Tuple of FilesDiff."""
        print_section("Processing files", "📄")
        filename_list = FilesPath(
            tuple(str(file.get("filename", "")) for file in files)
        )
        self.languages = LanguageUtils.get_file_languages(filename_list)

        print_info("Retrieving code diffs by file...")
        files_diff = []
        for file in files:
            filename: str = file.get("filename", "")
            patch: str = file.get("patch", "")
            if not self.languages.get(filename):
                print_warning(
                    f"Skipping file analysis {filename}: no languages detected"
                )
                continue

            diff = {
                "sha": self.last_commit_sha,
                "filename": filename,
                "languages": self.languages.get(filename),
                "patch": patch,
            }
            files_diff.append(diff)

            print_debug(f"Retrieved code diffs for file: {filename}")

        # Check if there are no files to review
        if not files_diff:
            raise ValueError("No languages detected for files to review")

        print_success("Successfully retrieved code diffs by file!")
        self._diffs = FilesDiff(tuple(files_diff))

    @property
    def languages(self) -> Languages:
        return self._languages

    @languages.setter
    def languages(self, value: Languages) -> None:
        self._languages = Languages(value)

    @property
    def last_commit_sha(self) -> CommitSha:
        return self._last_commit_sha

    @last_commit_sha.setter
    def last_commit_sha(self, sha: str) -> None:
        self._last_commit_sha = CommitSha(sha)

    @property
    def reviewed_label(self) -> Label:
        return Label("ReviewedByAI")

    @abstractmethod
    def request_files_analysis_from_api(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def post_review_comments(
        self, diff: CodeDiff, reviewer_output: CodeReviewResponse
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def _assign_reviewed_label(self) -> None:
        raise NotImplementedError
