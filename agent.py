import argparse
import asyncio
import os

from dotenv import load_dotenv
from agent_prompts import REVIEW_PROMPT
from contextlib import AsyncExitStack

from rich.markdown import Markdown
from rich.console import Console
from rich.live import Live

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.mcp import MCPServerStdio

from configure_langfuse import configure_langfuse

load_dotenv()

# Configure Langfuse for agent observability
tracer = configure_langfuse()

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

# ========== Helper function to get model configuration ==========
def get_model():
    llm = os.getenv('MODEL_CHOICE', 'gpt-4.1-mini')
    base_url = os.getenv('BASE_URL', 'https://api.openai.com/v1')
    api_key = os.getenv('LLM_API_KEY', 'no-api-key-provided')

    return OpenAIModel(llm, provider=OpenAIProvider(base_url=base_url, api_key=api_key))

# ========== Set up MCP servers for each service ==========

# Brave Search MCP server
brave_server = MCPServerStdio(
    'npx', ['-y', '@modelcontextprotocol/server-brave-search'],
    env={"BRAVE_API_KEY": os.getenv('BRAVE_API_KEY', '')}
)

# Filesystem MCP server
filesystem_server = MCPServerStdio(
    'npx', ['-y', '@modelcontextprotocol/server-filesystem', os.getenv('LOCAL_FILE_DIR', '')]
)

git_platform = os.getenv('PLATFORM', 'github')
repository_server = None
if git_platform == 'github':
    # GitHub MCP server
    repository_server = MCPServerStdio(
        'npx', ['-y', '@modelcontextprotocol/server-github'],
        env={"GITHUB_PERSONAL_ACCESS_TOKEN": os.getenv('GITHUB_TOKEN', '')}
    )
elif git_platform == 'gitlab':
    # Gitlab MCP server
    repository_server = MCPServerStdio(
        'npx', ['-y', '@modelcontextprotocol/server-gitlab'],
        env={
            "GITLAB_PERSONAL_ACCESS_TOKEN": os.getenv('GITLAB_TOKEN', ''),
            "GITLAB_API_URL": os.getenv('GITLAB_API_URL', 'https://gitlab.com/api/v4'),
        }
    )

# Firecrawl MCP server
firecrawl_server = MCPServerStdio(
    'npx', ['-y', 'firecrawl-mcp'],
    env={"FIRECRAWL_API_KEY": os.getenv('FIRECRAWL_API_KEY', '')}
)

# ========== Create subagents with their MCP servers ==========

# Brave search agent
brave_agent = Agent(
    get_model(),
    system_prompt="You are a web search specialist using Brave Search. Find relevant information on the web.",
    mcp_servers=[brave_server],
    instrument=True
)

# Filesystem agent
filesystem_agent = Agent(
    get_model(),
    system_prompt="You are a filesystem specialist. You retrieve all the files content in the directory of the User to provide complementary instructions for the code review.",
    mcp_servers=[filesystem_server],
    instrument=True
)

# Repository agent
repository_agent = Agent(
    get_model(),
    system_prompt=(
        "You are a GitHub/GitLab specialist. Help users interact with its repositories and features.",
        "You are the only one able to create the issue(s) on the PR/MR following the code review."
    ),
    mcp_servers=[repository_server],
    instrument=True
)

# Firecrawl agent
firecrawl_agent = Agent(
    get_model(),
    system_prompt="You are a web crawling specialist. Help users extract data from websites.",
    mcp_servers=[firecrawl_server],
    instrument=True
)

# ========== Create the code reviewer agents ==========
review_agent = Agent(
    get_model(),
    system_prompt=REVIEW_PROMPT,
    instrument=True
)

# ========== Create the primary orchestration agent ==========
primary_agent = Agent(
    get_model(),
    system_prompt="""You are a primary orchestration agent that can call upon specialized subagents
    to perform various tasks. Each subagent is an expert in interacting with a specific third-party service.
    Analyze the user request and delegate the work to the appropriate subagent.""",
    instrument=True
)

# ========== Define tools for the primary agent to call subagents ==========
@primary_agent.tool_plain
async def use_brave_search_agent(query: str) -> dict[str, str]:
    """
    Search the web using Brave Search through the Brave subagent.
    Use this tool when the user needs to find information on the internet or research a topic.

    Args:
        ctx: The run context.
        query: The search query or instruction for the Brave search agent.

    Returns:
        The search results or response from the Brave agent.
    """
    print(f"Calling Brave agent with query: {query}")
    result = await brave_agent.run(query)
    return {"result": result.data}

@primary_agent.tool_plain
async def use_filesystem_agent(query: str) -> dict[str, str]:
    """
    Interact with the file system through the filesystem subagent.
    Use this tool when the user needs to read, write, list, or modify files.

    Args:
        ctx: The run context.
        query: The instruction for the filesystem agent.

    Returns:
        The response from the filesystem agent.
    """
    print(f"Calling Filesystem agent with query: {query}")
    result = await filesystem_agent.run(query)
    return {"result": result.data}

@primary_agent.tool_plain
async def use_git_repository_agent(query: str) -> dict[str, str]:
    """
    Interact with GitHub or GitLab through the Git repository subagent.
    Use this tool when the user needs to access repositories, issues, PRs, or other Git resources.

    Args:
        ctx: The run context.
        query: The instruction for the Git repository agent.

    Returns:
        The response from the Git repository agent.
    """
    print(f"Calling Git repository agent with query: {query}")
    result = await repository_agent.run(query)
    return {"result": result.data}

@primary_agent.tool_plain
async def use_firecrawl_agent(query: str) -> dict[str, str]:
    """
    Crawl and analyze websites using the Firecrawl subagent.
    Use this tool when the user needs to extract data from websites or perform web scraping.

    Args:
        ctx: The run context.
        query: The instruction for the Firecrawl agent.

    Returns:
        The response from the Firecrawl agent.
    """
    print(f"Calling Firecrawl agent with query: {query}")
    result = await firecrawl_agent.run(query)
    return {"result": result.data}

@primary_agent.tool_plain
async def use_reviewer_agent(query: str) -> dict[str, str]:
    """
    Review any diff of code using the reviewer subagent.
    Use this tool when the user needs to review a diff of code.

    Args:
        ctx: The run context.
        query: The instruction for the reviewer agent.

    Returns:
        The response from the reviewer agent.
    """
    print(f"Calling Reviewer agent with query: {query}")
    result = await review_agent.run(query)
    return {"result": result.data}

# ========== Main execution function ==========

async def main():
    """Main entry point for the code review agent."""
    args = parse_arguments()

    platform = args.platform or git_platform
    repository = args.repository or os.getenv('REPOSITORY', '')
    pr_id = args.pr_id

    instructions_path = args.instructions_path

    print((
        f"Starting code review for {platform.upper()} PR #{pr_id} in {repository}.",
        f"Instructions path: {instructions_path}.",
    ))

    # ========== Validate inputs ==========

    if platform not in ('github', 'gitlab'):
        print("Invalid platform. Must be either 'github' or 'gitlab'")
        return 1

    if platform == 'github' and not os.getenv('GITHUB_TOKEN', ''):
        print("GITHUB_TOKEN environment variable is required when platform is 'github'")
        return 1

    if platform == 'gitlab' and not os.getenv('GITLAB_TOKEN', ''):
        print("GITLAB_TOKEN environment variable is required when platform is 'gitlab'")
        return 1

    if not repository:
        print("Repository not specified. Use --repository or set REPOSITORY environment variable")
        return 1

    # ========== Start MCP servers ==========

    # Use AsyncExitStack to manage all MCP servers in one context
    async with AsyncExitStack() as stack:
        # Start all the subagent MCP servers
        print("Starting MCP servers...")
        await stack.enter_async_context(brave_agent.run_mcp_servers())
        await stack.enter_async_context(filesystem_agent.run_mcp_servers())
        await stack.enter_async_context(repository_agent.run_mcp_servers())
        await stack.enter_async_context(firecrawl_agent.run_mcp_servers())
        await stack.enter_async_context(review_agent.run_mcp_servers())
        print("All MCP servers started successfully!")

        console = Console()
        user_input = f"Review pull request #{pr_id} in {repository} and create issues on it following the code review."

        try:
            # Configure the metadata for the Langfuse tracing
            with tracer.start_as_current_span("Code-Review-Agent-Trace") as span:
                span.set_attribute("langfuse.user.id", f"user-{pr_id}")
                span.set_attribute("langfuse.session.id", "1111" if platform == 'github' else "2222")

                print("\n[Assistant]")
                curr_message = ""
                with Live('', console=console, vertical_overflow='visible') as live:
                    async with primary_agent.run_stream(user_input) as result:
                        async for message in result.stream_text(delta=True):
                            curr_message += message
                            live.update(Markdown(curr_message))

                span.set_attribute("input.value", user_input)
                span.set_attribute("output.value", curr_message)

        except Exception as e:
            print(f"\n[Error] An error occurred: {str(e)}")
            return 1

if __name__ == "__main__":
    asyncio.run(main())
