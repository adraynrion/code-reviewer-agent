import argparse
import asyncio
import os

from dotenv import load_dotenv

from rich.markdown import Markdown
from rich.console import Console
from rich.live import Live

from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio

from configure_langfuse import configure_langfuse
from agent_model import get_model

load_dotenv()

# Configure Langfuse for agent observability
tracer = configure_langfuse()

def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Crawler Agent')
    parser.add_argument('--doc-url', type=str, required=True,
                       help='URL of the documentation to crawl')
    parser.add_argument('--mode', type=str, choices=['full', 'single-page'], default='single-page',
                       help='Force the crawling of the only page sent (single-page - default) or will follow all the links of the page (full)')
    return parser.parse_args()

# ========== Set up MCP servers for each service ==========

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

# ========== Create subagents with their MCP servers ==========

# Crawl4ai agent
crawl4ai_agent = Agent(
    get_model(),
    system_prompt="You are a crawler agent. Help fill the vector database with the documentation website.",
    mcp_servers=[crawl4ai_server],
    instrument=True
)

# ========== Main execution function ==========

async def main():
    """Main entry point for the crawler agent."""
    args = parse_arguments()

    doc_url = args.doc_url
    mode = args.mode

    print((
        f"Starting crawler agent for {doc_url}.",
    ))

    # ========== Start MCP servers ==========

    async with crawl4ai_agent.run_mcp_servers():
        console = Console()
        user_input = f"Fill the vector database with the documentation website at {doc_url}."
        if mode == 'single-page':
            user_input += f" You must only crawl the website page sent by the user and NO OTHER pages."
        else:
            user_input += " You must crawl all the pages linked from the website page sent by the user."

        try:
            # Configure the metadata for the Langfuse tracing
            with tracer.start_as_current_span("Crawler-Agent-Trace") as span:
                span.set_attribute("langfuse.user.id", "user-crawler")
                span.set_attribute("langfuse.session.id", "0001")

                print("\n[Assistant]")
                curr_message = ""
                with Live('', console=console, vertical_overflow='visible') as live:
                    async with crawl4ai_agent.run_stream(user_input) as result:
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
