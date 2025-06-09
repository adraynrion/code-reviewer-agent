"""Code review service for the code review agent."""

import argparse
import asyncio
import json
import os
import sys
import time
from typing import Any, Dict, List

import requests
from dotenv import load_dotenv
from openai import OpenAI
from pydantic_ai import Agent

from ..models.agent import get_embedding_model_str, get_model, get_supabase
from ..prompts.agent import MAIN_USER_PROMPT, REVIEW_PROMPT
from ..utils import (
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
from ..utils.config import config
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
    try:
        print_debug(f"Generating embeddings for query: {query[:100]}...")
        embeddings_response = openai_client.embeddings.create(
            input=query, model=get_embedding_model_str()
        )
        embedding = embeddings_response.data[0].embedding

        print_debug(f"Searching documents with threshold: {match_threshold}")
        response = supabase_client.rpc(
            "match_documents",
            {"query_embedding": embedding, "match_threshold": match_threshold},
        ).execute()

        if not hasattr(response, "data"):
            print_error("Unexpected response format from Supabase")
            raise ValueError("Unexpected response format from Supabase")

        results = [dict(item) for item in response.data]
        print_success(f"Found {len(results)} matching document(s)")

        if results and config.DEBUG:  # Only show debug info if debug is enabled
            print_debug("Top match:")
            print_debug(f"  Content: {results[0].get('content', '')[:200]}...")
            print_debug(f"  Similarity: {results[0].get('similarity', 0):.4f}")

        return results

    except Exception as e:
        print_error(f"Error searching documents: {str(e)}")
        print_exception()
        raise


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
    print_section("Starting Code Review", "🔍")
    print_info("Preparing review prompt...")
    prompt = REVIEW_PROMPT.format(code_diff=code_diff)

    try:
        print_info("Sending request to reviewer agent...")
        start_time = time.perf_counter()

        response = await reviewer_agent.run(prompt)

        duration = time.perf_counter() - start_time
        print_success(f"Review completed in {duration:.2f} seconds")

        response_content = getattr(response, "content", None)
        if isinstance(response_content, str):
            return response_content

        # Handle different response formats
        result = (
            str(response_content)
            if response_content is not None
            else "No review content available"
        )
        if not result.strip():
            print_warning("Received empty review content")
            result = "No issues found or no review content was generated."

        return result

    except Exception as e:
        error_msg = f"Error generating review: {str(e)}"
        print_error(error_msg)
        print_exception()
        return error_msg


def parse_arguments() -> argparse.Namespace:
    """Parse and validate command line arguments.

    Returns:
        Parsed command line arguments

    """
    print_section("Parsing Command Line Arguments", "🔧")

    # Create the argument parser with rich help formatting
    parser = argparse.ArgumentParser(
        description="[bold]Code Review Agent[/bold] - Automated code review tool for GitHub and GitLab",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "[bold]Examples:[/bold]\n"
            "  python -m code_reviewer_agent --platform github --repository owner/repo --pr-id 123\n"
            "  python -m code_reviewer_agent --platform gitlab --repository 12345 --pr-id 42 --instructions-path ./docs"
        ),
    )

    # Platform argument
    parser.add_argument(
        "--platform",
        type=str,
        choices=["github", "gitlab"],
        help="Version control platform (overrides PLATFORM env var)",
        metavar="PLATFORM",
    )

    # Repository argument
    parser.add_argument(
        "--repository",
        type=str,
        help=(
            "Repository identifier. For GitHub: 'owner/repo' format. "
            "For GitLab: project ID (overrides REPOSITORY env var)"
        ),
        metavar="REPO",
    )

    # PR/MR ID argument
    parser.add_argument(
        "--pr-id",
        type=int,
        help="Pull request or merge request ID (overrides PR_ID env var)",
        metavar="ID",
    )

    # Instructions path argument
    parser.add_argument(
        "--instructions-path",
        type=str,
        help=(
            "Path to the local directory containing your custom instructions "
            "for the code review (overrides LOCAL_FILE_DIR env var)"
        ),
        metavar="PATH",
    )

    # Parse arguments
    try:
        args = parser.parse_args()
        print_success("Command line arguments parsed successfully")
        return args

    except Exception as e:
        print_error(f"Error parsing command line arguments: {str(e)}")
        parser.print_help()
        print_exception()
        sys.exit(1)


async def main() -> int:
    """Main entry point for the code review agent."""
    console.clear()
    print_header("Code Reviewer Agent")

    args = parse_arguments()
    platform: str = args.platform or os.getenv("PLATFORM", "")
    repository: str = args.repository or os.getenv("REPOSITORY", "")
    pr_id: int = args.pr_id
    instructions_path: str = args.instructions_path
    reviewed_label: str = "ReviewedByAI"

    print_section("Configuration")
    print_info(f"Platform: {platform.upper()}")
    print_info(f"Repository: {repository}")
    print_info(f"PR/MR ID: {pr_id}")
    print_info(f"Instructions path: {instructions_path}")

    # Validate inputs
    if platform not in ("github", "gitlab"):
        print_error("Invalid platform. Must be either 'github' or 'gitlab'")
        return 1

    if platform == "github" and not os.getenv("GITHUB_TOKEN", ""):
        print_error(
            "GITHUB_TOKEN environment variable is required when platform is 'github'"
        )
        return 1

    if platform == "gitlab" and not os.getenv("GITLAB_TOKEN", ""):
        print_error(
            "GITLAB_TOKEN environment variable is required when platform is 'gitlab'"
        )
        return 1

    if not repository:
        print_error(
            "Repository not specified. Use --repository or set REPOSITORY environment variable"
        )
        return 1

    # Fetch pull/merge request files
    print_section("Fetching PR/MR Information")
    repository_deps = {}

    try:
        if platform == "github":
            print_info("Connecting to GitHub repository...")
            GITHUB_PERSONAL_ACCESS_TOKEN = os.getenv("GITHUB_TOKEN", "")
            headers = {"Authorization": f"token {GITHUB_PERSONAL_ACCESS_TOKEN}"}
            pr_metadata_url = (
                f"https://api.github.com/repos/{repository}/pulls/{pr_id}/commits"
            )
            pr_metadata_response = requests.get(pr_metadata_url, headers=headers)
            pr_metadata = pr_metadata_response.json()
            if pr_metadata_response.status_code != 200:
                print_error(
                    f"Failed to fetch pull request commits: {pr_metadata_response.status_code} {pr_metadata_response.text}"
                )
                return 1

            url = f"https://api.github.com/repos/{repository}/pulls/{pr_id}/files"
            repository_deps = {
                "GITHUB_PERSONAL_ACCESS_TOKEN": GITHUB_PERSONAL_ACCESS_TOKEN,
                "PR_SHA": pr_metadata[-1]["sha"],
            }
            print_success("Successfully connected to GitHub repository")

        elif platform == "gitlab":
            print_info("Connecting to GitLab repository...")
            GITLAB_PERSONAL_ACCESS_TOKEN = os.getenv("GITLAB_TOKEN", "")
            GITLAB_API_URL = os.getenv("GITLAB_API_URL", "https://gitlab.com/api/v4")
            headers = {"Private-Token": f"{GITLAB_PERSONAL_ACCESS_TOKEN}"}
            mr_metadata_url = f"{GITLAB_API_URL}/projects/{repository.replace('/', '%2F')}/merge_requests/{pr_id}"
            mr_metadata_response = requests.get(mr_metadata_url, headers=headers)
            mr_metadata = mr_metadata_response.json()
            if mr_metadata_response.status_code != 200:
                print_error(
                    f"Failed to fetch merge request metadata: {mr_metadata_response.status_code} {mr_metadata_response.text}"
                )
                return 1

            url = f"{GITLAB_API_URL}/projects/{repository.replace('/', '%2F')}/merge_requests/{pr_id}/changes"
            repository_deps = {
                "GITLAB_PERSONAL_ACCESS_TOKEN": GITLAB_PERSONAL_ACCESS_TOKEN,
                "GITLAB_API_URL": GITLAB_API_URL,
                "MR_SHA_METADATA": mr_metadata["diff_refs"],
            }
            print_success("Successfully connected to GitLab repository")

        # Fetch the list of changed files
        print_info("Fetching list of changed files...")
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print_error(
                f"Failed to fetch pull request files: {response.status_code} {response.text}"
            )
            return 1

    except requests.exceptions.RequestException as e:
        print_error(f"Network error while fetching repository data: {str(e)}")
        return 1
    except Exception as e:
        print_error(f"Unexpected error while fetching repository data: {str(e)}")
        print_exception()
        return 1

    # Process the changed files
    print_section("Processing Changed Files")
    pull_request_files = response.json()
    files = (
        pull_request_files
        if platform == "github"
        else pull_request_files.get("changes", [])
    )

    # Process each file in the PR/MR
    user_messages = []
    print_info(f"Retrieving diffs from {platform.upper()}...")

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
            print_info(f"  - {filename} ({len(patch)} bytes)")

    # Check if there are files to review
    if not user_messages:
        print_warning("No files with changes found to review")
        return 0

    print_success(f"Found {len(user_messages)} file(s) with changes to review")

    # ========== Retrieving filesystem instructions ==========
    print_section("Retrieving Filesystem Instructions")
    print_info(f"Looking for instructions in: {local_instructions_dir}")

    try:
        # List all files in the instructions directory using direct filesystem access
        instructions_files = [
            f
            for f in os.listdir(local_instructions_dir)
            if os.path.isfile(os.path.join(local_instructions_dir, f))
        ]

        filesystem_instructions = []
        for file in instructions_files:
            file_path = os.path.join(local_instructions_dir, file)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    filesystem_instructions.append(content)
                    print_success(f"  - Loaded: {file} ({len(content)} bytes)")
            except Exception as file_error:
                print_warning(f"  - Failed to load {file}: {str(file_error)}")

        if not filesystem_instructions:
            print_warning("No instruction files found or loaded successfully")
        else:
            print_success(
                f"Successfully loaded {len(filesystem_instructions)} instruction file(s)"
            )

    except Exception as e:
        print_error(f"Error while retrieving filesystem instructions: {str(e)}")
        print_exception()
        return 1

    # ========== Reviewer Agent: loop on each file diff ==========
    print_section("Starting Code Review")
    print_info(f"Reviewing {len(user_messages)} file(s) with changes")

    try:
        with tracer.start_as_current_span("CR-Agent-Main-Trace") as main_span:
            main_span.set_attribute("langfuse.user.id", f"pr-{pr_id}")
            main_span.set_attribute("langfuse.session.id", repository)

            for user_message_item in user_messages:
                user_message: dict[str, Any] = user_message_item
                filename = user_message.get("filename", "unknown")
                languages = ", ".join(user_message.get("languages", ["unknown"]))
                patch = user_message.get("patch", "")

                print_header(f"Reviewing: {filename}")
                print_info(f"Languages: {languages}")

                # Print the diff with syntax highlighting
                if patch:
                    print_section("Code Changes")
                    print_diff(patch, filename)

                # Prepare the input for the code review
                diff_content = (
                    f"# Filename: {filename}\n# Languages: {languages}\n{patch}\n"
                )
                user_input = MAIN_USER_PROMPT.format(
                    custom_instructions=(
                        "\n\n".join(filesystem_instructions)
                        if filesystem_instructions
                        else "No custom instructions provided."
                    ),
                    diff=diff_content,
                )

                # Start tracing for this file review
                with tracer.start_as_current_span(
                    "CR-Agent-Review"
                ) as file_review_span:
                    file_review_span.set_attribute("langfuse.user.id", f"pr-{pr_id}")
                    file_review_span.set_attribute("langfuse.session.id", repository)
                    file_review_span.set_attribute("filename", filename)
                    file_review_span.set_attribute("languages", languages)

                    # Allow the AI Agent to retry up to 3 times if it fails to format the output correctly
                    i = 1
                    retry_limit = 3
                    succeeded = False
                    suffix_user_instructions = "\n\n**Your output is not in the correct JSON format!** Please try again."
                    safe_cr_agent_output = ""

                    print_info(
                        f"Starting code review (max {retry_limit} attempts allowed)"
                    )

                    while i <= retry_limit:
                        attempt_header = f"Attempt {i}/{retry_limit}"
                        print_section(attempt_header, "🔄")

                        try:
                            # Run the code review AI Agent
                            print_info("Running AI code review...")
                            start_time = time.perf_counter()

                            try:
                                reviewer_output = await reviewer_agent.run(
                                    f"{user_input}{suffix_user_instructions if i > 1 else ''}"
                                )
                            except Exception as agent_error:
                                print_error(f"Agent run failed: {str(agent_error)}")
                                raise

                            duration = time.perf_counter() - start_time
                            print_success(f"Review completed in {duration:.2f} seconds")

                            # Parse the output of the code review AI Agent
                            print_info("Validating review output...")
                            safe_cr_agent_output = (
                                reviewer_output.output.replace("\r", "")
                                .replace("\n", "")
                                .replace("\t", "")
                            )

                            try:
                                reviewer_output_json = json.loads(safe_cr_agent_output)

                                # Validate the structure of the output
                                if not isinstance(reviewer_output_json, list):
                                    raise ValueError("Output is not a list of objects")

                                for idx, item in enumerate(reviewer_output_json):
                                    if not isinstance(item, dict):
                                        raise ValueError(
                                            f"Item at index {idx} in output is not a dictionary"
                                        )

                                    # Check for required keys
                                    required_keys = [
                                        "line_number",
                                        "code_diff",
                                        "comments",
                                        "title",
                                    ]
                                    for key in required_keys:
                                        if key not in item:
                                            raise ValueError(
                                                f"Item at index {idx} is missing required key: {key}"
                                            )

                                    # Check for unexpected keys
                                    if len(item) > 4:
                                        extra_keys = set(item.keys()) - set(
                                            required_keys
                                        )
                                        raise ValueError(
                                            f"Item at index {idx} has unexpected keys: {', '.join(extra_keys)}"
                                        )

                                # If we get here, validation passed
                                print_success("Output validation passed")

                                # Print the review summary
                                print_section("Review Summary")
                                for idx, item in enumerate(reviewer_output_json, 1):
                                    print_info(
                                        f"Finding {idx}: {item.get('title', 'No title')}"
                                    )
                                    print_info(
                                        f"  • Line: {item.get('line_number', 'N/A')}"
                                    )
                                    severity = item.get("severity", "info").upper()
                                    severity_color = {
                                        "CRITICAL": "red",
                                        "HIGH": "yellow",
                                        "MEDIUM": "blue",
                                        "LOW": "cyan",
                                        "INFO": "green",
                                    }.get(severity, "white")
                                    print_info(
                                        f"  • Severity: [{severity_color}]{severity}[/{severity_color}]"
                                    )

                                succeeded = True
                                break

                            except (json.JSONDecodeError, ValueError) as e:
                                print_error(f"Validation error: {str(e)}")
                                print_debug(
                                    f"Raw output: {safe_cr_agent_output[:500]}..."
                                    if len(safe_cr_agent_output) > 500
                                    else f"Raw output: {safe_cr_agent_output}"
                                )

                                if i < retry_limit:
                                    print_info(
                                        f"Retrying... ({i+1}/{retry_limit} attempts remaining)"
                                    )
                                    suffix_user_instructions += f" Failed to validate output from your attempt #{i}! Error log: {str(e)}."
                                    i += 1
                                    continue
                                else:
                                    raise

                        except Exception as e:
                            print_error(
                                f"Unexpected error during review attempt {i}: {str(e)}"
                            )
                            if i < retry_limit:
                                print_info(
                                    f"Retrying... ({i+1}/{retry_limit} attempts remaining)"
                                )
                                i += 1
                                continue
                            else:
                                raise

                    # Set attributes before potential loop "continue"
                    file_review_span.set_attribute("input.value", user_input)
                    file_review_span.set_attribute("output.value", safe_cr_agent_output)

                    if not succeeded:
                        print_error(
                            f"Failed to parse JSON output from CR AI Agent after {retry_limit} attempts! "
                            "Skipping this file diff."
                        )
                        continue

                    # Post review comments to the PR/MR
                    print_section("Posting Review")
                    try:
                        if platform == "github":
                            print_info("Posting review to GitHub...")
                            await post_github_review(
                                repository,
                                pr_id,
                                user_message,
                                reviewer_output_json,
                                repository_deps,
                            )
                        else:
                            print_info("Posting review to GitLab...")
                            await post_gitlab_review(
                                repository,
                                pr_id,
                                user_message,
                                reviewer_output_json,
                                repository_deps,
                            )
                        print_success("Review posted successfully")

                    except Exception as post_error:
                        print_error(f"Failed to post review: {str(post_error)}")
                        print_exception()
                        # Continue with the next file even if posting fails for one

            # Add label and assign reviewer after processing all files
            print_section("Finalizing Review")
            try:
                if platform == "github":
                    print_info("Adding reviewer and label to GitHub PR...")
                    await add_github_reviewer(
                        repository, pr_id, headers, reviewed_label
                    )
                else:
                    print_info("Adding reviewer and label to GitLab MR...")
                    await add_gitlab_reviewer(
                        repository, pr_id, headers, reviewed_label, repository_deps
                    )
                print_success("Reviewer and label added successfully")

            except Exception as reviewer_error:
                print_error(f"Failed to add reviewer/label: {str(reviewer_error)}")
                print_exception()
                # Continue even if reviewer/label update fails

    except Exception as e:
        print_error(f"An unexpected error occurred: {str(e)}")
        print_exception()
        return 1

    print_section("Review Complete", "✅")
    print_success("Code review process finished successfully")
    return 0


async def post_github_review(
    repository: str,
    pr_id: int,
    user_message: dict,
    reviewer_output_json: list,
    repository_deps: dict,
) -> None:
    """Post review comments to a GitHub PR."""
    print_section("Posting to GitHub PR", "📝")
    headers = {
        "Authorization": f"token {repository_deps['GITHUB_PERSONAL_ACCESS_TOKEN']}",
        "Accept": "application/vnd.github.v3+json",
    }

    try:
        print_info("Preparing review comments...")
        body = ""
        for cr_comment in reviewer_output_json:
            body += (
                f"### {cr_comment.get('title', 'Code Review Comment')}\n"
                f"**Line {cr_comment.get('line_number', 'N/A')}**\n\n"
                f"{cr_comment.get('comments', '')}\n\n"
                "```diff\n"
                f"{cr_comment.get('code_diff', '')}"
                "\n```\n\n"
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

        print_info(f"Posting review to PR #{pr_id}...")
        response = requests.post(
            f"https://api.github.com/repos/{repository}/pulls/{pr_id}/comments",
            headers=headers,
            json=data,
        )

        if response.status_code != 201:
            print_error(
                f"Failed to post comment on PR #{pr_id}: {response.status_code}"
            )
            print_debug(f"Response: {response.text}")
        else:
            print_success(f"Successfully posted review comment on PR #{pr_id}")

    except Exception as e:
        print_error(f"Error posting to GitHub PR: {str(e)}")
        print_exception()


async def post_gitlab_review(
    repository: str,
    mr_id: int,
    user_message: dict,
    reviewer_output_json: list,
    repository_deps: dict,
) -> None:
    """Post review comments to a GitLab MR."""
    print_section("Posting to GitLab MR", "📝")
    headers = {
        "Private-Token": repository_deps["GITLAB_PERSONAL_ACCESS_TOKEN"],
        "Content-Type": "application/json",
    }

    try:
        comment_count = 0
        print_info(
            f"Preparing {len(reviewer_output_json)} comment(s) for MR #{mr_id}..."
        )

        for idx, cr_comment in enumerate(reviewer_output_json, 1):
            try:
                print_info(f"Posting comment {idx}/{len(reviewer_output_json)}...")

                # Format the comment with markdown
                body = (
                    f"**{cr_comment.get('title', 'Code Review Comment')}**\n\n"
                    f"{cr_comment.get('comments', '')}\n\n"
                    "```diff\n"
                    f"{cr_comment.get('code_diff', '')}\n"
                    "```"
                )

                data = {
                    "body": body,
                    "position": {
                        "base_sha": repository_deps["MR_SHA_METADATA"]["base_sha"],
                        "start_sha": repository_deps["MR_SHA_METADATA"]["start_sha"],
                        "head_sha": repository_deps["MR_SHA_METADATA"]["head_sha"],
                        "position_type": "text",
                        "new_path": user_message["filename"],
                        "new_line": cr_comment.get("line_number", 1),
                    },
                }

                response = requests.post(
                    f"{repository_deps['GITLAB_API_URL']}/projects/{repository.replace('/', '%2F')}/merge_requests/{mr_id}/discussions",
                    headers=headers,
                    json=data,
                )

                if response.status_code == 201:
                    comment_count += 1
                    print_success(f"Posted comment {idx}/{len(reviewer_output_json)}")
                else:
                    print_error(
                        f"Failed to post comment {idx}/{len(reviewer_output_json)}: "
                        f"{response.status_code} - {response.text}"
                    )

            except Exception as comment_error:
                print_error(
                    f"Error posting comment {idx}/{len(reviewer_output_json)}: {str(comment_error)}"
                )
                print_exception()
                continue

        if comment_count > 0:
            print_success(
                f"Successfully posted {comment_count} comment(s) to MR #{mr_id}"
            )
        else:
            print_warning("No comments were successfully posted to the MR")

    except Exception as e:
        print_error(f"Error posting to GitLab MR: {str(e)}")
        print_exception()


async def add_github_reviewer(
    repository: str, pr_id: int, headers: dict, reviewed_label: str
) -> None:
    """Add reviewer and label to a GitHub PR."""
    print_section("Adding GitHub Reviewer", "👥")

    try:
        # Add label
        print_info(f"Adding label '{reviewed_label}' to PR #{pr_id}...")
        label_url = f"https://api.github.com/repos/{repository}/issues/{pr_id}/labels"
        label_data = {"labels": [reviewed_label]}

        response = requests.post(label_url, headers=headers, json=label_data)
        if response.status_code == 200:
            print_success(f"Successfully added label '{reviewed_label}' to PR #{pr_id}")
        else:
            print_error(
                f"Failed to add label '{reviewed_label}' to PR #{pr_id}: "
                f"{response.status_code} - {response.text}"
            )

        # Request review from the owner of the PR
        print_info(f"Requesting review for PR #{pr_id}...")
        pr_url = f"https://api.github.com/repos/{repository}/pulls/{pr_id}"
        pr_response = requests.get(pr_url, headers=headers)

        if pr_response.status_code != 200:
            print_error(
                f"Failed to get PR details for #{pr_id}: {pr_response.status_code} - {pr_response.text}"
            )
            return

        pr_data = pr_response.json()
        if "user" not in pr_data or "login" not in pr_data["user"]:
            print_warning("Could not determine PR author. Cannot request review.")
            return

        author = pr_data["user"]["login"]
        review_url = f"https://api.github.com/repos/{repository}/pulls/{pr_id}/requested_reviewers"
        review_data = {"reviewers": [author]}

        response = requests.post(review_url, headers=headers, json=review_data)
        if response.status_code == 201:
            print_success(f"Successfully requested review from {author} on PR #{pr_id}")
        else:
            print_error(
                f"Failed to request review from {author} on PR #{pr_id}: "
                f"{response.status_code} - {response.text}"
            )

    except Exception as e:
        print_error(f"Error adding GitHub reviewer: {str(e)}")
        print_exception()


async def add_gitlab_reviewer(
    repository: str,
    mr_id: int,
    headers: dict,
    reviewed_label: str,
    repository_deps: dict,
) -> None:
    """Add reviewer and label to a GitLab MR."""
    print_section("Adding GitLab Reviewer", "👥")

    try:
        # Add the label to the MR
        print_info(f"Adding label '{reviewed_label}' to MR #{mr_id}...")
        label_url = (
            f"{repository_deps['GITLAB_API_URL']}/projects/"
            f"{repository.replace('/', '%2F')}/merge_requests/{mr_id}?add_labels={reviewed_label}"
        )

        response = requests.put(label_url, headers=headers)
        if response.status_code == 200:
            print_success(f"Successfully added label '{reviewed_label}' to MR #{mr_id}")
        else:
            print_error(
                f"Failed to add label to MR #{mr_id}: {response.status_code} - {response.text}"
            )

        # Get the current user to assign as reviewer
        print_info("Getting current user information...")
        user_resp = requests.get(
            f"{repository_deps['GITLAB_API_URL']}/user", headers=headers
        )

        if user_resp.status_code != 200:
            print_error(
                f"Failed to get current user: {user_resp.status_code} - {user_resp.text}"
            )
            return

        try:
            user_data = user_resp.json()
            reviewer_id = user_data.get("id")
            reviewer_name = user_data.get("name", f"User {reviewer_id}")

            if not reviewer_id:
                print_warning("Could not determine reviewer ID from user data")
                return

            print_info(f"Current user: {reviewer_name} (ID: {reviewer_id})")

            # Assign the current user as reviewer
            print_info(f"Assigning {reviewer_name} as reviewer to MR #{mr_id}...")
            reviewer_url = (
                f"{repository_deps['GITLAB_API_URL']}/projects/"
                f"{repository.replace('/', '%2F')}/merge_requests/{mr_id}"
                f"?reviewer_ids%5B%5D={reviewer_id}"
            )

            response = requests.put(reviewer_url, headers=headers)
            if response.status_code == 200:
                print_success(
                    f"Successfully assigned {reviewer_name} as reviewer to MR #{mr_id}"
                )
            else:
                print_error(
                    f"Failed to assign reviewer to MR #{mr_id}: {response.status_code} - {response.text}"
                )

        except (ValueError, KeyError) as e:
            print_error(f"Error processing user data: {str(e)}")
            print_debug(f"User response: {user_resp.text}")

    except Exception as e:
        print_error(f"Error adding GitLab reviewer: {str(e)}")
        print_exception()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code if isinstance(exit_code, int) else 0)
