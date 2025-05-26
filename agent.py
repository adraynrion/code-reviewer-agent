from __future__ import annotations as _annotations

import argparse
import asyncio
import os
import sys
import httpx
import logfire
import json

from dataclasses import dataclass
from pydantic_ai import Agent
from typing import Dict, Any
from uuid import uuid4

from agent_tools import (
    get_pr_diff,
    post_review_comment,
    get_review_instructions,
    search_best_practices,
    detect_languages,
    aggregate_review_comments,
)
from agent_prompts import SYSTEM_PROMPT

logfire.configure(send_to_logfire='if-token-present')

@dataclass
class ReviewDeps:
    """Dependency holder for API clients, config for GitHub/GitLab and MCP tools"""
    http_client: httpx.AsyncClient
    platform: str  # 'github' or 'gitlab'
    github_token: str | None
    gitlab_token: str | None
    repository: str
    pr_id: int
    instructions_path: str
    log_level: str
    openai_api_key: str  # OpenAI API key for the agent to use
    agent: Any  # The agent instance that will handle LLM interactions

    def __post_init__(self):
        """Initialize the MCP server process"""
        self._mcp_process = None
        self._request_id = 0
        self._mcp_brave = None  # Will be initialized lazily if needed

    async def _get_mcp_process(self):
        """Get or start the MCP server process"""
        if self._mcp_process is None or self._mcp_process.returncode is not None:
            # Start the Context7 MCP server
            self._mcp_process = await asyncio.create_subprocess_exec(
                'npx', '-y', '@upstash/context7-mcp',
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            # Wait a moment for the server to start
            await asyncio.sleep(1)
        return self._mcp_process

    async def _send_mcp_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send a JSON-RPC request to the MCP server"""
        try:
            proc = await self._get_mcp_process()
            if proc.returncode is not None:
                return {'error': 'MCP server process is not running'}

            # Prepare the JSON-RPC request
            request = {
                'jsonrpc': '2.0',
                'id': str(uuid4()),
                'method': method,
                'params': params
            }

            # Send the request
            request_json = json.dumps(request) + '\n'
            proc.stdin.write(request_json.encode('utf-8'))
            await proc.stdin.drain()

            # Read the response
            line = await proc.stdout.readline()
            if not line:
                return {'error': 'No response from MCP server'}

            response = json.loads(line.decode('utf-8').strip())
            if 'error' in response:
                return {'error': response['error']}
            return response.get('result', {})

        except json.JSONDecodeError:
            return {'error': 'Failed to parse MCP server response'}
        except Exception as e:
            return {'error': f'MCP request failed: {str(e)}'}

    # MCP Tool methods
    async def resolve_library_id(self, params: dict) -> dict:
        """Resolve a library name to its Context7 ID"""
        if 'libraryName' not in params:
            return {'error': 'libraryName parameter is required'}

        # Prepare the request parameters
        request_params = {
            'name': params['libraryName']
        }
        if 'version' in params:
            request_params['version'] = params['version']

        # Send the request to the MCP server
        result = await self._send_mcp_request('resolve-library-id', request_params)
        if 'error' in result:
            return result

        # Format the result to match the expected format
        return {
            'libraries': [
                {
                    'id': result.get('id', ''),
                    'name': params['libraryName'],
                    'version': request_params.get('version', 'latest')
                }
            ]
        }

    async def get_library_docs(self, params: dict) -> dict:
        """Retrieve documentation from Context7"""
        required_params = ['context7CompatibleLibraryID']
        for param in required_params:
            if param not in params:
                return {'error': f'{param} parameter is required'}

        # Prepare the request parameters
        request_params = {
            'library_id': params['context7CompatibleLibraryID']
        }
        if 'tokens' in params:
            request_params['tokens'] = params['tokens']
        if 'topic' in params:
            request_params['topic'] = params['topic']

        # Send the request to the MCP server
        result = await self._send_mcp_request('get-library-docs', request_params)
        if 'error' in result:
            return result

        # Format the result to match the expected format
        return {
            'content': result.get('content', ''),
            'metadata': {
                'library_id': params['context7CompatibleLibraryID'],
                'tokens': request_params.get('tokens', 10000)
            }
        }

    async def search_web(self, params: dict) -> dict:
        """Perform a web search using the Brave Search API"""
        try:
            # Check if we have a Brave API key
            brave_api_key = os.getenv('BRAVE_API_KEY')
            if not brave_api_key:
                return {
                    'error': 'BRAVE_API_KEY environment variable is not set',
                    'suggestion': 'Please set the BRAVE_API_KEY environment variable to enable web search'
                }

            # Extract query and other parameters
            query = params.get('query')
            if not query:
                return {'error': 'query parameter is required'}

            # For now, return a placeholder response
            # TODO: In a real implementation, you would make an HTTP request to the Brave Search API
            return {
                'error': 'Brave Search API integration not implemented',
                'suggestion': 'Implement the Brave Search API integration using the BRAVE_API_KEY',
                'query': query,
                'results': []
            }

        except Exception as e:
            return {
                'error': f'Failed to perform web search: {str(e)}',
                'suggestion': 'Check your BRAVE_API_KEY and internet connection'
            }

# Agent will be created in the main function with the proper dependencies

def parse_arguments():
    parser = argparse.ArgumentParser(description='AI Code Review Agent')
    parser.add_argument(
        '--pr-id',
        type=int,
        required=True,
        help='Pull/Merge Request ID to review'
    )
    parser.add_argument(
        '--repository',
        type=str,
        help='Repository in format owner/repo (overrides REPOSITORY env var)'
    )
    parser.add_argument(
        '--platform',
        type=str,
        choices=['github', 'gitlab'],
        help='Platform: github or gitlab (overrides PLATFORM env var)'
    )
    parser.add_argument(
        '--instructions',
        type=str,
        default='review_instructions.md',
        help='Path to custom review instructions file (default: review_instructions.md)'
    )
    parser.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help='Logging level (default: INFO)'
    )
    return parser.parse_args()

async def main():
    args = parse_arguments()

    github_token = os.getenv('GITHUB_TOKEN')
    gitlab_token = os.getenv('GITLAB_TOKEN')
    platform = args.platform or os.getenv('PLATFORM', 'github').lower()
    repository = args.repository or os.getenv('REPOSITORY')
    pr_id = args.pr_id
    instructions_path = args.instructions
    log_level = args.log_level

    if not repository:
        print("Error: Repository not specified. Use --repository or set REPOSITORY environment variable")
        sys.exit(1)

    if platform not in ('github', 'gitlab'):
        print("Error: Invalid platform. Must be either 'github' or 'gitlab'")
        sys.exit(1)

    if platform == 'github' and not github_token:
        print("Error: GITHUB_TOKEN environment variable is required when platform is 'github'")
        sys.exit(1)

    if platform == 'gitlab' and not gitlab_token:
        print("Error: GITLAB_TOKEN environment variable is required when platform is 'gitlab'")
        sys.exit(1)

    print(f"Starting code review for {platform.upper()} PR #{pr_id} in {repository}")

    async with httpx.AsyncClient() as http_client:
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if not openai_api_key:
            print("Error: OPENAI_API_KEY environment variable is required")
            sys.exit(1)

        # Create the agent instance with the base system prompt
        # The actual system prompt with custom_instructions and best_practices will be set in analyze_with_llm
        agent = Agent(
            "openai:gpt-4.1-mini", # [LLM]: Use OpenAI "Codex" LLM (or similar) for code analysis
            system_prompt=SYSTEM_PROMPT,
            deps_type=ReviewDeps,
            retries=2,
        )

        # Register tools
        agent.add_tool(get_pr_diff)
        agent.add_tool(post_review_comment)
        agent.add_tool(get_review_instructions)
        agent.add_tool(search_best_practices)
        agent.add_tool(detect_languages)
        agent.add_tool(aggregate_review_comments)

        # Create dependencies with the agent
        deps = ReviewDeps(
            http_client=http_client,
            platform=platform,
            github_token=github_token,
            gitlab_token=gitlab_token,
            repository=repository,
            pr_id=pr_id,
            instructions_path=instructions_path,
            log_level=log_level,
            openai_api_key=openai_api_key,
            agent=agent
        )

        # Run the agent
        await agent.run("Review this pull request", deps=deps)

if __name__ == "__main__":
    asyncio.run(main())
