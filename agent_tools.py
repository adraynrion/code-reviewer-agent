"""Tools for the code review agent to interact with GitHub/GitLab and analyze code."""

import json
import logging
from typing import Any, Dict, List, Optional
from pydantic_ai import RunContext

from models import FileDiff, ReviewComment, PRDiffResponse
from models.deps import ReviewDeps

# Configure logger
logger = logging.getLogger(__name__)

async def parse_unified_diff(diff_text: str) -> List[Dict[str, Any]]:
    """
    Parse a GitHub-provided unified diff into structured file diffs.

    Args:
        diff_text: The unified diff text from GitHub

    Returns:
        List of parsed file diffs with metadata
    """
    files = []
    current_file = None
    splited_diff_text = diff_text.split('\n')

    for line in splited_diff_text:
        # Start of a new file diff
        if line.startswith('diff --git'):
            # Process previous file if exists
            if current_file is not None:
                if 'patch' in current_file and isinstance(current_file['patch'], list):
                    current_file['patch'] = '\n'.join(current_file['patch'])
                files.append(current_file)

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

            current_file = {
                'filename': filename,
                'status': status,
                'previous_filename': previous_filename,
                'additions': 0,
                'deletions': 0,
                'patch': [],
                'is_binary': False
            }

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
    if current_file:
        # Convert patch list to string if needed
        if 'patch' in current_file and isinstance(current_file['patch'], list):
            current_file['patch'] = '\n'.join(current_file['patch'])
        files.append(current_file)

    return files

async def get_pr_diff(
    context: RunContext[ReviewDeps],
    repository: str,
    pr_id: int,
) -> PRDiffResponse:
    """
    Get the diff for a pull request.

    Args:
        context: The dependency injection container
        repository: The repository in format 'owner/repo' or 'group/project' for GitLab
        pr_id: The pull/merge request number

    Returns:
        PRDiffResponse containing the diff information
    """
    if context.deps.platform == 'github':
        # First, get the PR details to get the base and head SHAs
        pr_url = f"https://api.github.com/repos/{repository}/pulls/{pr_id}"
        headers = {
            "Authorization": f"token {context.deps.github_token}",
            "Accept": "application/vnd.github.v3+json"
        }

        # Get PR details
        pr_response = await context.deps.http_client.get(pr_url, headers=headers)
        pr_response.raise_for_status()
        pr_data = pr_response.json()
        base_sha = pr_data['base']['sha']
        head_sha = pr_data['head']['sha']

        # Get the raw diff
        diff_url = f"https://api.github.com/repos/{repository}/pulls/{pr_id}.diff"
        diff_response = await context.deps.http_client.get(diff_url, headers=headers)
        diff_response.raise_for_status()
        diff_text = diff_response.text

        # Parse the diff
        files = await parse_unified_diff(diff_text)

        # Ensure all files have base and head SHAs
        for file in files:
            file['base_sha'] = base_sha
            file['head_sha'] = head_sha

        return PRDiffResponse(
            files=[FileDiff(**f) for f in files],
            base_sha=base_sha,
            head_sha=head_sha
        )
    else:  # GitLab
        # TODO: Similar implementation for GitLab
        pass

    return PRDiffResponse(files=[], base_sha='', head_sha='')

async def post_review_comment(
    context: RunContext[ReviewDeps],
    repository: str,
    pr_id: int,
    comments: List[ReviewComment],
) -> bool:
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

        response = await context.deps.http_client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return True
    else:  # GitLab
        # TODO: Similar implementation for GitLab
        pass

    return False

async def get_review_instructions(
    context: RunContext[ReviewDeps],
    instructions_path: str,
) -> str:
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

async def search_best_practices(
    context: RunContext[ReviewDeps],
    language: str,
    framework: Optional[str] = None,
) -> str:
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

async def detect_languages(
    context: RunContext[ReviewDeps],
    files: List[FileDiff],
) -> List[str]:
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

async def analyze_with_llm(
    context: RunContext[ReviewDeps],
    diff_content: str,
    custom_instructions: str,
    best_practices: str
) -> List[Dict[str, Any]]:
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

        return comments

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response: {e}")
        return [{
            'path': 'review_error',
            'line': 1,
            'body': 'Failed to parse review comments. Please try again or check the logs.',
            'side': 'RIGHT',
            'severity': 'error'
        }]
    except Exception as e:
        logger.exception("Error during LLM analysis")
        return [{
            'path': 'review_error',
            'line': 1,
            'body': f'Error generating review: {str(e)}',
            'side': 'RIGHT',
            'severity': 'error'
        }]


async def aggregate_review_comments(
    context: RunContext[ReviewDeps],
    diff: PRDiffResponse,
    custom_instructions: str,
    best_practices: Dict[str, str],
) -> List[Dict[str, Any]]:
    """
    Generate review comments based on the diff, custom instructions, and best practices.

    This function uses the agent to analyze code changes and generate meaningful,
    actionable review comments that help improve code quality.

    Args:
        deps: The dependency injection container with agent and logger
        diff: The PR diff object containing file changes
        custom_instructions: Custom review instructions for the agent
        best_practices: Language-specific best practices to consider

    Returns:
        List[Dict[str, Any]]: List of review comments with path, line, body, and side
    """
    # Process each file in the diff
    comments = []

    # Analyze the actual code changes
    try:
        # Convert the files to a formatted string for analysis
        diff_content = "\n".join(
            f"File: {file['filename']} ({file['status']})\n"
            f"Additions: {file['additions']}, Deletions: {file['deletions']}\n"
            f"{file.get('patch', 'No changes')}\n"
            for file in diff.files
        )
        
        if diff_content:
            # Convert best_practices to string if it's a dictionary
            best_practices_str = (
                json.dumps(best_practices, indent=2)
                if isinstance(best_practices, dict)
                else best_practices
            )

            file_comments = await analyze_with_llm(
                context=context,
                diff_content=diff_content,
                custom_instructions=custom_instructions,
                best_practices=best_practices_str
            )
            comments.extend(file_comments)
    except Exception as e:
        logger.exception("Error processing diff")
        comments.append({
            'path': 'review_error',
            'line': 1,
            'body': f'Error processing diff: {str(e)}',
            'side': 'RIGHT',
            'severity': 'error'
        })

    return comments
