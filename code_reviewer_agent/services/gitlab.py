from typing import Any, Dict, List

import requests

from code_reviewer_agent.models.agent import CodeReviewResponse
from code_reviewer_agent.utils.config import config
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

from ..utils.file_utils import get_file_languages


def get_request_files(repository: str, mr_id: int) -> List[Dict[str, Any]]:
    """Fetch the merge request files from GitLab.

    Args:
        repository: The repository identifier as 'project_id'
        mr_id: The merge request ID

    Returns:
        List of merge request files

    Raises:
        Exception: If the merge request files cannot be fetched

    """
    print_header("GitLab Merge Request management process")

    # ===== Fetch the merge request metadata =====
    last_commit_sha_metadata: Dict[str, Any] = {}
    try:
        print_section("Connecting to GitLab repository", "🌐")

        print_info("Retrieving commits...")
        headers = {"Private-Token": f"{config.GITLAB_TOKEN}"}
        mr_metadata_url = f"{config.GITLAB_API_URL}/projects/{repository.replace('/', '%2F')}/merge_requests/{mr_id}"
        mr_metadata_response = requests.get(mr_metadata_url, headers=headers)
        mr_metadata = mr_metadata_response.json()
        if mr_metadata_response.status_code != 200:
            print_error(
                f"Failed to fetch merge request metadata: {mr_metadata_response.status_code} {mr_metadata_response.text}"
            )
            raise Exception("Failed to fetch merge request metadata")
        last_commit_sha_metadata = mr_metadata["diff_refs"]
        print_success("Successfully retrieved merge request commits")

        print_info("Retrieving changed files...")
        url = f"{config.GITLAB_API_URL}/projects/{repository.replace('/', '%2F')}/merge_requests/{mr_id}/changes"
        mr_files = requests.get(url, headers=headers)
        if mr_files.status_code != 200:
            print_error(
                f"Failed to fetch merge request files: {mr_files.status_code} {mr_files.text}"
            )
            raise Exception("Failed to fetch merge request files")
        print_success("Successfully retrieved merge request files")

    except requests.exceptions.RequestException as e:
        print_exception()
        raise Exception(f"Network error while fetching merge request data: {str(e)}")
    except Exception as e:
        print_exception()
        raise Exception(f"Unexpected error while fetching merge request data: {str(e)}")

    # ===== Process the changed files =====
    print_section("Processing retrieved files", "📄")
    files: List[Dict[str, Any]] = mr_files.json()
    filename_list: List[str] = [file["filename"] for file in files]
    languages_dict = get_file_languages(filename_list)

    # Process each file in the MR
    print_info("Retrieving diffs data by file...")
    files_diff: List[Dict[str, Any]] = []
    for file in files:
        filename = file["filename"]
        patch = file.get("diff", "")
        if not languages_dict.get(filename):
            print_warning(f"No languages detected for file: {filename}")
            continue

        diff = {
            "sha": last_commit_sha_metadata,
            "filename": filename,
            "languages": languages_dict.get(filename),
            "patch": patch,
        }
        files_diff.append(diff)

        print_debug(
            f"Retrieved diff data for file: {filename} ({len(patch)} characters)"
        )

    # Check if there are no files to review
    if not files_diff:
        raise Exception("No files with changes found to review")

    print_success("Successfully retrieved diffs data by file")
    return files_diff


async def post_gitlab_review(
    repository: str,
    mr_id: int,
    raw_diff: dict[str, Any],
    reviewer_output: CodeReviewResponse,
) -> None:
    """Post one review comment to given GitLab repo and MR."""
    print_section(f"Posting to GitLab repo {repository} MR #{mr_id}", "📝")
    headers = {
        "Private-Token": config.GITLAB_TOKEN,
        "Content-Type": "application/json",
    }

    print_info("Preparing review comments...")
    body = (
        f"### {reviewer_output.title}\n"
        f"**Line {reviewer_output.line_number}**\n\n"
        f"{reviewer_output.comment}\n\n"
    )

    code_diff = reviewer_output.code_diff
    # Format code diff if needed
    if not code_diff.startswith("```diff"):
        code_diff = "```diff\n" + code_diff + "\n```\n\n"

    data = {
        "body": body,
        "position": {
            "base_sha": raw_diff["sha"]["base_sha"],
            "start_sha": raw_diff["sha"]["start_sha"],
            "head_sha": raw_diff["sha"]["head_sha"],
            "position_type": "text",
            "new_path": raw_diff["filename"],
            "new_line": reviewer_output.line_number,
        },
    }

    print_info("Posting review...")
    comment_response = requests.post(
        f"{config.GITLAB_API_URL}/projects/{repository}/merge_requests/{mr_id}/discussions",
        headers=headers,
        json=data,
    )

    if comment_response.status_code != 201:
        raise Exception(
            f"Failed to post comment on repo #{repository} MR #{mr_id}: {comment_response.text}"
        )

    print_success("Successfully posted review comment!")


async def update_gitlab_mr(
    repository: str,
    mr_id: int,
    reviewed_label: str,
) -> None:
    """Set owner of GITLAB_TOKEN as reviewer (if not the same as the Assignee of the MR)
    and 'reviewed_label' as label of given GitLab MR."""
    headers = {
        "Private-Token": config.GITLAB_TOKEN,
        "Content-Type": "application/json",
    }

    print_info(f"Adding label '{reviewed_label}' to MR #{mr_id}...")
    # TODO: Retrieve existing label before POST (it replace every existing labels)

    label_url = f"{config.GITLAB_API_URL}/projects/{repository}/merge_requests/{mr_id}?add_labels={reviewed_label}"
    label_response = requests.put(label_url, headers=headers)
    if label_response.status_code != 200:
        raise Exception(
            f"Failed to set label as '{reviewed_label}' to MR #{mr_id}: {label_response.status_code} - {label_response.text}"
        )
    print_success(f"Successfully set label as '{reviewed_label}' to MR #{mr_id}")

    # ===== Set MR reviewer as the owner of the GITLAB_TOKEN =====
    print_info(f"Retrieving GITLAB_TOKEN owner...")
    user_resp = requests.get(f"{config.GITLAB_API_URL}/user", headers=headers)
    if user_resp.status_code != 200:
        raise Exception(
            f"Failed to get current user: {user_resp.status_code} - {user_resp.text}"
        )

    user_data = user_resp.json()
    reviewer_id = user_data.get("id")
    reviewer_name = user_data.get("name", f"User {reviewer_id}")
    if not reviewer_id:
        raise Exception("Could not determine reviewer ID from user data")

    print_info(f"Setting reviewer as {reviewer_name} on MR #{mr_id}...")
    reviewer_url = (
        f"{config.GITLAB_API_URL}/projects/"
        f"{repository.replace('/', '%2F')}/merge_requests/{mr_id}"
        f"?reviewer_ids%5B%5D={reviewer_id}"
    )
    reviewer_response = requests.put(reviewer_url, headers=headers)
    if reviewer_response.status_code != 200:
        raise Exception(
            f"Failed to assign reviewer to MR #{mr_id}: {reviewer_response.status_code} - {reviewer_response.text}"
        )
    print_success(f"Successfully assigned {reviewer_name} as reviewer to MR #{mr_id}")
