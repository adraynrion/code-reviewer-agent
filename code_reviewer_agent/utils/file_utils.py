import os
from typing import Dict, List, Set, Tuple, Union

from code_reviewer_agent.models.base_types import StringValidator


class Filename(StringValidator):
    pass


class FilesPath(Union[str, List[str]]):
    pass


class LanguageTuple(Tuple[str]):
    pass


class FileLanguages(Dict[str, Set[str]]):
    pass


class LanguageUtils:
    _language_dict = {
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

    @classmethod
    def _detect_language(cls, filename: Filename) -> LanguageTuple:
        ext = filename.split(".")[-1].lower()
        if not ext or ext == filename:
            return LanguageTuple()
        return cls._language_dict.get(ext, LanguageTuple())

    @classmethod
    def get_file_languages(cls, file_paths: FilesPath) -> FileLanguages:
        languages: FileLanguages = {}
        for file_path in file_paths:
            filename = os.path.basename(file_path)
            detected_languages = cls._detect_language(filename)
            for lang in detected_languages:
                if file_path not in languages:
                    languages[file_path] = set()
                languages[file_path].add(lang)
        return languages
