import requests
from requests.exceptions import RequestException

from code_reviewer_agent.models.base_types import StringValidator
from code_reviewer_agent.models.pydantic_config_models import ReviewerConfig
from code_reviewer_agent.models.pydantic_reviewer_models import CodeReviewResponse
from code_reviewer_agent.services.repository import (
    CodeDiff,
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


class GitLabToken(StringValidator):
    pass


class GitLabApiUrl(StringValidator):
    pass


class GitLabReviewerService(RepositoryService):
    def __init__(
        self, repository: Repository, request_id: RequestId, config: ReviewerConfig
    ) -> None:
        RepositoryService.__init__(self, repository, request_id)
        self._gitlab_token = config.gitlab_token
        self._gitlab_api_url = config.gitlab_api_url

    @property
    def gitlab_token(self) -> GitLabToken:
        return self._gitlab_token

    @property
    def gitlab_api_url(self) -> GitLabApiUrl:
        return self._gitlab_api_url

    def request_files_analysis_from_api(self) -> None:
        # ===== Fetch the merge request metadata =====
        print_section("Fetching GitLab Merge Request files", "🌐")
        headers = {"Authorization": f"token {self.gitlab_token}"}
        try:
            print_info("Retrieving commits...")
            mr_metadata_url = f"{self.gitlab_api_url}/projects/{self.repository}/merge_requests/{self.request_id}"
            resp = requests.get(mr_metadata_url, headers=headers)
            if resp.status_code != 200:
                print_error(
                    f"Failed to fetch merge request commits: {resp.status_code} {resp.text}"
                )
                raise Exception("Failed to fetch merge request commits")
            mr_metadata = resp.json()
            self.last_commit_sha = mr_metadata["diff_refs"]
            print_success("Successfully retrieved merge request commits")

            print_info("Retrieving changed files...")
            url = f"{self.gitlab_api_url}/projects/{self.repository}/merge_requests/{self.request_id}/changes"
            resp = requests.get(url, headers=headers)
            if resp.status_code != 200:
                print_error(
                    f"Failed to fetch merge request files: {resp.status_code} {resp.text}"
                )
                raise Exception("Failed to fetch merge request files")
            files: Files = resp.json()
            if not files or len(files) == 0:
                raise ValueError("No files with changes found to review")
            print_success("Successfully retrieved merge request files")
            self.diffs = files
        except RequestException as e:
            raise Exception(
                f"Network error while fetching merge request data: {str(e)}"
            )
        except ValueError:
            raise
        except Exception as e:
            raise Exception(
                f"Unexpected error while fetching merge request data: {str(e)}"
            )

    async def post_review_comments(
        self, diff: CodeDiff, reviewer_output: CodeReviewResponse
    ) -> None:
        print_section(
            f"Posting to GitLab repo {self.repository} MR #{self.request_id}", "📝"
        )
        headers = {
            "Private-Token": self.gitlab_token,
            "Content-Type": "application/json",
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
            "position": {
                "base_sha": diff["sha"]["base_sha"],
                "start_sha": diff["sha"]["start_sha"],
                "head_sha": diff["sha"]["head_sha"],
                "position_type": "text",
                "new_path": diff["filename"],
                "new_line": reviewer_output.line_number,
            },
        }

        print_info("Posting review comment...")
        resp = requests.post(
            f"{self.gitlab_api_url}/projects/{self.repository}/merge_requests/{self.request_id}/discussions",
            headers=headers,
            json=data,
        )
        if resp.status_code != 201:
            raise Exception(
                f"Failed to post comment on repo {self.repository} MR #{self.request_id}: {resp.text}"
            )
        print_success("Successfully posted review comment!")

        self._assign_reviewed_label()

    def _assign_reviewed_label(self):
        # ===== Update MR with reviewed_label =====
        print_section(
            f"Updating MR #{self.request_id} of GitLab repo {self.repository}", "🏷️"
        )
        headers = {
            "Private-Token": self.gitlab_token,
            "Content-Type": "application/json",
        }

        print_info(f"Adding label '{self.reviewed_label}'...")
        # TODO: Retrieve existing label before POST (it replace every existing labels)

        label_url = f"{self.gitlab_api_url}/projects/{self.repository}/merge_requests/{self.request_id}?add_labels={self.reviewed_label}"
        resp = requests.put(label_url, headers=headers)
        if resp.status_code != 200:
            raise Exception(f"Failed to set label to MR: {resp.text}")
        print_success(f"Successfully set label on MR!")

        # ===== Set MR reviewer as the owner of the GITLAB_TOKEN =====
        print_info(f"Retrieving GITLAB_TOKEN owner...")
        user_url = f"{self.gitlab_api_url}/user"
        resp = requests.get(user_url, headers=headers)
        if resp.status_code != 200:
            raise Exception(
                f"Failed to get authenticated user: {resp.status_code} - {resp.text}"
            )

        user_data = resp.json()
        user_id = user_data.get("id")
        user_name = user_data.get("name", f"User {user_id}")
        if (
            not user_id
        ):  # Only check user_id as it is the only field required for the update request
            raise Exception(
                "Could not determine GITLAB_TOKEN owner. 'id' field missing in response."
            )

        print_info(f"Setting reviewer as {user_name} on MR...")
        review_url = (
            f"{self.gitlab_api_url}/projects/"
            f"{self.repository}/merge_requests/{self.request_id}"
            f"?reviewer_ids%5B%5D={user_id}"
        )
        resp = requests.put(review_url, headers=headers)
        if resp.status_code != 200:
            raise Exception(
                f"Failed to set reviewer on MR: {resp.status_code} - {resp.text}"
            )
        print_success(f"Successfully set reviewer on MR!")
