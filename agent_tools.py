"""Tools for the code review agent to interact with GitHub/GitLab and analyze code."""

import asyncio
import json
import logging
import random
import time
import traceback
from typing import Any, Dict, List, Optional
from pydantic_ai import RunContext
from models import FileDiff, ReviewComment, PRDiffResponse
from models.deps import ReviewDeps
from langfuse_integration import get_langfuse_tracer
from langfuse_decorators import track_llm, track_tool

# Configure logger
logger = logging.getLogger(__name__)

# Don't add handlers here - they'll be added by the main application
# This prevents duplicate log messages when the module is imported multiple times
if not logger.handlers:
    console = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console.setFormatter(formatter)
    logger.addHandler(console)

def log_info(message: str):
    """Log an info message to the logger."""
    logger.info(message)

def log_error(message: str, exc_info=None):
    """Log an error message to the logger."""
    logger.error(message, exc_info=exc_info)

@track_tool(name="parse_unified_diff", metadata={"component": "diff_parsing"})
def parse_unified_diff(diff_text: str) -> List[Dict[str, Any]]:
    """
    Parse a GitHub-provided unified diff into structured file diffs.

    Args:
        diff_text: The unified diff text from GitHub

    Returns:
        List of parsed file diffs with metadata
    """
    log_info("Starting to parse unified diff")
    log_info(f"Diff text size: {len(diff_text)} characters")

    # Log first 500 chars of diff for debugging
    log_info(f"Diff preview (first 500 chars):\n{diff_text[:500]}...")
    log_info(f"Diff ends with: ...{diff_text[-100:] if len(diff_text) > 100 else diff_text}")

    if not diff_text.strip():
        log_error("Empty diff text received")

    files = []
    current_file = None
    splited_diff_text = diff_text.split('\n')
    file_count = 0

    for line in splited_diff_text:
        # Start of a new file diff
        if line.startswith('diff --git'):
            # Process previous file if exists
            if current_file is not None:
                if 'patch' in current_file and isinstance(current_file['patch'], list):
                    current_file['patch'] = '\n'.join(current_file['patch'])
                files.append(current_file)
                file_count += 1
                log_info(f"Completed processing file {file_count}: {current_file.get('filename', 'unknown')} "
                       f"({current_file.get('status', 'unknown')} - {len(current_file.get('patch', '').splitlines())} lines)")

            # Extract old and new file paths
            parts = line.split()
            old_path = parts[2][2:]  # Skip 'a/'
            new_path = parts[3][2:]  # Skip 'b/'

            # Determine file status
            status = 'modified'
            if old_path == '/dev/null':
                status = 'added'
            elif new_path == '/dev/null':
                status = 'deleted'

            # Determine filename
            filename = old_path
            if new_path != '/dev/null':
                filename = new_path

            # Determine previous filename
            previous_filename = None
            if old_path != '/dev/null':
                previous_filename = old_path

            # Initialize new file
            current_file = {
                'filename': filename,
                'status': status,
                'patch': []
            }
            log_info(f"Starting to process file: {new_path} (status: {status})")

            current_file['previous_filename'] = previous_filename
            current_file['additions'] = 0
            current_file['deletions'] = 0
            current_file['is_binary'] = False

            # Check for binary file indicator in the next 5 lines
            next_lines = splited_diff_text[splited_diff_text.index(line) + 1:splited_diff_text.index(line) + 5]
            for l in next_lines:
                if 'binary' in l.lower():
                    current_file['is_binary'] = True
                    break



        # Parse diff metadata
        elif line.startswith('index ') and current_file:
            # Extract SHAs if available (format: index <base-sha>..<head-sha> <mode>)
            parts = line.split()
            if '..' in parts[1]:
                base_sha, head_sha = parts[1].split('..')[:2]
                current_file['base_sha'] = base_sha
                current_file['head_sha'] = head_sha

        # Parse hunk headers
        elif line.startswith('@@ ') and current_file and not current_file['is_binary']:
            current_file['patch'].append(line)

        # Parse added/removed lines
        elif current_file and not current_file['is_binary']:
            if line.startswith('+') and not line.startswith('+++'):
                current_file['additions'] += 1
                current_file['patch'].append(line)
            elif line.startswith('-') and not line.startswith('---'):
                current_file['deletions'] += 1
                current_file['patch'].append(line)
            elif line.startswith(' '):
                current_file['patch'].append(line)

    # Add the last file if exists
    if current_file is not None:
        if 'patch' in current_file and isinstance(current_file['patch'], list):
            current_file['patch'] = '\n'.join(current_file['patch'])
        files.append(current_file)
        file_count += 1
        log_info(f"Completed processing final file: {current_file.get('filename', 'unknown')} "
               f"({current_file.get('status', 'unknown')} - {len(current_file.get('patch', '').splitlines())} lines)")

    log_info(f"Successfully parsed {file_count} files from diff")
    log_info(f"Total chunks in diff: {len([f for f in files if 'patch' in f])}")

    # Log summary of parsed files
    if files:
        log_info("Parsed files summary:")
        for i, f in enumerate(files, 1):
            log_info(f"  {i}. {f.get('filename', 'unknown')} ({f.get('status', 'unknown')}) - "
                   f"{len(f.get('patch', '').splitlines())} lines")
    else:
        log_info("No files were parsed from the diff")

    return files

@track_tool(name="get_pr_diff", metadata={"component": "git_client"})
async def get_pr_diff(
    context: RunContext[ReviewDeps],
    repository: str,
    pr_id: int,
    max_files: int = 20,
    max_chunk_size: int = 5000,
    deps: Optional[ReviewDeps] = None,
) -> PRDiffResponse:
    # Use deps from context if not provided directly
    if deps is None and hasattr(context, 'deps'):
        deps = context.deps
    log_info(f"Fetching PR diff for repository: {repository}, PR: {pr_id}")
    """
    Get the diff for a pull request, handling large PRs by processing in chunks.

    Args:
        context: The dependency injection container
        repository: The repository in format 'owner/repo' or 'group/project' for GitLab
        pr_id: The pull/merge request number
        max_files: Maximum number of files to process in one go (reduced to 20 to avoid rate limits)
        max_chunk_size: Maximum diff size in characters per chunk (reduced to 5000 to avoid rate limits)

    Returns:
        PRDiffResponse containing the diff information
    """
    try:
        # Use deps from context if not provided directly
        if deps is None and hasattr(context, 'deps'):
            deps = context.deps

        if deps is None:
            raise ValueError("No dependencies provided. Please ensure the agent is initialized with the correct dependencies.")

        platform = deps.platform if hasattr(deps, 'platform') else 'github'  # Default to github if not specified

        # Add delay to respect rate limits
        await asyncio.sleep(2)

        if platform == 'github':
            log_info("Using GitHub platform")
            # First, get the PR details to get the base and head SHAs
            pr_url = f"https://api.github.com/repos/{repository}/pulls/{pr_id}"
            headers = {
                "Authorization": f"token {deps.github_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            log_info(f"Fetching PR details from: {pr_url}")

            # Get PR details
            pr_response = await deps.http_client.get(pr_url, headers=headers)
            log_info(f"PR details response status: {pr_response.status_code}")

            if pr_response.status_code != 200:
                log_error(f"Failed to fetch PR details: {pr_response.text}")
                pr_response.raise_for_status()

            pr_data = pr_response.json()

            # Get the list of files in the PR to process in chunks
            files_url = f"https://api.github.com/repos/{repository}/pulls/{pr_id}/files?per_page={max_files}"
            log_info(f"Fetching PR files from: {files_url}")
            files_response = await deps.http_client.get(files_url, headers=headers)
            if files_response.status_code != 200:
                log_error(f"Failed to fetch file list: {files_response.text}")
                files_response.raise_for_status()

            files_data = files_response.json()
            total_files = len(files_data)
            log_info(f"Found {total_files} files in PR #{pr_id}")

            # Process files in chunks
            all_files = []
            current_chunk = []
            current_chunk_size = 0

            for file_data in files_data:
                file_size = file_data.get('additions', 0) + file_data.get('deletions', 0)

                # If adding this file would exceed our chunk size, process the current chunk
                if current_chunk and (len(current_chunk) >= max_files or
                                    current_chunk_size + file_size > max_chunk_size):
                    all_files.append(current_chunk)
                    current_chunk = []
                    current_chunk_size = 0

                current_chunk.append(file_data['filename'])
                current_chunk_size += file_size

            # Add the last chunk if not empty
            if current_chunk:
                all_files.append(current_chunk)

            log_info(f"Split PR into {len(all_files)} chunks for processing")
            base_sha = pr_data.get('base', {}).get('sha')
            head_sha = pr_data.get('head', {}).get('sha')

            if not base_sha or not head_sha:
                log_error(f"Missing SHA information in PR data: {pr_data}")
                raise ValueError("Missing base or head SHA in PR data")

            log_info(f"Base SHA: {base_sha}, Head SHA: {head_sha}")

            # Process each chunk of files
            all_parsed_files = []

            for chunk_idx, file_chunk in enumerate(all_files, 1):
                log_info(f"Processing chunk {chunk_idx}/{len(all_files)} with {len(file_chunk)} files")

                # Get the diff for this chunk of files
                diff_url = f"https://api.github.com/repos/{repository}/pulls/{pr_id}"
                diff_headers = {
                    **headers,
                    "Accept": "application/vnd.github.v3.diff"
                }

                # Add per_page parameter to limit the number of files
                params = {
                    'per_page': max_files,
                    'page': 1
                }

                # Fetch the diff for this chunk
                log_info(f"Fetching diff for chunk {chunk_idx} with {len(file_chunk)} files")
                diff_response = await deps.http_client.get(
                    diff_url,
                    headers=diff_headers,
                    params=params
                )

                if diff_response.status_code != 200:
                    log_error(f"Failed to fetch diff for chunk {chunk_idx}: {diff_response.text}")
                    diff_response.raise_for_status()

                diff_text = diff_response.text
                log_info(f"Successfully fetched diff for chunk {chunk_idx}, size: {len(diff_text)} bytes")

                # Parse the diff for this chunk
                parsed_files = parse_unified_diff(diff_text)
                all_parsed_files.extend(parsed_files)

                # Be nice to the API - add a small delay between chunks
                if chunk_idx < len(all_files):
                    await asyncio.sleep(1)

            log_info(f"Completed processing all {len(all_parsed_files)} files across {len(all_files)} chunks")

            # Calculate total lines across all chunks
            total_lines = sum(f.get('additions', 0) + f.get('deletions', 0) for f in all_parsed_files)
            log_info(f"Parsed {len(all_parsed_files)} files with {total_lines} total lines changed")

            # Convert dictionaries to FileDiff objects
            file_diffs = []
            for f in all_parsed_files:
                try:
                    file_diff = FileDiff(
                        filename=f['filename'],
                        status=f['status'],
                        additions=f.get('additions', 0),
                        deletions=f.get('deletions', 0),
                        patch=f.get('patch', ''),
                        previous_filename=f.get('previous_filename')
                    )
                    file_diffs.append(file_diff)
                except KeyError as e:
                    log_error(f"Error creating FileDiff for {f.get('filename', 'unknown')}: {e}")
                    continue

            # Create the response with all parsed files
            return PRDiffResponse(
                files=file_diffs,
                base_sha=base_sha,
                head_sha=head_sha
            )
        else:  # GitLab
            log_info("GitLab integration not yet implemented")
            # TODO: Implement GitLab integration
            return PRDiffResponse(files=[], base_sha='', head_sha='')

    except Exception as e:
        log_error(f"Error in get_pr_diff: {str(e)}", exc_info=True)
        raise

@track_tool(name="post_review_comment", metadata={"component": "code_review_poster"})
async def post_review_comment(
    context: RunContext[ReviewDeps],
    repository: str,
    pr_id: int,
    comments: List[ReviewComment],
    deps: ReviewDeps = None,  # Dependencies injected by the agent
) -> bool:
    # Use deps from context if not provided directly
    if deps is None and hasattr(context, 'deps'):
        deps = context.deps
    log_info(f"Posting {len(comments)} review comments to {repository} PR #{pr_id}")
    """
    Post review comments to a pull request.

    Args:
        context: The dependency injection container
        repository: The repository in format 'owner/repo' or 'group/project' for GitLab
        pr_id: The pull/merge request number
        comments: List of comments to post

    Returns:
        bool: True if comments were posted successfully
    """
    # Get Langfuse tracer for tracking
    tracer = get_langfuse_tracer()
    start_time = time.time()

    # Track comment statistics
    stats = {
        "total_comments": len(comments),
        "platform": context.deps.platform,
        "repository": repository,
        "pr_id": pr_id,
        "success": False,
        "error": None
    }

    try:
        if context.deps.platform == 'github':
            url = f"https://api.github.com/repos/{repository}/pulls/{pr_id}/reviews"
            headers = {
                "Authorization": f"token {context.deps.github_token}",
                "Accept": "application/vnd.github.v3+json"
            }

            github_comments = []
            for comment in comments:
                github_comments.append({
                    "path": comment.path,
                    "position": comment.line,
                    "body": comment.body,
                    "side": "RIGHT"
                })

            payload = {
                "event": "COMMENT",
                "comments": github_comments
            }

            # Log the API call
            if tracer and tracer.trace:
                tracer.log_event(
                    name="github_api_call_start",
                    metadata={
                        "url": url,
                        "num_comments": len(github_comments),
                        "headers": {k: "[REDACTED]" if k.lower() == "authorization" else v
                                  for k, v in headers.items()}
                    }
                )

            response = await context.deps.http_client.post(url, headers=headers, json=payload)
            response.raise_for_status()

            stats["success"] = True
            return True

        else:  # GitLab
            # TODO: Similar implementation for GitLab
            if tracer and tracer.trace:
                tracer.log_event(
                    name="gitlab_not_implemented",
                    metadata={"message": "GitLab integration not yet implemented"}
                )
            return False

    except Exception as e:
        error_msg = str(e)
        stats["error"] = error_msg
        logger.error(f"Failed to post review comments: {error_msg}", exc_info=True)

        # Log the error to Langfuse
        if tracer and tracer.trace:
            tracer.log_event(
                name="post_comments_error",
                metadata={
                    "error_type": type(e).__name__,
                    "error_message": error_msg,
                    "stack_trace": traceback.format_exc()
                }
            )

        raise

    finally:
        # Log completion metrics
        if tracer and tracer.trace:
            duration = time.time() - start_time
            tracer.log_event(
                name="post_comments_complete",
                metadata={
                    **stats,
                    "duration_seconds": duration,
                    "comments_per_second": len(comments) / duration if duration > 0 else 0
                }
            )

@track_tool(name="get_review_instructions", metadata={"component": "file_io"})
async def get_review_instructions(
    context: RunContext[ReviewDeps],
    instructions_path: str,
    deps: ReviewDeps = None,  # Dependencies injected by the agent
) -> str:
    # Use deps from context if not provided directly
    if deps is None and hasattr(context, 'deps'):
        deps = context.deps
    log_info(f"Loading review instructions from: {instructions_path}")
    """
    Load custom review instructions from a markdown file.

    Args:
        context: The dependency injection container
        instructions_path: Path to the markdown file with review instructions

    Returns:
        str: The contents of the instructions file
    """
    try:
        with open(instructions_path, 'r') as f:
            return f.read()
    except Exception as e:
        print(f"Warning: Could not load review instructions: {e}")
        return ""

@track_tool(name="search_best_practices", metadata={"component": "documentation_search"})
async def search_best_practices(
    context: RunContext[ReviewDeps],
    language: str,
    framework: Optional[str] = None,
    deps: ReviewDeps = None,  # Dependencies injected by the agent
) -> str:
    # Use deps from context if not provided directly
    if deps is None and hasattr(context, 'deps'):
        deps = context.deps
    log_info(f"Searching best practices for {language}{f' with framework {framework}' if framework else ''}")
    """
    Search and retrieve language/framework-specific best practices.

    This function first uses Context7 MCP tools to search for official documentation
    about best practices for the given language (and optional framework).
    If such documentation is unavailable, it falls back to a generic web search.

    Args:
        context: The dependency injection container with required methods:
            - resolve_library_id: Resolves a library name to its Context7 ID
            - get_library_docs: Retrieves documentation from Context7
            - search_web: Performs a web search
        language: The programming language to search for (e.g., 'python', 'javascript').
        framework: Optional framework (e.g., 'django', 'react').

    Returns:
        str: Best practices information in markdown format with source attribution.
    """
    def _format_search_query(lang: str, fw: Optional[str] = None) -> str:
        return f"{lang} {fw}".strip() if fw else lang

    search_query = _format_search_query(language, framework)
    primary_error = None

    # Try Context7 MCP first
    try:
        # Resolve library ID using the injected dependency
        resolved_libs = await context.deps.resolve_library_id({"libraryName": search_query})
        if not resolved_libs or not resolved_libs.get('libraries'):
            raise ValueError(f"No libraries found for: {search_query}")

        # Get the most relevant library from the search results
        lib_id = resolved_libs['libraries'][0]['id']

        # Fetch documentation using the injected dependency
        docs = await context.deps.get_library_docs({
            "context7CompatibleLibraryID": lib_id,
            "tokens": 5000,
            "topic": "best practices"
        })

        if not docs or 'content' not in docs or not docs['content'].strip():
            raise ValueError("No content found in documentation")

        # Format the response with source attribution
        result = f"# Best Practices for {search_query.title()}\n\n"
        result += docs['content'].strip()
        result += f"\n\n*Documentation retrieved from {lib_id}*"
        return result

    except Exception as e:
        primary_error = str(e)
        # Fall through to web search

    # Fallback to web search if Context7 fails
    try:
        fallback_query = f"{language} {framework} best practices" if framework else f"{language} best practices"
        # Perform a web search using the injected search_web dependency
        search_results = await context.deps.search_web({
            "query": fallback_query,
            "domain": "github.com"  # Focus on GitHub for code-related content
        })

        if search_results and search_results.get('results'):
            result = f"# Best Practices for {fallback_query.title()}\n\n"
            for i, item in enumerate(search_results['results'][:3], 1):
                title = item.get('title', 'No title')
                url = item.get('url', '#')
                result += f"{i}. [{title}]({url})\n"
                if 'snippet' in item:
                    result += f"   {item['snippet']}\n\n"

            if primary_error:
                result += f"\n*Note: Fallback to web search (Context7 error: {primary_error})*"
            return result

        return f"No best practices found for '{fallback_query}'.\n\n(Context7 error: {primary_error or 'N/A'})"

    except Exception as inner_error:
        error_msg = f"Error retrieving best practices for {language}"
        if framework:
            error_msg += f" with {framework}"
        error_msg += f" due to: {inner_error}"
        return error_msg

@track_tool(name="detect_languages", metadata={"component": "code_analysis"})
async def detect_languages(
    context: RunContext[ReviewDeps],
    files: List[FileDiff],
    deps: ReviewDeps = None,  # Dependencies injected by the agent
) -> List[str]:
    # Use deps from context if not provided directly
    if deps is None and hasattr(context, 'deps'):
        deps = context.deps
    log_info(f"Detecting languages from {len(files)} files")
    """
    Detect programming languages from file extensions in the diff.

    Args:
        context: The dependency injection container
        files: List of files in the diff

    Returns:
        List of detected programming languages
    """
    extensions = set()
    for file in files:
        if '.' in file['filename']:
            ext = file['filename'].split('.')[-1].lower()
            extensions.add(ext)

    # Map extensions to languages
    ext_to_lang = {
        'py': 'Python',
        'js': 'JavaScript',
        'jsx': 'JavaScript',
        'ts': 'TypeScript',
        'tsx': 'TypeScript',
        'java': 'Java',
        'go': 'Go',
        'rb': 'Ruby',
        'php': 'PHP',
        'cs': 'C#',
        'c': 'C',
        'cpp': 'C++',
        'h': 'C/C++',
        'hpp': 'C++',
        'swift': 'Swift',
        'kt': 'Kotlin',
        'rs': 'Rust',
        'sh': 'Shell',
        'sql': 'SQL',
        'html': 'HTML',
        'css': 'CSS',
        'scss': 'SCSS',
        'json': 'JSON',
        'yaml': 'YAML',
        'yml': 'YAML',
        'toml': 'TOML',
        'md': 'Markdown',
        'vue': 'Vue.js',
    }

    languages = set()
    for ext in extensions:
        if ext in ext_to_lang:
            languages.add(ext_to_lang[ext])

    return list(languages)

# Helper function to truncate large text
def _truncate_text(text: str, max_length: int = 4000) -> str:
    """Truncate text to a maximum length, adding an ellipsis if truncated."""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + '...'

@track_llm(
    name="analyze_code_diff",
    model="gpt-4o",  # Using gpt-4o for better performance and higher token limits
    input_mapping=lambda context, diff_content, custom_instructions, best_practices: {
        "diff_preview": _truncate_text(diff_content, 500),
        "custom_instructions_preview": _truncate_text(custom_instructions, 500),
        "best_practices_preview": _truncate_text(best_practices, 500),
        "diff_length": len(diff_content),
        "custom_instructions_length": len(custom_instructions),
        "best_practices_length": len(best_practices),
    },
    output_mapping=lambda result: {
        "num_comments": len(result) if isinstance(result, list) else 0,
        "comment_examples": [
            {
                "path": c.get("path", ""),
                "line": c.get("line", 0),
                "severity": c.get("severity", "info")
            }
            for c in (result[:2] if isinstance(result, list) else [])
        ],
    },
    metadata={"component": "code_review_analyzer"},
)
async def analyze_with_llm(
    context: RunContext[ReviewDeps],
    diff_content: str,
    custom_instructions: str,
    best_practices: str
) -> List[Dict[str, Any]]:
    log_info("Starting LLM analysis of the diff")
    log_info(f"Diff size: {len(diff_content)} chars, Instructions: {len(custom_instructions)} chars, Best practices: {len(best_practices)} chars")
    """Send diff to LLM for analysis and return structured comments.

    This function formats the diff and other context into a message for the agent.
    The actual LLM call is handled by the agent's built-in prompt system.

    Args:
        context: Dependency injection container with agent and context
        diff_content: The raw diff content to analyze
        custom_instructions: Custom review instructions
        best_practices: Language-specific best practices

    Returns:
        List of review comment dictionaries
    """
    # Get Langfuse tracer for additional tracking
    tracer = get_langfuse_tracer()

    # Format the message for the agent
    message = f"""
    ## Code Diff to Review:
    ```diff
    {diff_content}
    ```

    Please provide your feedback as a JSON array of comment objects. Each comment should have:
    - path: Relative file path
    - line: Line number (1-based)
    - body: The review comment (be specific and suggest fixes)
    - side: 'RIGHT' for new code, 'LEFT' for old code
    - severity: 'info'|'warning'|'error' (optional)
    """.format(diff_content=diff_content)

    try:
        # Format the system prompt with the provided custom_instructions and best_practices
        formatted_system_prompt = context.deps.agent.system_prompt.format(
            custom_instructions=custom_instructions,
            best_practices=best_practices
        )

        # Update the agent's system prompt with the formatted version
        context.deps.agent.system_prompt = formatted_system_prompt

        # Log the LLM call start
        if tracer and tracer.trace:
            tracer.log_event(
                name="llm_call_start",
                metadata={
                    "model": getattr(context.deps.agent, "llm_model", "unknown"),
                    "diff_length": len(diff_content),
                    "instructions_length": len(custom_instructions),
                    "best_practices_length": len(best_practices),
                }
            )

        # Now run the agent with the diff content
        response = await context.deps.agent.run(message, deps=context.deps)

        # The response should be a string containing JSON
        if not isinstance(response, str):
            response = str(response)

        # Extract JSON from markdown code block if present
        if '```json' in response:
            response = response.split('```json')[1].split('```')[0].strip()
        elif '```' in response:
            # Handle case where language isn't specified
            response = response.split('```')[1].split('```')[0].strip()

        comments = json.loads(response)
        if not isinstance(comments, list):
            raise ValueError("LLM response is not a list of comments")

        # Log successful completion
        if tracer and tracer.trace:
            tracer.log_event(
                name="llm_call_complete",
                metadata={
                    "num_comments": len(comments),
                    "response_length": len(response),
                }
            )

        return comments

    except json.JSONDecodeError as e:
        error_msg = f"Failed to parse LLM response: {e}"
        logger.error(error_msg)

        # Log the error to Langfuse
        if tracer and tracer.trace:
            tracer.log_event(
                name="llm_call_error",
                metadata={
                    "error_type": "JSONDecodeError",
                    "error_message": str(e),
                    "response_preview": _truncate_text(response, 500) if 'response' in locals() else "No response"
                }
            )

        return [{
            'path': 'review_error',
            'line': 1,
            'body': 'Failed to parse review comments. Please try again or check the logs.',
            'side': 'RIGHT',
            'severity': 'error'
        }]
    except Exception as e:
        error_msg = f"Error during LLM analysis: {e}"
        logger.exception(error_msg)

        # Log the error to Langfuse
        if tracer and tracer.trace:
            tracer.log_event(
                name="llm_call_error",
                metadata={
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "response_preview": _truncate_text(response, 500) if 'response' in locals() else "No response"
                }
            )

        return [{
            'path': 'review_error',
            'line': 1,
            'body': f'Error generating review: {str(e)}',
            'side': 'RIGHT',
            'severity': 'error'
        }]


@track_tool(
    name="aggregate_review_comments",
    metadata={"component": "code_review_processor"}
)
@track_tool(name="aggregate_review_comments", metadata={"component": "review_processing"})
def count_tokens(text: str) -> int:
    """Estimate the number of tokens in a text string."""
    if not text:
        return 0
    # More accurate token estimation for code
    # 1 token ~= 4 chars for English, but can be more for code
    # Add a buffer to be safe
    return max(1, len(text) // 3)  # More conservative estimate for code

def chunk_text(text: str, max_chunk_size: int = 10000) -> List[str]:
    """Split text into smaller chunks that won't exceed token limits."""
    if not text:
        return []

    # Split by lines first to avoid breaking in the middle of a line
    lines = text.split('\n')
    chunks = []
    current_chunk = []
    current_size = 0

    for line in lines:
        line_size = count_tokens(line)
        if current_size + line_size > max_chunk_size and current_chunk:
            chunks.append('\n'.join(current_chunk))
            current_chunk = []
            current_size = 0
        current_chunk.append(line)
        current_size += line_size

    if current_chunk:
        chunks.append('\n'.join(current_chunk))

    return chunks

class TokenBucket:
    """Token bucket implementation for rate limiting."""
    def __init__(self, tokens: int, refill_rate: float):
        self.tokens = tokens
        self.capacity = tokens
        self.refill_rate = refill_rate  # tokens per second
        self.last_update = time.time()
        self.lock = asyncio.Lock()

    async def consume(self, tokens: int) -> float:
        """Consume tokens, returns the time to wait if rate limited."""
        async with self.lock:
            now = time.time()
            time_passed = now - self.last_update

            # Refill tokens based on time passed
            self.tokens = min(
                self.capacity,
                self.tokens + time_passed * self.refill_rate
            )
            self.last_update = now

            if tokens > self.tokens:
                # Calculate wait time needed
                tokens_needed = tokens - self.tokens
                wait_time = tokens_needed / self.refill_rate
                # Ensure we have enough tokens for next request
                self.tokens = 0
                return wait_time

            self.tokens -= tokens
            return 0.0

    async def wait_for_tokens(self, tokens: int):
        """Wait until we have enough tokens available."""
        while True:
            wait_time = await self.consume(tokens)
            if wait_time <= 0:
                break
            log_info(f"Rate limiting: Waiting {wait_time:.2f}s to stay under TPM...")
            await asyncio.sleep(wait_time)

async def process_file_with_retry(
    context: RunContext[ReviewDeps],
    file_content: str,
    custom_instructions: str,
    best_practices: str,
    max_retries: int = 3,
    initial_delay: float = 1.0
) -> List[Dict[str, Any]]:
    """Process a file with retry logic for rate limits."""
    delay = initial_delay
    last_error = None

    for attempt in range(max_retries):
        try:
            return await analyze_with_llm(
                context=context,
                diff_content=file_content,
                custom_instructions=custom_instructions,
                best_practices=best_practices
            )
        except Exception as e:
            last_error = e
            if "rate_limit" in str(e).lower() or "429" in str(e):
                wait_time = min(delay * (2 ** attempt), 60)  # Exponential backoff with max 60s
                log_info(f"Rate limited, retry {attempt + 1}/{max_retries} in {wait_time:.1f}s...")
                await asyncio.sleep(wait_time)
            else:
                raise

    raise last_error or Exception("Max retries exceeded")

async def aggregate_review_comments(
    context: RunContext[ReviewDeps],
    diff: PRDiffResponse,
    custom_instructions: str,
    best_practices: Dict[str, str],
    deps: ReviewDeps = None,  # Dependencies injected by the agent
    batch_size: int = 1,  # Process one file at a time to better control rate limiting
    max_tokens_per_minute: int = 150000,  # Stay well under 200k TPM limit
) -> List[Dict[str, Any]]:
    # Use deps from context if not provided directly
    if deps is None and hasattr(context, 'deps'):
        deps = context.deps

    log_info(f"Aggregating review comments for {len(diff.files)} files in batches of {batch_size}")
    log_info(f"Available languages for best practices: {list(best_practices.keys())}")
    """
    Generate review comments based on the diff, custom instructions, and best practices.

    This function uses the agent to analyze code changes and generate meaningful,
    actionable review comments that help improve code quality. It processes files in
    smaller batches to avoid rate limits and improve reliability.

    Args:
        deps: The dependency injection container with agent and logger
        diff: The PR diff object containing file changes
        custom_instructions: Custom review instructions for the agent
        best_practices: Language-specific best practices to consider
        batch_size: Number of files to process in each batch (default: 5)

    Returns:
        List[Dict[str, Any]]: List of review comments with path, line, body, and side
    """
    # Get Langfuse tracer for tracking
    tracer = get_langfuse_tracer()

    # Track the start of comment generation
    start_time = time.time()
    all_comments = []

    # Initialize token bucket with very conservative settings
    # Use only 40% of the limit to be extra safe
    safe_limit = int(max_tokens_per_minute * 0.4)
    # Distribute over 50 seconds to avoid end-of-minute spikes
    tokens_per_second = safe_limit / 50
    
    token_bucket = TokenBucket(
        tokens=safe_limit,
        refill_rate=tokens_per_second
    )
    
    # More aggressive chunking
    MAX_CHUNK_SIZE = 1000  # Smaller chunks to stay well under limits
    # Assume 2x tokens for response to be safe
    TOKEN_MULTIPLIER = 2.0  # Count both input and output tokens
    
    # Global lock to ensure serial processing
    process_lock = asyncio.Lock()
    
    # Initialize token tracking
    token_tracker = {
        'total_processed': 0,
        'start_time': time.time()
    }

    # Process files one at a time with strict rate limiting
    for i, file in enumerate(diff.files, 1):
        log_info(f"Processing file {i}/{len(diff.files)}: {file.filename}")
        
        # Add delay between files with jitter
        if i > 1:  # No need to wait before the first file
            delay = 2.0 + (random.random() * 2.0)  # 2-4 seconds between files
            log_info(f"Waiting {delay:.1f} seconds before next file to respect rate limits...")
            await asyncio.sleep(delay)

        # Track stats for this file
        file_comments = []
        batch_stats = {
            "total_files": 1,
            "files_processed": 0,
            "files_with_comments": 0,
            "total_comments": 0,
            "languages": {}
        }
        
        try:
            # Get the best practices for this file's language if available
            file_best_practices = best_practices.get(file.language.lower(), "")

            # Skip binary files or files that are too large
            if file.status == 'binary' or not file.patch:
                log_info(f"Skipping binary or empty file: {file.filename}")
                batch_stats["files_processed"] += 1
                continue

            # Process file in chunks if needed
            file_content = f"File: {file.filename}\n\n{file.patch}"
            chunks = chunk_text(file_content, MAX_CHUNK_SIZE)
            file_comments = []
            
            async with process_lock:  # Ensure only one chunk is processed at a time
                for chunk_num, chunk in enumerate(chunks, 1):
                    # Calculate tokens for this chunk with buffer
                    input_tokens = count_tokens(chunk)
                    chunk_tokens = int(input_tokens * TOKEN_MULTIPLIER)
                    
                    # Wait for enough tokens to be available
                    log_info(f"Waiting for {chunk_tokens} tokens to process chunk {chunk_num}/{len(chunks)} of {file.filename}")
                    await token_bucket.wait_for_tokens(chunk_tokens)
                    
                    # Process the chunk
                    log_info(f"Processing chunk {chunk_num}/{len(chunks)} of {file.filename} "
                           f"(input: {input_tokens} tokens, total: {chunk_tokens} tokens)")
                    
                    chunk_start_time = time.time()
                    try:
                        # Process with retry
                        chunk_comments = await process_file_with_retry(
                            context=context,
                            file_content=chunk,
                            custom_instructions=custom_instructions,
                            best_practices=file_best_practices
                        )
                        
                        # Update stats
                        token_tracker['total_processed'] += chunk_tokens
                        elapsed = time.time() - token_tracker['start_time']
                        tpm = (token_tracker['total_processed'] / max(elapsed, 1)) * 60
                        
                        file_comments.extend(chunk_comments)
                        
                        # Log successful processing
                        chunk_time = time.time() - chunk_start_time
                        log_info(
                            f"Processed chunk {chunk_num}/{len(chunks)} in {chunk_time:.1f}s - "
                            f"{len(chunk_comments)} comments - "
                            f"Current rate: {tpm:,.0f} TPM"
                        )
                        
                        # Add a dynamic delay based on current rate
                        if tpm > safe_limit * 0.8:  # If we're approaching the limit
                            wait_time = 1.0 + (tpm / safe_limit)  # Scale wait time with usage
                            log_info(f"Rate limiting: Waiting {wait_time:.1f}s to stay under TPM...")
                            await asyncio.sleep(wait_time)
                        
                    except Exception as e:
                        chunk_time = time.time() - chunk_start_time
                        log_error(
                            f"Error processing chunk {chunk_num} of {file.filename} "
                            f"after {chunk_time:.1f}s: {str(e)}", 
                            exc_info=e
                        )
                        file_comments.append({
                            'path': file.filename,
                            'line': 1,
                            'body': f'Error processing chunk {chunk_num}: {str(e)}',
                            'side': 'RIGHT',
                            'severity': 'error'
                        })
                        
                        # On error, wait a bit longer
                        await asyncio.sleep(2.0)

            # Add file path to each comment
            for comment in file_comments:
                comment['path'] = file.filename
                if 'line' not in comment:
                    comment['line'] = 1  # Default line number if not specified
                if 'side' not in comment:
                    comment['side'] = 'RIGHT'  # Default side if not specified

            # Update stats
            batch_stats["files_processed"] += 1
            if file_comments:
                batch_stats["files_with_comments"] += 1
                batch_stats["total_comments"] += len(file_comments)
                all_comments.extend(file_comments)
            
            # Update language stats
            if file.language:
                batch_stats["languages"][file.language] = batch_stats["languages"].get(file.language, 0) + 1

            log_info(f"Processed {file.filename} - {len(file_comments)} comments")
                
        except Exception as e:
            log_error(f"Error processing file {file.filename if hasattr(file, 'filename') else 'unknown'}", exc_info=e)
            # Add error comment
            all_comments.append({
                'path': file.filename if hasattr(file, 'filename') else 'unknown',
                'line': 1,
                'body': f'Error processing file: {str(e)}',
                'side': 'RIGHT',
                'severity': 'error'
            })

    # Log completion
    end_time = time.time()
    duration = end_time - start_time

    # Aggregate stats across all batches
    total_stats = {
        "total_files": len(diff.files),
        "files_processed": sum(batch_stats.get("files_processed", 0) for _ in range(0, len(diff.files), batch_size)),
        "files_with_comments": sum(batch_stats.get("files_with_comments", 0) for _ in range(0, len(diff.files), batch_size)),
        "total_comments": len(all_comments),
        "languages": {}
    }

    # Merge language stats
    for i in range(0, len(diff.files), batch_size):
        for lang, count in batch_stats.get("languages", {}).items():
            total_stats["languages"][lang] = total_stats["languages"].get(lang, 0) + count

    log_info(f"Review completed in {duration:.2f} seconds")
    log_info(f"Files processed: {total_stats['files_processed']}/{total_stats['total_files']}")
    log_info(f"Files with comments: {total_stats['files_with_comments']}")
    log_info(f"Total comments: {total_stats['total_comments']}")
    log_info(f"Languages detected: {', '.join(total_stats['languages'].keys()) if total_stats['languages'] else 'None'}")

    # Log detailed language stats
    for lang, count in total_stats['languages'].items():
        log_info(f"  - {lang}: {count} files")

    # Calculate additional stats
    stats = {
        "total_additions": 0,
        "total_deletions": 0,
        "files_with_changes": 0,
        "generated_comments": 0,
        "error_count": 0
    }

    # Initialize comments list
    all_comments = []

    try:
        # Process each file in the diff
        for file in diff.files:
            try:
                # Skip binary or empty files
                if file.status == 'binary' or not hasattr(file, 'patch') or not file.patch:
                    log_info(f"Skipping binary or empty file: {getattr(file, 'filename', 'unknown')}")
                    continue

                # Track file changes
                if hasattr(file, 'additions'):
                    stats["total_additions"] += file.additions
                if hasattr(file, 'deletions'):
                    stats["total_deletions"] += file.deletions
                if hasattr(file, 'changes') and file.changes > 0:
                    stats["files_with_changes"] += 1

                # Format the file diff for analysis
                diff_content = (
                    f"File: {file.filename} ({file.status if hasattr(file, 'status') else 'modified'})\n"
                    f"Additions: {getattr(file, 'additions', 0)}, Deletions: {getattr(file, 'deletions', 0)}\n"
                    f"{file.patch}\n"
                )

                # Get best practices for this file's language
                file_lang = getattr(file, 'language', '').lower()
                file_best_practices = best_practices.get(file_lang, "")

                # Log the start of LLM analysis for this file
                if tracer and tracer.trace:
                    tracer.log_event(
                        name="llm_analysis_start",
                        metadata={
                            "file": getattr(file, 'filename', 'unknown'),
                            "language": file_lang,
                            "additions": getattr(file, 'additions', 0),
                            "deletions": getattr(file, 'deletions', 0),
                            "changes": getattr(file, 'changes', 0)
                        }
                    )

                # Analyze the file with LLM
                file_comments = await analyze_with_llm(
                    context=context,
                    diff_content=diff_content,
                    custom_instructions=custom_instructions,
                    best_practices=file_best_practices
                )

                # Process and validate comments
                valid_comments = []
                for comment in file_comments:
                    if not isinstance(comment, dict) or 'body' not in comment:
                        continue

                    # Ensure required fields are present
                    if 'path' not in comment:
                        comment['path'] = getattr(file, 'filename', 'unknown')
                    if 'line' not in comment:
                        comment['line'] = 1
                    if 'side' not in comment:
                        comment['side'] = 'RIGHT'
                    if 'severity' not in comment:
                        comment['severity'] = 'info'

                    valid_comments.append(comment)

                # Add to all comments
                all_comments.extend(valid_comments)
                stats["generated_comments"] += len(valid_comments)

                log_info(f"Processed {getattr(file, 'filename', 'unknown')} - {len(valid_comments)} comments")

            except Exception as e:
                stats["error_count"] += 1
                error_msg = f"Error processing file {getattr(file, 'filename', 'unknown')}: {str(e)}"
                logger.exception(error_msg)

                # Add error comment
                all_comments.append({
                    'path': getattr(file, 'filename', 'unknown'),
                    'line': 1,
                    'body': f'Error processing file: {str(e)}',
                    'side': 'RIGHT',
                    'severity': 'error'
                })

                # Log the error to Langfuse
                if tracer and tracer.trace:
                    tracer.log_event(
                        name="file_processing_error",
                        metadata={
                            "file": getattr(file, 'filename', 'unknown'),
                            "error_type": type(e).__name__,
                            "error_message": str(e),
                            "stack_trace": traceback.format_exc()
                        }
                    )

    except Exception as e:
        stats["error_count"] += 1
        error_msg = f"Unexpected error during review: {str(e)}"
        logger.exception(error_msg)

        # Add error comment
        all_comments.append({
            'path': 'review_error',
            'line': 1,
            'body': error_msg,
            'side': 'RIGHT',
            'severity': 'error'
        })

        # Log the error to Langfuse
        if tracer and tracer.trace:
            tracer.log_event(
                name="review_processing_error",
                metadata={
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "stack_trace": traceback.format_exc()
                }
            )

    finally:
        # Log completion metrics
        if tracer and tracer.trace:
            duration = time.time() - start_time
            tracer.log_event(
                name="review_completed",
                metadata={
                    **stats,
                    "total_files_processed": len(diff.files),
                    "total_comments_generated": len(all_comments),
                    "duration_seconds": duration,
                    "files_per_second": len(diff.files) / duration if duration > 0 else 0,
                    "comments_per_second": len(all_comments) / duration if duration > 0 else 0
                }
            )

    return all_comments
