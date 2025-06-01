import argparse
import asyncio
import os
import requests
import time
import json
from openai import OpenAI

from dotenv import load_dotenv

from agent_model import get_model, get_supabase, get_embedding_model_str
from agent_prompts import (
    MAIN_USER_PROMPT,
    REVIEW_PROMPT,
)

from pydantic_ai import Agent

from configure_langfuse import configure_langfuse
from utils import get_file_languages

load_dotenv()

# Configure Langfuse for agent observability
tracer = configure_langfuse()
local_instructions_dir = os.getenv('LOCAL_FILE_DIR', '')
supabase_client = get_supabase()

openai_client = OpenAI()

# ========== Utils functions ==========

def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Code Review Agent')
    parser.add_argument('--platform', type=str, choices=['github', 'gitlab'],
                       help='Platform: github or gitlab (overrides PLATFORM env var)')
    parser.add_argument('--repository', type=str,
                       help='Repository in format owner/repo for GitHub and project_id for GitLab (overrides REPOSITORY env var)')
    parser.add_argument('--pr-id', type=int, required=True,
                       help='Pull/Merge Request ID to review')
    parser.add_argument('--instructions-path', type=str, default='instructions',
                       help='Path to custom review instructions folder (default: instructions)')
    return parser.parse_args()

def search_documents(query: str, match_threshold: float = 0.8) -> list[dict]:
    """Search for documents similar to the query using embeddings.

    Args:
        query: The search query string
        match_threshold: Similarity threshold for document matching (0-1)

    Returns:
        List of matching documents with their metadata
    """
    embeddings_response = openai_client.embeddings.create(
        input=query,
        model=get_embedding_model_str()
    )
    embedding = embeddings_response.data[0].embedding
    response = supabase_client.rpc("match_documents", {
        "query_embedding": embedding,
        "match_threshold": match_threshold
    }).execute()
    return response.data

# ========== Create the code reviewer agents ==========

reviewer_agent = Agent(
    get_model(),
    system_prompt=REVIEW_PROMPT,
    tools=[search_documents],
    instrument=True
)

# ========== Main execution function ==========

async def main():
    """Main entry point for the code review agent."""
    args = parse_arguments()

    platform = args.platform
    repository = args.repository or os.getenv('REPOSITORY', '')
    pr_id = args.pr_id

    instructions_path = args.instructions_path

    reviewed_label = "ReviewedByAI"

    print((
        f"Starting code review for {platform.upper()} PR/MR #{pr_id} in {repository}.",
        f"Instructions path: {instructions_path}.",
    ))

    # ========== Validate inputs ==========

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
        print("Repository not specified. Use --repository or set REPOSITORY environment variable")
        return 1

    # ========== Fetch pull request files ==========

    repository_deps = {}
    if platform == "github":
        GITHUB_PERSONAL_ACCESS_TOKEN = os.getenv('GITHUB_TOKEN', '')
        # Define the headers
        headers = {"Authorization": f"token {GITHUB_PERSONAL_ACCESS_TOKEN}"}
        # Get the latest commit SHA of the PR
        pr_metadata_url = f"https://api.github.com/repos/{repository}/pulls/{pr_id}/commits"
        pr_metadata_response = requests.get(pr_metadata_url, headers=headers)
        pr_metadata = pr_metadata_response.json()
        if pr_metadata_response.status_code != 200:
            print(f"\033[91mFailed to fetch pull request commits: {pr_metadata_response.status_code} {pr_metadata_response.text}\033[0m")
            return 1
        # Construct the URL to fetch the diff
        url = f"https://api.github.com/repos/{repository}/pulls/{pr_id}/files"
        # Store the dependencies
        repository_deps = {
            "GITHUB_PERSONAL_ACCESS_TOKEN": GITHUB_PERSONAL_ACCESS_TOKEN,
            "PR_SHA": pr_metadata[-1]["sha"], # Setup latest commit SHA of the PR
        }
    elif platform == "gitlab":
        GITLAB_PERSONAL_ACCESS_TOKEN = os.getenv('GITLAB_TOKEN', '')
        GITLAB_API_URL = os.getenv('GITLAB_API_URL', 'https://gitlab.com/api/v4')
        # Define the headers
        headers = {"Private-Token": f"{GITLAB_PERSONAL_ACCESS_TOKEN}"}
        # Get MR Metadata with SHAs
        mr_metadata_url = f"{GITLAB_API_URL}/projects/{repository}/merge_requests/{pr_id}"
        print(mr_metadata_url)
        mr_metadata_response = requests.get(mr_metadata_url, headers=headers)
        mr_metadata = mr_metadata_response.json()
        if mr_metadata_response.status_code != 200:
            print(f"\033[91m[ERROR] Failed to fetch merge request metadata: {mr_metadata_response.status_code} {mr_metadata_response.text}\033[0m")
            return 1
        # Construct the URL to fetch the diff
        url = f"{GITLAB_API_URL}/projects/{repository}/merge_requests/{pr_id}/changes"
        # Store the dependencies
        repository_deps = {
            "GITLAB_PERSONAL_ACCESS_TOKEN": GITLAB_PERSONAL_ACCESS_TOKEN,
            "GITLAB_API_URL": GITLAB_API_URL,
            "MR_SHA_METADATA": mr_metadata["diff_refs"],
        }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"\033[91mFailed to fetch pull request files: {response.status_code} {response.text}\033[0m")
        return 1

    pull_request_files = response.json()
    files = []
    if platform == "github":
        files = pull_request_files
    elif platform == "gitlab":
        files = pull_request_files.get("changes", [])

    # ========== Generate user messages for each file diff ==========

    userMessages = []
    print(f"\033[94mRetrieving diff from {platform.upper()}:\033[0m")
    for file in files:
        # Retrieve file name
        filename = ""
        if platform == "github":
            filename = file["filename"]
        elif platform == "gitlab":
            filename = file["new_path"]

        diff = {
            "filename": filename,
            "languages": get_file_languages(filename),
            "patch": "",
        }

        # Retrieve patch/diff string
        patch = ""
        if platform == "github":
            patch = file.get("patch", "")
            # Setup additional information for GitHub
            diff["sha"] = repository_deps["PR_SHA"]
        elif platform == "gitlab":
            patch = file.get("diff", "")
            # Setup additional information for GitLab
            diff["sha_metadata"] = repository_deps["MR_SHA_METADATA"]

        # Continue with the file diff if not empty
        if patch:
            # IMPORTANT: Replace all triple backticks with single backticks or escape them
            safePatch = patch.replace('```', "''")
            diff["patch"] = "```diff\n"
            diff["patch"] += safePatch
            diff["patch"] += "\n```"

            # Store diff changes as user message
            userMessages.append(diff)
            print((
                f"\033[92m+ {filename} --- detected {', '.join(diff['languages']).upper()} languages"
                f" at SHA\033[0m {diff['sha'] if platform == 'github' else diff['sha_metadata']['base_sha']}"
            ))
        else:
            print(f"\033[91m- {filename} --- no diff (probably moved or renamed file only)\033[0m")

    # ========== Retrieving filesystem instructions ==========

    try:
        print(f"\n\033[94mRetrieving filesystem instructions at {local_instructions_dir}...\033[0m")
        # List all files in the instructions directory using direct filesystem access
        instructions_files = [f for f in os.listdir(local_instructions_dir)
                                if os.path.isfile(os.path.join(local_instructions_dir, f))]
        filesystem_instructions = []
        for file in instructions_files:
            file_path = os.path.join(local_instructions_dir, file)
            with open(file_path, 'r', encoding='utf-8') as f:
                filesystem_instructions.append(f.read())
        print(f"\033[92mRetrieved {len(instructions_files)} instructions file(s):\033[0m")
        for file in instructions_files:
            print(f"\033[92m- {file}\033[0m")

    except Exception as e:
        print(f"\n\033[91m[Retrieving filesystem instructions error] An error occurred: {str(e)}\033[0m")
        return 1

    # ========== Reviewer Agent: loop on each file diff ==========

    try:
        with tracer.start_as_current_span("CR-Agent-Main-Trace") as main_span:
            main_span.set_attribute("langfuse.user.id", f"pr-{pr_id}")
            main_span.set_attribute("langfuse.session.id", repository)

            for userMessage in userMessages:
                with tracer.start_as_current_span("CR-Agent-Review") as file_review_span:
                    file_review_span.set_attribute("langfuse.user.id", f"pr-{pr_id}")
                    file_review_span.set_attribute("langfuse.session.id", repository)

                    # ----- Generate user input for the code review
                    diff = (
                        f"# Filename: {userMessage['filename']}\n"
                        f"# Languages: {', '.join(userMessage['languages'])}\n"
                        f"{userMessage['patch']}\n"
                    )
                    print(f"\n\033[95mStarting CR by AI Agent of the following diff:\n{diff}\033[0m")
                    user_input = MAIN_USER_PROMPT.format(
                        custom_instructions="\n\n".join(filesystem_instructions),
                        diff=diff
                    )

                    # Allow the AI Agent to retry up to 3 times if it fails to format the output correctly
                    i = 1
                    retry_limit = 3
                    succeeded = False
                    suffix_user_instructions = "\n\n**Your output is not in the correct JSON format!** Please try again."
                    while i <= retry_limit:
                        try:
                            # ----- Run the code review AI Agent
                            start_time = time.perf_counter()
                            reviewer_output = await reviewer_agent.run(f"{user_input}{suffix_user_instructions if i > 0 else ''}")
                            duration = time.perf_counter() - start_time
                            print(f"\033[93mCR AI Agent took ⏱️ {duration:.3f} seconds to review the file diff.\033[0m")

                            # ----- Parse the output of the code review AI Agent

                            # Escape all literal newlines and carriage returns (make all line breaks become '\\n')
                            safe_cr_agent_output = reviewer_output.output.replace('\r', '').replace('\n', '').replace('\t', '')
                            reviewer_output_json = json.loads(safe_cr_agent_output)

                            if not isinstance(reviewer_output_json, list):
                                raise ValueError("Output is not a list of objects")
                            for idx, item in enumerate(reviewer_output_json):
                                if not isinstance(item, dict):
                                    raise ValueError(f"Item at index {idx} in output is not a dictionary")
                                for key in ["line_number", "code_diff", "comments", "title"]:
                                    if key not in item:
                                        raise ValueError(f"Item at index {idx} is missing required key: {key}")
                                if len(item) > 4:
                                    raise ValueError(f"Item at index {idx} has more keys than expected")
                            succeeded = True
                            print(f"\033[92mSuccessfully parsed JSON output from CR AI Agent! Metadata are:\033[0m")
                            print("\033[96m" + json.dumps(reviewer_output_json, indent=2) + "\033[0m")
                            break
                        except json.JSONDecodeError as e:
                            print(f"\033[91m[Error] Failed to validate output from CR AI Agent: {str(e)}. Attempt #{i} output:\n{safe_cr_agent_output}\033[0m")
                            suffix_user_instructions += f"Failed to validate output from your attempt #{i}! Error log: {str(e)}."
                            i += 1

                    # Set attributes before potential loop "continue"
                    file_review_span.set_attribute("input.value", user_input)
                    file_review_span.set_attribute("output.value", safe_cr_agent_output)

                    if not succeeded:
                        print(f"\n\033[95m[Critical] Failed to parse JSON output from CR AI Agent after {retry_limit} attempts! Skipping this file diff.\n\033[0m")
                        continue

                    if platform == "github":
                        # GitHub's API doesn't give you:
                        # - the diff of a specific commit in the context of the PR, nor
                        # - an endpoint to post inline comments on such a commit
                        #
                        # So posting all the comment ON THE LAST COMMIT of the PR
                        print(f"\n\033[94mPosting {len(reviewer_output_json)} comment(s) on the PR...\033[0m")
                        headers = {
                            "Authorization": f"Bearer {repository_deps['GITHUB_PERSONAL_ACCESS_TOKEN']}",
                            "Accept": "application/vnd.github.v3+json"
                        }
                        # Defining the body as follow:
                        #   - One comment by file placed on the first line of the file code diff.
                        #   - This comment contains all the comments from the AI Agent.
                        #
                        # This is enforced here because the AI Agent has difficulty finding the correct line of code to put the comment on.
                        body = "# Code reviewer AI Agent comments\n\n"
                        for cr_comment in reviewer_output_json:
                            body += f"## {cr_comment.get('title', 'Comment')}\n\n"
                            body += cr_comment.get("comments", "") + "\n\n```diff\n" + cr_comment.get("code_diff", "") + "\n```\n\n"

                        data = {
                            "body": body,
                            "commit_id": userMessage["sha"],
                            "path": userMessage['filename'],
                            "side": "RIGHT",
                            "line": reviewer_output_json[0].get("line_number", 0), # Retrieve the line_number of the first comment (after that, the Agent hallucinate this value)
                        }
                        response = requests.post(
                            f"https://api.github.com/repos/{repository}/pulls/{pr_id}/comments",
                            headers=headers,
                            json=data
                        )
                        if response.status_code != 201:
                            print(f"\033[91m[Error] Failed to post a new comment on the PR #{pr_id}: {response.text}\n\033[0m")
                        else:
                            print(f"\033[92mComment(s) posted on the PR #{pr_id}!\033[0m")

                    elif platform == "gitlab":
                        # Post the code review to the MR, as a comment, on the corresponding commit, on the corresponding line of code
                        print("\n\033[94mPosting comment result on the MR...\033[0m")
                        headers = {
                            "Private-Token": repository_deps['GITLAB_PERSONAL_ACCESS_TOKEN'],
                            "Content-Type": "application/json"
                        }
                        for cr_comment in reviewer_output_json:
                            body = cr_comment.get("comments", "") + "\n\n```diff\n" + cr_comment.get("code_diff", "") + "\n```\n\n"
                            data = {
                                "body": body,
                                "position": {
                                    "position_type": "text",
                                    "base_sha": userMessage["sha_metadata"]["base_sha"],
                                    "start_sha": userMessage["sha_metadata"]["start_sha"],
                                    "head_sha": userMessage["sha_metadata"]["head_sha"],
                                    "new_path": userMessage["filename"],
                                    # "old_path": userMessage["filename"],
                                    "new_line": cr_comment.get("line_number", 0),
                                    # "old_line": reviewer_output_json.get("line_number", 0),
                                },
                            }
                            response = requests.post(
                                f"{repository_deps['GITLAB_API_URL']}/projects/{repository}/merge_requests/{pr_id}/discussions",
                                headers=headers,
                                json=data
                            )
                            if response.status_code != 201:
                                print(f"\033[91m[Error] Failed to post a new comment on the MR #{pr_id}: {response.text}\n\033[0m")
                            else:
                                print(f"\033[92mComment(s) posted on the MR #{pr_id}!\033[0m")

        # Add the "reviewed_label" label to the PR/MR
        # Additionally, set the Reviewer as the user linked to the GITHUB_PERSONAL_ACCESS_TOKEN env variable
        if platform == "github":
            # Set the label for the PR (GitHub)
            response = requests.post(
                f"https://api.github.com/repos/{repository}/issues/{pr_id}/labels",
                headers=headers,
                json=[{"name": reviewed_label}]
            )
            if response.status_code != 200:
                print(f"\n\033[91m[Error] Failed to add label: {response.text}\n\033[0m")
            else:
                print(f"\n\033[95mLabel '{reviewed_label}' added to PR #{pr_id}!\033[0m")

            # Get the username of the authenticated user with the GITHUB_PERSONAL_ACCESS_TOKEN
            user_resp = requests.get(
                "https://api.github.com/user",
                headers=headers
            )
            if user_resp.status_code != 200:
                print(f"\n\033[91m[Error] Failed to get username: {user_resp.text}\n\033[0m")
            else:
                reviewer = user_resp.json()["login"]
                print(f"\n\033[93mUsername '{reviewer}' retrieved! Assigning reviewer on the PR...\033[0m")
                # Assign reviewer to the pull request
                response = requests.post(
                    f"https://api.github.com/repos/{repository}/pulls/{pr_id}/requested_reviewers",
                    headers=headers,
                    json={"reviewers": [reviewer]}
                )
                if response.status_code != 200:
                    print(f"\033[91m[Error] Failed to assign PR: {response.text}\n\033[0m")
                else:
                    print(f"\033[95mReviewer {reviewer} set for PR #{pr_id}!\033[0m")
        elif platform == "gitlab":
            # Set the label for the MR (GitLab)
            response = requests.put(
                f"{repository_deps['GITLAB_API_URL']}/projects/{repository}/merge_requests/{pr_id}",
                headers=headers,
                json={"labels": reviewed_label}
            )
            if response.status_code != 200:
                print(f"\033[91m[Error] Failed to add label: {response.text}\n\033[0m")
            else:
                print(f"\n\033[95mLabel '{reviewed_label}' added to MR #{pr_id}!\033[0m")

            # Get the username (and ID) of the authenticated user with the GITLAB_PERSONAL_ACCESS_TOKEN
            user_resp = requests.get(
                f"{repository_deps['GITLAB_API_URL']}/user",
                headers=headers
            )
            if user_resp.status_code != 200:
                print(f"\n\033[91m[Error] Failed to get username: {user_resp.text}\n\033[0m")
            else:
                reviewer_id = user_resp.json()["id"]
                reviewer_username = user_resp.json()["username"]
                print(f"\n\033[93mUsername '{reviewer_username}' retrieved! Assigning reviewer on the MR...\033[0m")
                # Assign reviewer to the merge request
                response = requests.put(
                    f"{repository_deps['GITLAB_API_URL']}/projects/{repository}/merge_requests/{pr_id}",
                    headers=headers,
                    json={"reviewer_ids": [reviewer_id]}
                )
                if response.status_code != 200:
                    print(f"\033[91m[Error] Failed to assign MR: {response.text}\n\033[0m")
                else:
                    print(f"\033[95mReviewer {reviewer_username} set for MR #{pr_id}!\033[0m")

    except Exception as e:
        print(f"\n\033[91m[Error] An error occurred: {str(e)}\n\033[0m")
        return 1

if __name__ == "__main__":
    asyncio.run(main())
