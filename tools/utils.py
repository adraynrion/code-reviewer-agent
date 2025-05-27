"""Utility functions for the code review agent."""

import logging
from typing import Dict, List, Optional
from pydantic_ai import RunContext
from models import FileDiff
from models.deps import ReviewDeps

# Configure logger
logger = logging.getLogger(__name__)

def log_info(message: str) -> None:
    """Log an info message to the logger."""
    logger.info(message)

def log_error(message: str, exc_info=None) -> None:
    """Log an error message to the logger."""
    logger.error(message, exc_info=exc_info)

def _truncate_text(text: str, max_length: int = 4000) -> str:
    """
    Truncate text to a maximum length, adding an ellipsis if truncated.

    Args:
        text: The text to truncate
        max_length: Maximum length of the text

    Returns:
        Truncated text with ellipsis if needed
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + '...'

def count_tokens(text: str) -> int:
    """
    Estimate the number of tokens in a text string.

    This is a rough estimate based on average word length and whitespace.
    For more accurate counting, use the tokenizer specific to your LLM.

    Args:
        text: The text to count tokens for

    Returns:
        Estimated number of tokens
    """
    # Rough estimate: 1 token ~= 4 chars or 0.75 words in English
    return max(1, len(text) // 4)

def chunk_text(text: str, max_chunk_size: int = 10000) -> List[str]:
    """
    Split text into smaller chunks that won't exceed token limits.

    Args:
        text: The text to split
        max_chunk_size: Maximum size of each chunk in characters

    Returns:
        List of text chunks
    """
    if not text:
        return []

    # If text is already small enough, return as is
    if len(text) <= max_chunk_size:
        return [text]

    # Try to split on double newlines first (paragraphs)
    chunks = []
    current_chunk = ""

    for paragraph in text.split('\n\n'):
        # If adding this paragraph would exceed the chunk size, start a new chunk
        if len(current_chunk) + len(paragraph) + 2 > max_chunk_size and current_chunk:
            chunks.append(current_chunk)
            current_chunk = paragraph
        else:
            if current_chunk:
                current_chunk += '\n\n' + paragraph
            else:
                current_chunk = paragraph

    # Add the last chunk if not empty
    if current_chunk:
        chunks.append(current_chunk)

    # If we still have chunks that are too large, split on newlines
    final_chunks = []
    for chunk in chunks:
        if len(chunk) > max_chunk_size:
            final_chunks.extend(chunk[i:i + max_chunk_size] for i in range(0, len(chunk), max_chunk_size))
        else:
            final_chunks.append(chunk)

    return final_chunks

async def detect_languages(
    context: RunContext[ReviewDeps],
    files: List[FileDiff],
    deps: ReviewDeps = None
) -> Dict[str, List[str]]:
    """
    Detect programming languages used in the changed files.

    Args:
        context: The dependency injection container
        files: List of file diffs
        deps: Optional dependencies (will be extracted from context if not provided)

    Returns:
        Dictionary mapping file paths to lists of detected languages
    """
    # Use deps from context if not provided directly
    if deps is None and hasattr(context, 'deps'):
        deps = context.deps

    if deps is None:
        raise ValueError("No dependencies provided. Please ensure the agent is initialized with the correct dependencies.")

    language_map = {}

    for file in files:
        if not hasattr(file, 'filename') or not file.filename:
            continue

        # Simple file extension based detection
        ext = file.filename.split('.')[-1].lower()
        languages = []

        if ext in ['py']:
            languages.append('python')
        elif ext in ['js', 'jsx', 'ts', 'tsx']:
            languages.append('javascript')
            if ext in ['ts', 'tsx']:
                languages.append('typescript')
        elif ext in ['java']:
            languages.append('java')
        elif ext in ['go']:
            languages.append('go')
        elif ext in ['rb']:
            languages.append('ruby')
        elif ext in ['php']:
            languages.append('php')
        elif ext in ['cs']:
            languages.append('csharp')
        elif ext in ['cpp', 'cxx', 'cc', 'h', 'hpp']:
            languages.append('c++')
        elif ext in ['c']:
            languages.append('c')
        elif ext in ['swift']:
            languages.append('swift')
        elif ext in ['kt', 'kts']:
            languages.append('kotlin')
        elif ext in ['rs']:
            languages.append('rust')
        elif ext in ['scala']:
            languages.append('scala')

        if languages:
            language_map[file.filename] = languages

    return language_map

async def search_best_practices(
    context: RunContext[ReviewDeps],
    language: str,
    framework: Optional[str] = None,
    deps: ReviewDeps = None
) -> str:
    """
    Search for best practices for a given language and optional framework.

    Args:
        context: The dependency injection container
        language: The programming language
        framework: Optional framework (e.g., 'django', 'react', 'spring')
        deps: Optional dependencies (will be extracted from context if not provided)

    Returns:
        String containing best practices
    """
    # Use deps from context if not provided directly
    if deps is None and hasattr(context, 'deps'):
        deps = context.deps

    if deps is None:
        raise ValueError("No dependencies provided. Please ensure the agent is initialized with the correct dependencies.")

    # This is a simplified version - in a real implementation, you would query a knowledge base
    best_practices = []

    # Add language-specific best practices
    language = language.lower()
    if language == 'python':
        best_practices.extend([
            "Follow PEP 8 style guide for Python code.",
            "Use type hints for better code clarity and IDE support.",
            "Write docstrings for all public modules, functions, classes, and methods.",
            "Use list/dict/set comprehensions where they improve readability.",
            "Prefer f-strings over %-formatting or str.format()."
        ])
    elif language == 'javascript':
        best_practices.extend([
            "Use const by default, let when rebinding is needed, and avoid var.",
            "Use strict equality (===) instead of loose equality (==).",
            "Use template literals for string interpolation.",
            "Handle promises with async/await for better readability.",
            "Use ESLint and Prettier for consistent code style."
        ])

    # Add framework-specific best practices
    if framework:
        framework = framework.lower()
        if framework == 'django':
            best_practices.extend([
                "Keep business logic out of views, use services layer.",
                "Use Django's built-in authentication and authorization.",
                "Optimize database queries with select_related and prefetch_related.",
                "Use Django's class-based views for better code organization.",
                "Write unit tests for models, forms, and views."
            ])
        elif framework == 'react':
            best_practices.extend([
                "Use functional components with hooks.",
                "Keep components small and focused on a single responsibility.",
                "Use React.memo, useMemo, and useCallback for performance.",
                "Lift state up to the nearest common ancestor when needed.",
                "Use PropTypes or TypeScript for prop type checking."
            ])

    return "\n".join(f"- {bp}" for bp in best_practices) if best_practices else "No specific best practices found."

async def get_review_instructions(
    context: RunContext[ReviewDeps],
    instructions_path: str,
    deps: ReviewDeps = None
) -> str:
    """
    Get review instructions from a file or URL.

    Args:
        context: The dependency injection container
        instructions_path: Path to the instructions file or URL
        deps: Optional dependencies (will be extracted from context if not provided)

    Returns:
        String containing the review instructions
    """
    # Use deps from context if not provided directly
    if deps is None and hasattr(context, 'deps'):
        deps = context.deps

    if deps is None:
        raise ValueError("No dependencies provided. Please ensure the agent is initialized with the correct dependencies.")

    try:
        # Check if it's a URL
        if instructions_path.startswith(('http://', 'https://')):
            # In a real implementation, you would fetch the content from the URL
            # For now, we'll just return a placeholder
            return f"Review instructions from {instructions_path} (URL fetching not implemented)"

        # Otherwise, treat it as a file path
        with open(instructions_path, 'r') as f:
            return f.read()

    except Exception as e:
        log_error(f"Error loading review instructions from {instructions_path}: {str(e)}")
        return ""  # Return empty string if instructions can't be loaded
