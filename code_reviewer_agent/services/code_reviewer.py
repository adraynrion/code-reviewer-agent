"""Code review service for the code review agent."""

import argparse
import asyncio
import json
import os
import time
from typing import Any, Dict, List

import requests
from dotenv import load_dotenv
from openai import OpenAI
from pydantic_ai import Agent

from ..models.agent import get_embedding_model_str, get_model, get_supabase
from ..prompts.agent import MAIN_USER_PROMPT, REVIEW_PROMPT
from ..utils.file_utils import get_file_languages
from ..utils.langfuse import configure_langfuse

# Load environment variables
load_dotenv()

# Configure Langfuse for agent observability
tracer = configure_langfuse()
local_instructions_dir = os.getenv("LOCAL_FILE_DIR", "")
supabase_client = get_supabase()
openai_client = OpenAI()


async def search_documents(
    query: str, match_threshold: float = 0.8
) -> List[Dict[str, Any]]:
    """Search for documents similar to the query using embeddings.

    Args:
        query: The search query string
        match_threshold: Similarity threshold for document matching (0-1)

    Returns:
        List of matching documents with their metadata

    Raises:
        ValueError: If the response from Supabase is not in the expected format

    """
    embeddings_response = openai_client.embeddings.create(
        input=query, model=get_embedding_model_str()
    )
    embedding = embeddings_response.data[0].embedding
    response = supabase_client.rpc(
        "match_documents",
        {"query_embedding": embedding, "match_threshold": match_threshold},
    ).execute()

    if not hasattr(response, "data") or not isinstance(response.data, list):
        raise ValueError("Unexpected response format from Supabase")

    # Ensure each item in the list is a dictionary
    return [dict(item) for item in response.data]


# Create the code reviewer agent
reviewer_agent = Agent(
    get_model(), system_prompt=REVIEW_PROMPT, tools=[search_documents], instrument=True
)


async def review_code(code_diff: str) -> str:
    """Review the provided code diff and return feedback.

    Args:
        code_diff: The code diff to review

    Returns:
        String containing the review feedback

    """
    prompt = REVIEW_PROMPT.format(code_diff=code_diff)

    try:
        response = await reviewer_agent.run(prompt)
        # Ensure we return a string by converting the response content
        response_content = getattr(response, "content", None)
        if isinstance(response_content, str):
            return response_content
        return (
            str(response_content)
            if response_content is not None
            else "No review content available"
        )
    except Exception as e:
        return f"Error generating review: {str(e)}"


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Code Review Agent")
    parser.add_argument(
        "--platform",
        type=str,
        choices=["github", "gitlab"],
        help="Platform: github or gitlab (overrides PLATFORM env var)",
    )
    parser.add_argument(
        "--repository",
        type=str,
        help="Repository in format owner/repo for GitHub and project_id for GitLab (overrides REPOSITORY env var)",
    )
    parser.add_argument(
        "--pr-id", type=int, required=True, help="Pull/Merge Request ID to review"
    )
    parser.add_argument(
        "--instructions-path",
        type=str,
        default=os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "instructions"
        ),
        help="Path to custom review instructions folder (default: package/instructions)",
    )
    return parser.parse_args()


async def main() -> int:
    """Main entry point for the code review agent."""
    args = parse_arguments()

    platform: str = args.platform or os.getenv("PLATFORM", "")
    repository: str = args.repository or os.getenv("REPOSITORY", "")
    pr_id: int = args.pr_id
    instructions_path: str = args.instructions_path
    reviewed_label: str = "ReviewedByAI"

    print(
        (
            f"Starting code review for {platform.upper()} PR/MR #{pr_id} in {repository}.",
            f"Instructions path: {instructions_path}.",
        )
    )

    # Validate inputs
    if platform not in ("github", "gitlab"):
        print("Invalid platform. Must be either 'github' or 'gitlab'")
        return 1

    if platform == "github" and not os.getenv("GITHUB_TOKEN", ""):
        print("GITHUB_TOKEN environment variable is required when platform is 'github'")
        return 1

    if platform == "gitlab" and not os.getenv("GITLAB_TOKEN", ""):
        print("GITLAB_TOKEN environment variable is required when platform is 'gitlab'")
        return 1

    if not repository:
        print(
            "Repository not specified. Use --repository or set REPOSITORY environment variable"
        )
        return 1

    # Fetch pull/merge request files
    repository_deps = {}
    if platform == "github":
        GITHUB_PERSONAL_ACCESS_TOKEN = os.getenv("GITHUB_TOKEN", "")
        headers = {"Authorization": f"token {GITHUB_PERSONAL_ACCESS_TOKEN}"}
        pr_metadata_url = (
            f"https://api.github.com/repos/{repository}/pulls/{pr_id}/commits"
        )
        pr_metadata_response = requests.get(pr_metadata_url, headers=headers)
        pr_metadata = pr_metadata_response.json()
        if pr_metadata_response.status_code != 200:
            print(
                f"\033[91mFailed to fetch pull request commits: {pr_metadata_response.status_code} {pr_metadata_response.text}\033[0m"
            )
            return 1
        url = f"https://api.github.com/repos/{repository}/pulls/{pr_id}/files"
        repository_deps = {
            "GITHUB_PERSONAL_ACCESS_TOKEN": GITHUB_PERSONAL_ACCESS_TOKEN,
            "PR_SHA": pr_metadata[-1]["sha"],
        }
    elif platform == "gitlab":
        GITLAB_PERSONAL_ACCESS_TOKEN = os.getenv("GITLAB_TOKEN", "")
        GITLAB_API_URL = os.getenv("GITLAB_API_URL", "https://gitlab.com/api/v4")
        headers = {"Private-Token": f"{GITLAB_PERSONAL_ACCESS_TOKEN}"}
        mr_metadata_url = (
            f"{GITLAB_API_URL}/projects/{repository}/merge_requests/{pr_id}"
        )
        mr_metadata_response = requests.get(mr_metadata_url, headers=headers)
        mr_metadata = mr_metadata_response.json()
        if mr_metadata_response.status_code != 200:
            print(
                f"\033[91m[ERROR] Failed to fetch merge request metadata: {mr_metadata_response.status_code} {mr_metadata_response.text}\033[0m"
            )
            return 1
        url = f"{GITLAB_API_URL}/projects/{repository}/merge_requests/{pr_id}/changes"
        repository_deps = {
            "GITLAB_PERSONAL_ACCESS_TOKEN": GITLAB_PERSONAL_ACCESS_TOKEN,
            "GITLAB_API_URL": GITLAB_API_URL,
            "MR_SHA_METADATA": mr_metadata["diff_refs"],
        }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(
            f"\033[91mFailed to fetch pull request files: {response.status_code} {response.text}\033[0m"
        )
        return 1

    pull_request_files = response.json()
    files = (
        pull_request_files
        if platform == "github"
        else pull_request_files.get("changes", [])
    )

    # Process each file in the PR/MR
    user_messages = []
    print(f"\033[94mRetrieving diff from {platform.upper()}:\033[0m")
    for file in files:
        filename = file["filename"] if platform == "github" else file["new_path"]
        languages_dict = get_file_languages(filename)
        languages_list = list(languages_dict.keys()) if languages_dict else ["unknown"]
        diff = {
            "filename": filename,
            "languages": languages_list,
            "patch": "",
        }

        patch = file.get("patch" if platform == "github" else "diff", "")
        if platform == "github":
            diff["sha"] = repository_deps["PR_SHA"]
        elif platform == "gitlab":
            diff["sha_metadata"] = repository_deps["MR_SHA_METADATA"]

        if patch:
            safe_patch = patch.replace("```", "''")
            diff["patch"] = f"```diff\n{safe_patch}\n```"
            user_messages.append(diff)
            print(f"  - {filename} ({len(patch)} bytes)")

    # Process the files and generate reviews
    if not user_messages:
        print("No files found to review")
        return 0

    # ========== Retrieving filesystem instructions ==========
    try:
        print(
            f"\n\033[94mRetrieving filesystem instructions at {local_instructions_dir}...\033[0m"
        )
        # List all files in the instructions directory using direct filesystem access
        instructions_files = [
            f
            for f in os.listdir(local_instructions_dir)
            if os.path.isfile(os.path.join(local_instructions_dir, f))
        ]
        filesystem_instructions = []
        for file in instructions_files:
            file_path = os.path.join(local_instructions_dir, file)
            with open(file_path, "r", encoding="utf-8") as f:
                filesystem_instructions.append(f.read())
        print(
            f"\033[92mRetrieved {len(instructions_files)} instructions file(s):\033[0m"
        )
        for file in instructions_files:
            print(f"\033[92m- {file}\033[0m")
    except Exception as e:
        print(
            f"\n\033[91m[Retrieving filesystem instructions error] An error occurred: {str(e)}\033[0m"
        )
        return 1

    # ========== Reviewer Agent: loop on each file diff ==========
    try:
        with tracer.start_as_current_span("CR-Agent-Main-Trace") as main_span:
            main_span.set_attribute("langfuse.user.id", f"pr-{pr_id}")
            main_span.set_attribute("langfuse.session.id", repository)

            for user_message_item in user_messages:
                user_message: dict[str, Any] = (
                    user_message_item  # Ensure type is properly hinted
                )
                with tracer.start_as_current_span(
                    "CR-Agent-Review"
                ) as file_review_span:
                    file_review_span.set_attribute("langfuse.user.id", f"pr-{pr_id}")
                    file_review_span.set_attribute("langfuse.session.id", repository)

                    # Generate user input for the code review
                    filename = user_message.get("filename", "unknown")
                    languages = ", ".join(user_message.get("languages", ["unknown"]))
                    patch = user_message.get("patch", "")
                    diff_content = (
                        f"# Filename: {filename}\n# Languages: {languages}\n{patch}\n"
                    )
                    print(
                        f"\n\033[95mStarting CR by AI Agent of the following diff:\n{diff_content}\033[0m"
                    )
                    user_input = MAIN_USER_PROMPT.format(
                        custom_instructions="\n\n".join(filesystem_instructions),
                        diff=diff_content,
                    )

                    # Allow the AI Agent to retry up to 3 times if it fails to format the output correctly
                    i = 1
                    retry_limit = 3
                    succeeded = False
                    suffix_user_instructions = "\n\n**Your output is not in the correct JSON format!** Please try again."
                    safe_cr_agent_output = ""

                    while i <= retry_limit:
                        try:
                            # Run the code review AI Agent
                            start_time = time.perf_counter()
                            reviewer_output = await reviewer_agent.run(
                                f"{user_input}{suffix_user_instructions if i > 1 else ''}"
                            )
                            duration = time.perf_counter() - start_time
                            print(
                                f"\033[93mCR AI Agent took ⏱️ {duration:.3f} seconds to review the file diff.\033[0m"
                            )

                            # Parse the output of the code review AI Agent
                            safe_cr_agent_output = (
                                reviewer_output.output.replace("\r", "")
                                .replace("\n", "")
                                .replace("\t", "")
                            )
                            reviewer_output_json = json.loads(safe_cr_agent_output)

                            if not isinstance(reviewer_output_json, list):
                                raise ValueError("Output is not a list of objects")
                            for idx, item in enumerate(reviewer_output_json):
                                if not isinstance(item, dict):
                                    raise ValueError(
                                        f"Item at index {idx} in output is not a dictionary"
                                    )
                                for key in [
                                    "line_number",
                                    "code_diff",
                                    "comments",
                                    "title",
                                ]:
                                    if key not in item:
                                        raise ValueError(
                                            f"Item at index {idx} is missing required key: {key}"
                                        )
                                if len(item) > 4:
                                    raise ValueError(
                                        f"Item at index {idx} has more keys than expected"
                                    )

                            succeeded = True
                            print(
                                "\033[92mSuccessfully parsed JSON output from CR AI Agent! Metadata are:\033[0m"
                            )
                            print(
                                "\033[96m"
                                + json.dumps(reviewer_output_json, indent=2)
                                + "\033[0m"
                            )
                            break

                        except (json.JSONDecodeError, ValueError) as e:
                            print(
                                f"\033[91m[Error] Failed to validate output from CR AI Agent: {str(e)}. Attempt #{i} output:\n{safe_cr_agent_output}\033[0m"
                            )
                            suffix_user_instructions += f" Failed to validate output from your attempt #{i}! Error log: {str(e)}."
                            i += 1

                    # Set attributes before potential loop "continue"
                    file_review_span.set_attribute("input.value", user_input)
                    file_review_span.set_attribute("output.value", safe_cr_agent_output)

                    if not succeeded:
                        print(
                            f"\n\033[95m[Critical] Failed to parse JSON output from CR AI Agent after {retry_limit} attempts! Skipping this file diff.\n\033[0m"
                        )
                        continue

                    # Post review comments to the PR/MR
                    if platform == "github":
                        await post_github_review(
                            repository,
                            pr_id,
                            user_message,
                            reviewer_output_json,
                            repository_deps,
                        )
                    elif platform == "gitlab":
                        await post_gitlab_review(
                            repository,
                            pr_id,
                            user_message,
                            reviewer_output_json,
                            repository_deps,
                        )

            # Add label and assign reviewer after processing all files
            if platform == "github":
                await add_github_reviewer(repository, pr_id, headers, reviewed_label)
            elif platform == "gitlab":
                await add_gitlab_reviewer(
                    repository, pr_id, headers, reviewed_label, repository_deps
                )

    except Exception as e:
        print(f"\n\033[91m[Error] An error occurred: {str(e)}\n\033[0m")
        import traceback

        traceback.print_exc()
        return 1

    return 0


async def post_github_review(
    repository: str,
    pr_id: int,
    user_message: dict,
    reviewer_output_json: list,
    repository_deps: dict,
) -> None:
    """Post review comments to a GitHub PR."""
    print(
        f"\n\033[94mPosting {len(reviewer_output_json)} comment(s) on the PR...\033[0m"
    )
    headers = {
        "Authorization": f"Bearer {repository_deps['GITHUB_PERSONAL_ACCESS_TOKEN']}",
        "Accept": "application/vnd.github.v3+json",
    }

    # Create one comment with all review feedback
    body = "# Code reviewer AI Agent comments\n\n"
    for cr_comment in reviewer_output_json:
        body += f"## {cr_comment.get('title', 'Comment')}\n\n"
        body += (
            cr_comment.get("comments", "")
            + "\n\n```diff\n"
            + cr_comment.get("code_diff", "")
            + "\n```\n\n"
        )

    data = {
        "body": body,
        "commit_id": user_message["sha"],
        "path": user_message["filename"],
        "side": "RIGHT",
        "line": reviewer_output_json[0].get(
            "line_number", 1
        ),  # Use first comment's line number or default to 1
    }

    response = requests.post(
        f"https://api.github.com/repos/{repository}/pulls/{pr_id}/comments",
        headers=headers,
        json=data,
    )
    if response.status_code != 201:
        print(
            f"\033[91m[Error] Failed to post a new comment on the PR #{pr_id}: {response.text}\n\033[0m"
        )
    else:
        print(f"\033[92mComment(s) posted on the PR #{pr_id}!\033[0m")


async def post_gitlab_review(
    repository: str,
    mr_id: int,
    user_message: dict,
    reviewer_output_json: list,
    repository_deps: dict,
) -> None:
    """Post review comments to a GitLab MR."""
    print("\n\033[94mPosting comment result on the MR...\033[0m")
    headers = {
        "Private-Token": repository_deps["GITLAB_PERSONAL_ACCESS_TOKEN"],
        "Content-Type": "application/json",
    }

    for cr_comment in reviewer_output_json:
        body = (
            cr_comment.get("comments", "")
            + "\n\n```diff\n"
            + cr_comment.get("code_diff", "")
            + "\n```\n\n"
        )
        data = {
            "body": body,
            "position": {
                "position_type": "text",
                "base_sha": user_message["sha_metadata"]["base_sha"],
                "start_sha": user_message["sha_metadata"]["start_sha"],
                "head_sha": user_message["sha_metadata"]["head_sha"],
                "new_path": user_message["filename"],
                "new_line": cr_comment.get("line_number", 1),
            },
        }

        response = requests.post(
            f"{repository_deps['GITLAB_API_URL']}/projects/{repository}/merge_requests/{mr_id}/discussions",
            headers=headers,
            json=data,
        )
        if response.status_code != 201:
            print(
                f"\033[91m[Error] Failed to post a new comment on the MR #{mr_id}: {response.text}\n\033[0m"
            )
        else:
            print(f"\033[92mComment(s) posted on the MR #{mr_id}!\033[0m")


async def add_github_reviewer(
    repository: str, pr_id: int, headers: dict, reviewed_label: str
) -> None:
    """Add reviewer and label to a GitHub PR."""
    # Add the "reviewed_label" label to the PR
    response = requests.post(
        f"https://api.github.com/repos/{repository}/issues/{pr_id}/labels",
        headers=headers,
        json=[{"name": reviewed_label}],
    )
    if response.status_code != 200:
        print(f"\n\033[91m[Error] Failed to add label: {response.text}\n\033[0m")
    else:
        print(f"\n\033[95mLabel '{reviewed_label}' added to PR #{pr_id}!\033[0m")

    # Get the username of the authenticated user and assign as reviewer
    user_resp = requests.get("https://api.github.com/user", headers=headers)
    if user_resp.status_code != 200:
        print(f"\n\033[91m[Error] Failed to get username: {user_resp.text}\n\033[0m")
    else:
        reviewer = user_resp.json()["login"]
        print(
            f"\n\033[93mUsername '{reviewer}' retrieved! Assigning reviewer on the PR...\033[0m"
        )
        response = requests.post(
            f"https://api.github.com/repos/{repository}/pulls/{pr_id}/requested_reviewers",
            headers=headers,
            json={"reviewers": [reviewer]},
        )
        if response.status_code != 200:
            print(f"\033[91m[Error] Failed to assign PR: {response.text}\n\033[0m")
        else:
            print(f"\033[95mReviewer {reviewer} set for PR #{pr_id}!\033[0m")


async def add_gitlab_reviewer(
    repository: str,
    mr_id: int,
    headers: dict,
    reviewed_label: str,
    repository_deps: dict,
) -> None:
    """Add reviewer and label to a GitLab MR."""
    # Add the "reviewed_label" label to the MR
    response = requests.put(
        f"{repository_deps['GITLAB_API_URL']}/projects/{repository}/merge_requests/{mr_id}",
        headers=headers,
        json={"labels": reviewed_label},
    )
    if response.status_code != 200:
        print(f"\033[91m[Error] Failed to add label: {response.text}\n\033[0m")
    else:
        print(f"\n\033[95mLabel '{reviewed_label}' added to MR #{mr_id}!\033[0m")

    # Get the username of the authenticated user and assign as reviewer
    user_resp = requests.get(
        f"{repository_deps['GITLAB_API_URL']}/user", headers=headers
    )
    if user_resp.status_code != 200:
        print(f"\n\033[91m[Error] Failed to get username: {user_resp.text}\n\033[0m")
    else:
        reviewer_id = user_resp.json()["id"]
        reviewer_username = user_resp.json()["username"]
        print(
            f"\n\033[93mUsername '{reviewer_username}' retrieved! Assigning reviewer on the MR...\033[0m"
        )
        response = requests.put(
            f"{repository_deps['GITLAB_API_URL']}/projects/{repository}/merge_requests/{mr_id}",
            headers=headers,
            json={"reviewer_ids": [reviewer_id]},
        )
        if response.status_code != 200:
            print(f"\033[91m[Error] Failed to assign MR: {response.text}\n\033[0m")
        else:
            print(f"\033[95mReviewer {reviewer_username} set for MR #{mr_id}!\033[0m")


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code if isinstance(exit_code, int) else 0)
