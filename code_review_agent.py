import argparse
import asyncio
import os

from dotenv import load_dotenv
from agent_prompts import MANAGER_PROMPT, USER_PROMPT, REVIEW_PROMPT
from contextlib import AsyncExitStack
from agent_model import get_model

from rich.markdown import Markdown
from rich.console import Console
from rich.live import Live

from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio

from configure_langfuse import configure_langfuse

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
    'npx', ['-y', '@modelcontextprotocol/server-filesystem', os.getenv('LOCAL_FILE_DIR', '')]
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
    }
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

# Repository agent
repository_agent = Agent(
    get_model(),
    system_prompt=(
        "You are a GitHub/GitLab specialist. Help users interact with its repositories and features. You are the only one able to create the issue(s) on the PR/MR following the code review."
    ),
    mcp_servers=[] if repository_server is None else [repository_server],
    instrument=True
)
if repository_server is None:
    raise ValueError("Invalid platform. Must be either 'github' or 'gitlab'")

# ========== Create the code reviewer agents ==========
contextual_chunk_writer_agent = Agent(
    get_model(),
    system_prompt=f"""
        You are a contextual chunk writer agent. Help split the file diff by chunks of ~{chunk_size} tokens with additional context for the next agents processing.
        The user will provide the whole document to split into chunks.
        Please give a short succinct context to situate this chunk within the overall document for the purposes of improving understanding of the chunk.
        Answer only with the chunks of the document with the additional context for each chunk and nothing else.
    """,
    instrument=True
)
reviewer_agent = Agent(
    get_model(),
    system_prompt=REVIEW_PROMPT,
    instrument=True
)

# ========== Create the primary orchestration agent ==========
primary_agent = Agent(
    get_model(),
    system_prompt=MANAGER_PROMPT,
    instrument=True
)

# ========== Define tools for the primary agent to call subagents ==========

@primary_agent.tool_plain
async def use_filesystem_instructions_retriever_agent(query: str) -> dict[str, str]:
    """
    Interact with the filesystem instructions retriever agent.
    Use this tool to list and retrieve all the files content in the instructions folder.

    Args:
        ctx: The run context.
        query: The instruction for the filesystem instructions retriever agent.

    Returns:
        The response from the filesystem instructions retriever agent.
    """
    print(f"Calling filesystem instructions retriever agent with query: {query}")
    result = await filesystem_instructions_retriever_agent.run(query)
    return {"result": result.data}

@primary_agent.tool_plain
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
    return {"result": result.data}

@primary_agent.tool_plain
async def use_git_repository_agent(query: str) -> dict[str, str]:
    """
    Interact with GitHub or GitLab through the Git repository subagent.
    Use this tool when the user needs to access repositories, issues, PRs, or other Git resources.
    Additionnally, this tool can be used to create issues on the PR/MR following the code review.

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
async def use_contextual_chunk_writer_agent(query: str) -> dict[str, str]:
    f"""
    Use this tool to split the file diff by chunks of ~{chunk_size} tokens with additional context for the next agents processing.

    Args:
        ctx: The run context.
        query: The whole file content to split into chunks.

    Returns:
        The chunks of the file content with additional context for each chunk.
    """
    print(f"Calling Contextual Chunk Writer agent with query: {query}")
    result = await contextual_chunk_writer_agent.run(query)
    return {"result": result.data}

@primary_agent.tool_plain
async def use_reviewer_agent(query: str) -> dict[str, str]:
    """
    Use this tool to review any code diff using the reviewer subagent.
    Compile the file name, the code diff, the custom user instructions and the code language documentation to review the code diff.

    Args:
        ctx: The run context.
        query: The instruction for the reviewer agent.

    Returns:
        The response from the reviewer agent.
    """
    print(f"Calling Reviewer agent with query: {query}")
    result = await reviewer_agent.run(query)
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
        await stack.enter_async_context(filesystem_instructions_retriever_agent.run_mcp_servers())
        await stack.enter_async_context(crawl4ai_agent.run_mcp_servers())
        await stack.enter_async_context(repository_agent.run_mcp_servers())
        await stack.enter_async_context(contextual_chunk_writer_agent.run_mcp_servers())
        await stack.enter_async_context(reviewer_agent.run_mcp_servers())
        print("All MCP servers started successfully!")

        console = Console()
        user_input = USER_PROMPT.format(pr_id=pr_id, repository=repository)

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
