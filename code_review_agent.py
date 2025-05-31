import argparse
import asyncio
import os
import requests

from dotenv import load_dotenv

from agent_model import get_model
from agent_prompts import (
    FILESYSTEM_INSTRUCTIONS_RETRIEVER_USER_PROMPT,
    MAIN_USER_PROMPT,
    REVIEW_PROMPT,
)
from contextlib import AsyncExitStack

from rich.markdown import Markdown
from rich.console import Console
from rich.live import Live

from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio

from configure_langfuse import configure_langfuse
from utils import get_file_languages

load_dotenv()

# Configure Langfuse for agent observability
tracer = configure_langfuse()
chunk_size = 1000

def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Code Review Agent')
    parser.add_argument('--platform', type=str, choices=['github', 'gitlab'],
                       help='Platform: github or gitlab (overrides PLATFORM env var)')
    parser.add_argument('--repository', type=str,
                       help='Repository in format owner/repo (overrides REPOSITORY env var')
    parser.add_argument('--pr-id', type=int, required=True,
                       help='Pull/Merge Request ID to review')
    parser.add_argument('--instructions-path', type=str, default='instructions',
                       help='Path to custom review instructions folder (default: instructions)')
    return parser.parse_args()

# ========== Set up MCP servers for each service ==========

# Filesystem MCP server
filesystem_server = MCPServerStdio(
    'npx', ['-y', '@modelcontextprotocol/server-filesystem', os.getenv('LOCAL_FILE_DIR', '')],
    tool_prefix='filesystem',
)

# Crawl4ai MCP server
crawl4ai_server = MCPServerStdio(
    'docker',
    [
        'run', '--rm', '-i',
        '-e', 'TRANSPORT',
        '-e', 'OPENAI_API_KEY',
        '-e', 'SUPABASE_URL',
        '-e', 'SUPABASE_SERVICE_KEY',
        'mcp/crawl4ai-rag'
    ],
    {
        'TRANSPORT': 'stdio',
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY', ''),
        'SUPABASE_URL': os.getenv('SUPABASE_URL', ''),
        'SUPABASE_SERVICE_KEY': os.getenv('SUPABASE_SERVICE_KEY', '')
    },
    tool_prefix='crawl4ai',
)

# ========== Create subagents with their MCP servers ==========

# Custom instructions retriever agent
filesystem_instructions_retriever_agent = Agent(
    get_model(),
    system_prompt="""
    You are a file system files retriever agent. Help retrieve the related information from the files for the code review.
    """,
    mcp_servers=[filesystem_server],
    instrument=True
)

# Crawl4ai agent
crawl4ai_agent = Agent(
    get_model(),
    system_prompt="""
    You are a vector database documentation retriever agent. Help retrieve the related documentation based on the languages of the code to review from the vector database.
    """,
    mcp_servers=[crawl4ai_server],
    instrument=True
)

# ========== Create the code reviewer agents ==========
reviewer_agent = Agent(
    get_model(),
    system_prompt=REVIEW_PROMPT,
    instrument=True
)

# ========== Define tools for the reviewer agent to call subagents ==========
@reviewer_agent.tool_plain
async def use_crawl4ai_agent(query: str) -> dict[str, str]:
    """
    Interact with the crawl4ai agent.
    Use this tool to retrieve the related documentation based on the languages of the code to review from the vector database.

    Args:
        ctx: The run context.
        query: The instruction for the crawl4ai agent.

    Returns:
        The response from the crawl4ai agent.
    """
    print(f"Calling crawl4ai agent with query: {query}")
    result = await crawl4ai_agent.run(query)
    return {"result": result.output}

# ========== Main execution function ==========

async def main():
    """Main entry point for the code review agent."""
    args = parse_arguments()

    platform = args.platform
    repository = args.repository or os.getenv('REPOSITORY', '')
    pr_id = args.pr_id

    instructions_path = args.instructions_path

    print((
        f"Starting code review for {platform.upper()} PR #{pr_id} in {repository}.",
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
        url = f"https://api.github.com/repos/{repository}/pulls/{pr_id}/files"
        headers = {"Authorization": f"token {GITHUB_PERSONAL_ACCESS_TOKEN}"}
        repository_deps = {
            "GITHUB_PERSONAL_ACCESS_TOKEN": GITHUB_PERSONAL_ACCESS_TOKEN
        }
    elif platform == "gitlab":
        GITLAB_PERSONAL_ACCESS_TOKEN = os.getenv('GITLAB_TOKEN', '')
        GITLAB_API_URL = os.getenv('GITLAB_API_URL', 'https://gitlab.com/api/v4')
        url = f"{GITLAB_API_URL}/projects/{repository}/merge_requests/{pr_id}/changes"
        headers = {"Private-Token": f"{GITLAB_PERSONAL_ACCESS_TOKEN}"}
        repository_deps = {
            "GITLAB_PERSONAL_ACCESS_TOKEN": GITLAB_PERSONAL_ACCESS_TOKEN,
            "GITLAB_API_URL": GITLAB_API_URL
        }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch pull request files: {response.status_code} {response.text}")
        return 1

    pull_request_files = response.json()
    files = []
    if platform == "github":
        files = pull_request_files
    elif platform == "gitlab":
        files = pull_request_files.get("changes", [])

    # Generate user messages for each file diff
    userMessages = []

    for file in files:
        # Retrieve file name
        filename = ""
        if platform == "github":
            filename = file["filename"]
        elif platform == "gitlab":
            filename = file["new_path"]

        print(f"Processing file: {filename}")
        diff = f"### File : {filename}\n"
        diff += f"### Languages: {', '.join(get_file_languages(filename))}\n"
        diff += "\n"

        # Retrieve patch/diff string
        patch = ""
        if platform == "github":
            patch = file.get("patch", "_No diff available (probably a binary file)._")
        elif platform == "gitlab":
            patch = file.get("diff", "_No diff available (probably a binary file)._")

        # IMPORTANT: Replace all triple backticks with single backticks or escape them
        safePatch = patch.replace('```', "''")
        diff += "```diff\n"
        diff += safePatch
        diff += "\n```\n"

        diff += "\n---\n\n"

        # Construct User prompt message with current diff
        userMessages.append(str(MAIN_USER_PROMPT.format(diff=diff)))

    # ========== Start MCP servers ==========

    # Use AsyncExitStack to manage all MCP servers in one context
    async with AsyncExitStack() as stack:
        # Start all the subagent MCP servers
        print("Starting MCP servers...")
        # Manually run Agents
        await stack.enter_async_context(filesystem_instructions_retriever_agent.run_mcp_servers())
        # Reviewer Agent and its sub-agents
        await stack.enter_async_context(reviewer_agent.run_mcp_servers())
        await stack.enter_async_context(crawl4ai_agent.run_mcp_servers())
        print("All MCP servers started successfully!")

        console = Console()
        try:
            user_custom_instructions = ""
            curr_message = ""
            reviewed_label = "ReviewedByAI"

            with Live("", console=console, vertical_overflow="visible") as live:
                # Retrieve filesystem instructions
                with tracer.start_as_current_span("Filesystem-Instructions-Retrieval-Trace") as span:
                    span.set_attribute("langfuse.user.id", f"pr-{pr_id}")
                    span.set_attribute("langfuse.session.id", repository)

                    curr_message += "**Retrieving filesystem instructions...**\n"
                    live.update(Markdown(curr_message))
                    filesystem_instructions = await filesystem_instructions_retriever_agent.run(FILESYSTEM_INSTRUCTIONS_RETRIEVER_USER_PROMPT)
                    user_custom_instructions = filesystem_instructions.output
                    curr_message += f"**Retrieved filesystem instructions:**\n{user_custom_instructions}\n\n"
                    live.update(Markdown(curr_message))

                    span.set_attribute("input.value", FILESYSTEM_INSTRUCTIONS_RETRIEVER_USER_PROMPT)
                    span.set_attribute("output.value", user_custom_instructions)

                # Reviewer Agent loop on each file diff
                for userMessage in userMessages:
                    with tracer.start_as_current_span("Code-Review-Agent-Trace") as span:
                        span.set_attribute("langfuse.user.id", f"pr-{pr_id}")
                        span.set_attribute("langfuse.session.id", repository)

                        user_input = MAIN_USER_PROMPT.format(custom_instructions=user_custom_instructions, diff=userMessage)
                        reviewer_output = ""
                        curr_message += "**Reviewing new code diff...**\n"
                        live.update(Markdown(curr_message))
                        async with reviewer_agent.run_stream(user_input) as result:
                            async for message in result.stream_text(delta=True):
                                reviewer_output += message
                                curr_message += message
                                live.update(Markdown(curr_message))

                        curr_message += "\n\n---\n\n"
                        curr_message += "**Posting code review to PR/MR...**\n"
                        live.update(Markdown(curr_message))
                        if platform == "github":
                            headers = {
                                "Authorization": f"Bearer {repository_deps['GITHUB_PERSONAL_ACCESS_TOKEN']}",
                                "Accept": "application/vnd.github.v3+json"
                            }
                            data = {
                                "body": reviewer_output
                            }
                            response = requests.post(
                                f"https://api.github.com/repos/{repository}/issues/{pr_id}/comments",
                                headers=headers,
                                json=data
                            )
                            if response.status_code != 201:
                                print(f"\n[Error] Failed to post comment: {response.text}\n")

                            response = requests.post(
                                f"https://api.github.com/repos/{repository}/issues/{pr_id}/labels",
                                headers=headers,
                                json=[{"name": reviewed_label}]
                            )
                            if response.status_code != 200:
                                print(f"\n[Error] Failed to add label: {response.text}\n")
                        elif platform == "gitlab":
                            headers = {
                                "Private-Token": repository_deps['GITLAB_PERSONAL_ACCESS_TOKEN'],
                                "Content-Type": "application/json"
                            }
                            data = {
                                "body": reviewer_output
                            }
                            response = requests.post(
                                f"{repository_deps['GITLAB_API_URL']}/projects/{repository}/merge_requests/{pr_id}/notes",
                                headers=headers,
                                json=data
                            )
                            if response.status_code != 201:
                                print(f"\n[Error] Failed to post comment: {response.text}\n")

                            response = requests.post(
                                f"{repository_deps['GITLAB_API_URL']}/projects/{repository}/merge_requests/{pr_id}/labels",
                                headers=headers,
                                json=[{"name": reviewed_label}]
                            )
                            if response.status_code != 200:
                                print(f"\n[Error] Failed to add label: {response.text}\n")

                        curr_message += f"**Code review posted to PR/MR #{pr_id} and label {reviewed_label} added!**\n\n"
                        live.update(Markdown(curr_message))

                        span.set_attribute("input.value", user_input)
                        span.set_attribute("output.value", curr_message)

        except Exception as e:
            print(f"\n[Error] An error occurred: {str(e)}")
            return 1

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[Info] Code review process interrupted by user.")
    except Exception as e:
        print(f"\n[Error] An unexpected error occurred: {str(e)}")
