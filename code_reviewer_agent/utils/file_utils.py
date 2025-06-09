"""File utility functions for the code review agent."""

import os
from typing import Dict, List, Set, Union


def _detect_language(filename: str) -> list[str]:
    """Detect programming languages used based on the filename.

    Args:
        filename: The filename to detect the language for

    Returns:
        The detected programming languages.

    """
    # Simple file extension based detection
    ext = filename.split(".")[-1].lower()

    # Handle files without extensions
    if not ext or ext == filename:
        return ["no_extension"]

    # Language detection based on file extension
    language_map = {
        # Programming languages
        "py": ["python"],
        "js": ["javascript"],
        "jsx": ["javascript"],
        "mjs": ["javascript"],
        "cjs": ["javascript"],
        "ts": ["typescript", "javascript"],
        "tsx": ["typescript", "javascript"],
        "java": ["java"],
        "go": ["go"],
        "rb": ["ruby"],
        "php": ["php"],
        "phtml": ["php"],
        "php3": ["php"],
        "php4": ["php"],
        "php5": ["php"],
        "php7": ["php"],
        "phps": ["php"],
        "cs": ["csharp"],
        "cpp": ["c++"],
        "cxx": ["c++"],
        "cc": ["c++"],
        "hpp": ["c++", "c"],
        "hxx": ["c++", "c"],
        "hh": ["c++", "c"],
        "c": ["c"],
        "h": ["c", "c++"],
        "swift": ["swift"],
        "kt": ["kotlin"],
        "kts": ["kotlin"],
        "rs": ["rust"],
        "scala": ["scala"],
        "sc": ["scala"],
        # Web and markup
        "html": ["html"],
        "htm": ["html"],
        "xhtml": ["html"],
        "html5": ["html"],
        "css": ["css"],
        "scss": ["scss", "css"],
        "sass": ["sass", "css"],
        "less": ["less", "css"],
        # Template and configuration
        "json": ["json"],
        "yaml": ["yaml"],
        "yml": ["yaml"],
        "xml": ["xml"],
        "md": ["markdown"],
        "markdown": ["markdown"],
        # Shell and scripts
        "sh": ["shell"],
        "bash": ["shell"],
        "zsh": ["shell"],
        "fish": ["shell"],
        "ps1": ["powershell"],
        "psm1": ["powershell"],
        "psd1": ["powershell"],
        # Database
        "sql": ["sql"],
        # Configuration files
        "env": ["dotenv"],
        "env.example": ["dotenv"],
        "toml": ["toml"],
        "ini": ["ini"],
        "cfg": ["ini"],
        "prefs": ["ini"],
        "dockerfile": ["dockerfile"],
        "dockerignore": ["dockerfile"],
        "gitignore": ["git"],
        "gitattributes": ["git"],
        "gitmodules": ["git"],
        "editorconfig": ["editorconfig"],
    }

    return language_map.get(ext, ["unknown"])


def get_file_languages(file_paths: Union[str, List[str]]) -> Dict[str, Set[str]]:
    """Get the programming languages used in the given files.

    Args:
        file_paths: A single file path or a list of file paths to analyze

    Returns:
        Dictionary mapping detected languages to sets of file paths

    """
    # Convert single file path to list for consistent processing
    if isinstance(file_paths, str):
        file_paths = [file_paths]

    languages: Dict[str, Set[str]] = {}

    for file_path in file_paths:
        # Get the filename from the path
        filename = os.path.basename(file_path)

        # Detect languages for the current file
        detected_languages = _detect_language(filename)

        # Add file to each detected language's set
        for lang in detected_languages:
            if lang not in languages:
                languages[lang] = set()
            languages[lang].add(file_path)

    return languages
