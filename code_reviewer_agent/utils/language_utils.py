import os

from code_reviewer_agent.models.base_types import (
    Filename,
    FilesPath,
    Languages,
    LanguageTuple,
)


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
        return LanguageTuple(tuple(cls._language_dict.get(ext, [])))

    @classmethod
    def get_file_languages(cls, files_path: FilesPath) -> Languages:
        languages = Languages()
        for file_path in files_path:
            filename = os.path.basename(file_path)
            detected_languages = cls._detect_language(Filename(filename))
            for lang in detected_languages:
                if file_path not in languages:
                    languages[file_path] = set()
                languages[file_path].add(lang)
        return Languages(languages)
