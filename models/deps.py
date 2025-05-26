"""Dependency injection models for the code review agent."""
from dataclasses import dataclass
from typing import Any, Optional, Dict
import asyncio
import json
import os
import uuid
import httpx

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

    async def _get_context7_mcp_process(self):
        """Get or start the MCP server process"""
        if self._mcp_process is None or self._mcp_process.returncode is not None:
            # Start the Context7 MCP server
            self._mcp_process = await asyncio.create_subprocess_exec(
                'npx', '-y', '@upstash/context7-mcp',
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            # Wait for the server to be ready
            while True:
                line = await self._mcp_process.stdout.readline()
                if b'Server running' in line:
                    break

        return self._mcp_process

    async def _send_context7_mcp_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send a JSON-RPC request to the MCP server"""
        try:
            proc = await self._get_context7_mcp_process()
            if proc.returncode is not None:
                return {'error': 'MCP server process is not running'}

            # Prepare the JSON-RPC request
            request = {
                'jsonrpc': '2.0',
                'id': str(uuid.uuid4()),
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
        result = await self._send_context7_mcp_request('resolve-library-id', request_params)
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
        result = await self._send_context7_mcp_request('get-library-docs', request_params)
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

    async def _get_brave_mcp_process(self):
        """Get or start the Brave MCP server process"""
        if not hasattr(self, '_brave_mcp_process') or self._brave_mcp_process.poll() is not None:
            # Start the Brave MCP server
            self._brave_mcp_process = await asyncio.create_subprocess_exec(
                'uv', '--directory', 'brave_mcp_search/src', 'run', 'server.py',
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={
                    **os.environ,
                    'BRAVE_API_KEY': os.getenv('BRAVE_API_KEY', '')
                }
            )
            # Wait a moment for the server to start
            await asyncio.sleep(1)
        return self._brave_mcp_process

    async def _send_brave_mcp_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send a JSON-RPC request to the Brave MCP server"""
        try:
            proc = await self._get_brave_mcp_process()
            if proc.returncode is not None:
                return {'error': 'Brave MCP server process is not running'}

            # Prepare the JSON-RPC request
            request = {
                'jsonrpc': '2.0',
                'id': str(uuid.uuid4()),
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
                return {'error': 'No response from Brave MCP server'}

            response = json.loads(line.decode('utf-8').strip())
            if 'error' in response:
                return {'error': response['error']}
            return response.get('result', {})

        except json.JSONDecodeError:
            return {'error': 'Failed to parse Brave MCP server response'}
        except Exception as e:
            return {'error': f'Brave MCP request failed: {str(e)}'}

    async def search_web(self, params: dict) -> dict:
        """Perform a web search using the Brave Search API via MCP server"""
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

            # Prepare search parameters
            search_params = {
                'query': query,
                'count': params.get('count', 5),  # Default to 5 results
                'freshness': params.get('freshness'),
                'country': params.get('country'),
                'search_lang': params.get('search_lang'),
                'ui_lang': params.get('ui_lang'),
                'ui_location': params.get('ui_location'),
                'offset': params.get('offset')
            }

            # Remove None values
            search_params = {k: v for k, v in search_params.items() if v is not None}

            # Send the search request to the Brave MCP server
            result = await self._send_brave_mcp_request('brave_web_search', search_params)

            if 'error' in result:
                return {
                    'error': f'Brave search failed: {result["error"]}',
                    'query': query
                }

            # Format the results to match the expected format
            return {
                'results': result.get('results', []),
                'query': query,
                'count': len(result.get('results', [])),
                'metadata': {
                    'total_results': result.get('total_results', 0)
                }
            }

        except Exception as e:
            return {
                'error': f'Failed to perform web search: {str(e)}',
                'suggestion': 'Check your BRAVE_API_KEY and internet connection',
                'query': params.get('query', '')
            }
