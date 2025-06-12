from typing import Any, Dict, List

import requests

from code_reviewer_agent.config import config
from code_reviewer_agent.models.agent import CodeReviewResponse
from code_reviewer_agent.utils.file_utils import get_file_languages
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


def get_request_files(repository: str, pr_id: int) -> List[Dict[str, Any]]:
    """Fetch the pull request files from GitHub.

    Args:
        repository: The repository identifier as 'owner/repo'
        pr_id: The pull request ID

    Returns:
        List of pull request files

    Raises:
        Exception: If the pull request files cannot be fetched

    """
    print_header("GitHub Pull Request management process")

    # ===== Fetch the pull request metadata =====
    last_commit_sha = ""
    try:
        print_section("Connecting to GitHub repository", "🌐")

        print_info("Retrieving commits...")
        headers = {"Authorization": f"token {config.reviewer.github_token}"}
        pr_metadata_url = (
            f"https://api.github.com/repos/{repository}/pulls/{pr_id}/commits"
        )
        pr_metadata_response = requests.get(pr_metadata_url, headers=headers)
        pr_metadata = pr_metadata_response.json()
        if pr_metadata_response.status_code != 200:
            print_error(
                f"Failed to fetch pull request commits: {pr_metadata_response.status_code} {pr_metadata_response.text}"
            )
            raise Exception("Failed to fetch pull request commits")
        last_commit_sha = pr_metadata[-1]["sha"]
        print_success("Successfully retrieved pull request commits")

        print_info("Retrieving changed files...")
        url = f"https://api.github.com/repos/{repository}/pulls/{pr_id}/files"
        pr_files = requests.get(url, headers=headers)
        if pr_files.status_code != 200:
            print_error(
                f"Failed to fetch pull request files: {pr_files.status_code} {pr_files.text}"
            )
            raise Exception("Failed to fetch pull request files")
        print_success("Successfully retrieved pull request files")

    except requests.exceptions.RequestException as e:
        print_exception()
        raise Exception(f"Network error while fetching pull request data: {str(e)}")
    except Exception as e:
        print_exception()
        raise Exception(f"Unexpected error while fetching pull request data: {str(e)}")

    # ===== Process the changed files =====
    print_section("Processing retrieved files", "📄")
    files: List[Dict[str, Any]] = pr_files.json()
    filename_list: List[str] = [file["filename"] for file in files]
    languages_dict = get_file_languages(filename_list)

    # Process each file in the PR
    print_info("Retrieving diffs data by file...")
    files_diff: List[Dict[str, Any]] = []
    for file in files:
        filename = file["filename"]
        patch = file.get("patch", "")
        if not languages_dict.get(filename):
            print_warning(f"No languages detected for file: {filename}")
            continue

        diff = {
            "sha": last_commit_sha,
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


async def post_github_review(
    repository: str,
    pr_id: int,
    raw_diff: dict[str, Any],
    reviewer_output: CodeReviewResponse,
) -> None:
    """Post one review comment to given GitHub repo and PR."""
    print_section(f"Posting to GitHub repo {repository} PR #{pr_id}", "📝")
    headers = {
        "Authorization": f"token {config.reviewer.github_token}",
        "Accept": "application/vnd.github.v3+json",
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
        "commit_id": raw_diff["sha"],
        "path": raw_diff["filename"],
        "side": "RIGHT",
        "line": reviewer_output.line_number,
    }

    print_info("Posting review...")
    comment_response = requests.post(
        f"https://api.github.com/repos/{repository}/pulls/{pr_id}/comments",
        headers=headers,
        json=data,
    )

    if comment_response.status_code != 201:
        raise Exception(
            f"Failed to post comment on repo {repository} PR #{pr_id}: {comment_response.text}"
        )

    print_success("Successfully posted review comment!")


async def update_github_pr(
    repository: str,
    pr_id: int,
    reviewed_label: str,
) -> None:
    """Set owner of GITHUB_TOKEN as reviewer (if not the same as the Assignee of the PR)
    and 'reviewed_label' as label of given GitHub PR."""
    headers = {
        "Authorization": f"token {config.reviewer.github_token}",
        "Accept": "application/vnd.github.v3+json",
    }

    print_info(f"Adding label '{reviewed_label}' to PR #{pr_id}...")
    # TODO: Retrieve existing label before POST (it replace every existing labels)

    label_url = f"https://api.github.com/repos/{repository}/issues/{pr_id}/labels"
    label_data = {"labels": [reviewed_label]}
    label_response = requests.post(label_url, headers=headers, json=label_data)
    if label_response.status_code != 200:
        raise Exception(
            f"Failed to set label as '{reviewed_label}' to PR #{pr_id}: {label_response.text}"
        )
    print_success(f"Successfully set label as '{reviewed_label}' to PR #{pr_id}")

    # ===== Set PR reviewer as the owner of the GITHUB_TOKEN =====
    print_info(f"Retrieving GITHUB_TOKEN owner...")
    user_url = "https://api.github.com/user"
    user_response = requests.get(user_url, headers=headers)
    if user_response.status_code != 200:
        raise Exception(
            f"Failed to get authenticated user: {user_response.status_code} - {user_response.text}"
        )

    user_data = user_response.json()
    if "login" not in user_data:
        raise Exception(
            "Could not determine GITHUB_TOKEN owner. 'login' field missing in response."
        )

    token_owner = user_data["login"]
    print_info(f"Setting reviewer as {token_owner} on PR #{pr_id}...")
    review_url = (
        f"https://api.github.com/repos/{repository}/pulls/{pr_id}/requested_reviewers"
    )
    review_data = {"reviewers": [token_owner]}
    reviewer_response = requests.post(review_url, headers=headers, json=review_data)
    if reviewer_response.status_code != 201:
        raise Exception(
            f"Failed to set reviewer as {token_owner} on PR #{pr_id}: "
            f"{reviewer_response.status_code} - {reviewer_response.text}"
        )
    print_success(f"Successfully set reviewer as {token_owner} on PR #{pr_id}")
