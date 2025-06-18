import requests
from requests.exceptions import RequestException

from code_reviewer_agent.models.base_types import CodeDiff, GitHubToken
from code_reviewer_agent.models.pydantic_config_models import ReviewerConfig
from code_reviewer_agent.models.pydantic_reviewer_models import CodeReviewResponse
from code_reviewer_agent.services.repository import (
    Files,
    Repository,
    RepositoryService,
    RequestId,
)
from code_reviewer_agent.utils.rich_utils import (
    print_error,
    print_info,
    print_section,
    print_success,
)


class GitHubReviewerService(RepositoryService):
    def __init__(
        self, repository: Repository, request_id: RequestId, config: ReviewerConfig
    ) -> None:
        RepositoryService.__init__(self, repository, request_id)
        self._github_token = GitHubToken(config.github_token)

    @property
    def github_token(self) -> GitHubToken:
        return self._github_token

    def request_files_analysis_from_api(self) -> None:
        # ===== Fetch the pull request metadata =====
        print_section("Fetching GitHub Pull Request files", "🌐")
        headers = {"Authorization": f"token {self.github_token}"}
        try:
            print_info("Retrieving commits...")
            pr_metadata_url = f"https://api.github.com/repos/{self.repository}/pulls/{self.request_id}/commits"
            resp = requests.get(pr_metadata_url, headers=headers)
            if resp.status_code != 200:
                print_error(
                    f"Failed to fetch pull request commits: {resp.status_code} {resp.text}"
                )
                raise Exception("Failed to fetch pull request commits")
            pr_metadata = resp.json()
            self.last_commit_sha = pr_metadata[-1]["sha"]
            print_success("Successfully retrieved pull request commits")

            print_info("Retrieving changed files...")
            url = f"https://api.github.com/repos/{self.repository}/pulls/{self.request_id}/files"
            resp = requests.get(url, headers=headers)
            if resp.status_code != 200:
                print_error(
                    f"Failed to fetch pull request files: {resp.status_code} {resp.text}"
                )
                raise Exception("Failed to fetch pull request files")
            files: Files = resp.json()
            if not files or len(files) == 0:
                raise ValueError("No files with changes found to review")
            print_success("Successfully retrieved pull request files")
            self.diffs = files
        except RequestException as e:
            raise Exception(f"Network error while fetching pull request data: {str(e)}")
        except ValueError:
            raise
        except Exception as e:
            raise Exception(
                f"Unexpected error while fetching pull request data: {str(e)}"
            )

    async def post_review_comments(
        self, diff: CodeDiff, reviewer_output: CodeReviewResponse
    ) -> None:
        print_section(
            f"Posting to GitHub repo {self.repository} PR #{self.request_id}", "📝"
        )
        headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json",
        }

        print_info("Building Markdown review comment...")
        code_diff = reviewer_output.code_diff
        if not code_diff.startswith("```diff"):
            code_diff = "```diff\n" + code_diff + "\n```"
        body = (
            f"### {reviewer_output.title}\n"
            f"**Line {reviewer_output.line_number}**\n\n"
            f"{reviewer_output.comment}\n\n"
            f"{code_diff}"
        )

        data = {
            "body": body,
            "commit_id": diff["sha"],
            "path": diff["filename"],
            "side": "RIGHT",
            "line": reviewer_output.line_number,
        }

        print_info("Posting review comment...")
        resp = requests.post(
            f"https://api.github.com/repos/{self.repository}/pulls/{self.request_id}/comments",
            headers=headers,
            json=data,
        )
        if resp.status_code != 201:
            raise Exception(
                f"Failed to post comment on repo {self.repository} PR #{self.request_id}: {resp.text}"
            )
        print_success("Successfully posted review comment!")

        await self._assign_reviewed_label()

    async def _assign_reviewed_label(self) -> None:
        # ===== Update PR with reviewed_label =====
        print_section(
            f"Updating PR #{self.request_id} of GitHub repo {self.repository}", "🏷️"
        )
        headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json",
        }

        print_info(f"Adding label '{self.reviewed_label}'...")
        # TODO: Retrieve existing label before POST (it replace every existing labels)

        label_url = f"https://api.github.com/repos/{self.repository}/issues/{self.request_id}/labels"
        label_data = {"labels": [self.reviewed_label]}
        resp = requests.post(label_url, headers=headers, json=label_data)
        if resp.status_code != 200:
            raise Exception(f"Failed to set label to PR: {resp.text}")
        print_success(f"Successfully set label on PR!")

        # ===== Set PR reviewer as the owner of the GITHUB_TOKEN =====
        print_info(f"Retrieving GITHUB_TOKEN owner...")
        user_url = "https://api.github.com/user"
        resp = requests.get(user_url, headers=headers)
        if resp.status_code != 200:
            raise Exception(
                f"Failed to get authenticated user: {resp.status_code} - {resp.text}"
            )
        user_data = resp.json()
        if "login" not in user_data:
            raise Exception(
                "Could not determine GITHUB_TOKEN owner. 'login' field missing in response."
            )

        token_owner = user_data["login"]
        print_info(f"Setting reviewer as {token_owner} on PR...")
        review_url = f"https://api.github.com/repos/{self.repository}/pulls/{self.request_id}/requested_reviewers"
        review_data = {"reviewers": [token_owner]}
        resp = requests.post(review_url, headers=headers, json=review_data)
        if resp.status_code != 201:
            raise Exception(
                f"Failed to set reviewer on PR: {resp.status_code} - {resp.text}"
            )
        print_success(f"Successfully set reviewer on PR!")
