from unittest.mock import patch

import pytest

from code_reviewer_agent.models.base_types import (
    Filename,
    FilesPath,
    Languages,
    LanguageTuple,
)
from code_reviewer_agent.utils.language_utils import LanguageUtils


class TestLanguageUtils:
    """Test LanguageUtils class for language detection."""

    def test_language_dict_structure(self) -> None:
        """Test that _language_dict has expected structure."""
        assert isinstance(LanguageUtils._language_dict, dict)
        assert len(LanguageUtils._language_dict) > 0

        # Check some expected extensions
        assert "py" in LanguageUtils._language_dict
        assert "js" in LanguageUtils._language_dict
        assert "ts" in LanguageUtils._language_dict
        assert "java" in LanguageUtils._language_dict
        assert "go" in LanguageUtils._language_dict

        # Check that values are lists
        for ext, languages in LanguageUtils._language_dict.items():
            assert isinstance(languages, list)
            assert len(languages) > 0
            for lang in languages:
                assert isinstance(lang, str)

    def test_detect_language_python_files(self) -> None:
        """Test language detection for Python files."""
        result = LanguageUtils._detect_language(Filename("test.py"))
        assert result == LanguageTuple(("python",))

        result = LanguageUtils._detect_language(Filename("script.py"))
        assert result == LanguageTuple(("python",))

    def test_detect_language_javascript_files(self) -> None:
        """Test language detection for JavaScript files."""
        # Basic JavaScript
        result = LanguageUtils._detect_language(Filename("app.js"))
        assert result == LanguageTuple(("javascript",))

        # JSX
        result = LanguageUtils._detect_language(Filename("component.jsx"))
        assert result == LanguageTuple(("javascript",))

        # Module JS
        result = LanguageUtils._detect_language(Filename("module.mjs"))
        assert result == LanguageTuple(("javascript",))

        # CommonJS
        result = LanguageUtils._detect_language(Filename("common.cjs"))
        assert result == LanguageTuple(("javascript",))

    def test_detect_language_typescript_files(self) -> None:
        """Test language detection for TypeScript files."""
        # TypeScript
        result = LanguageUtils._detect_language(Filename("app.ts"))
        assert result == LanguageTuple(("typescript", "javascript"))

        # TSX
        result = LanguageUtils._detect_language(Filename("component.tsx"))
        assert result == LanguageTuple(("typescript", "javascript"))

    def test_detect_language_web_files(self) -> None:
        """Test language detection for web files."""
        # HTML files
        result = LanguageUtils._detect_language(Filename("index.html"))
        assert result == LanguageTuple(("html",))

        result = LanguageUtils._detect_language(Filename("page.htm"))
        assert result == LanguageTuple(("html",))

        result = LanguageUtils._detect_language(Filename("doc.xhtml"))
        assert result == LanguageTuple(("html",))

        # CSS files
        result = LanguageUtils._detect_language(Filename("style.css"))
        assert result == LanguageTuple(("css",))

        result = LanguageUtils._detect_language(Filename("style.scss"))
        assert result == LanguageTuple(("scss", "css"))

        result = LanguageUtils._detect_language(Filename("style.sass"))
        assert result == LanguageTuple(("sass", "css"))

        result = LanguageUtils._detect_language(Filename("style.less"))
        assert result == LanguageTuple(("less", "css"))

    def test_detect_language_config_files(self) -> None:
        """Test language detection for configuration files."""
        # JSON
        result = LanguageUtils._detect_language(Filename("package.json"))
        assert result == LanguageTuple(("json",))

        # YAML
        result = LanguageUtils._detect_language(Filename("config.yaml"))
        assert result == LanguageTuple(("yaml",))

        result = LanguageUtils._detect_language(Filename("config.yml"))
        assert result == LanguageTuple(("yaml",))

        # XML
        result = LanguageUtils._detect_language(Filename("config.xml"))
        assert result == LanguageTuple(("xml",))

        # Markdown
        result = LanguageUtils._detect_language(Filename("README.md"))
        assert result == LanguageTuple(("markdown",))

        result = LanguageUtils._detect_language(Filename("doc.markdown"))
        assert result == LanguageTuple(("markdown",))

    def test_detect_language_shell_files(self) -> None:
        """Test language detection for shell files."""
        result = LanguageUtils._detect_language(Filename("script.sh"))
        assert result == LanguageTuple(("shell",))

        result = LanguageUtils._detect_language(Filename("script.bash"))
        assert result == LanguageTuple(("shell",))

        result = LanguageUtils._detect_language(Filename("script.zsh"))
        assert result == LanguageTuple(("shell",))

        result = LanguageUtils._detect_language(Filename("script.fish"))
        assert result == LanguageTuple(("shell",))

    def test_detect_language_powershell_files(self) -> None:
        """Test language detection for PowerShell files."""
        result = LanguageUtils._detect_language(Filename("script.ps1"))
        assert result == LanguageTuple(("powershell",))

        result = LanguageUtils._detect_language(Filename("module.psm1"))
        assert result == LanguageTuple(("powershell",))

        result = LanguageUtils._detect_language(Filename("data.psd1"))
        assert result == LanguageTuple(("powershell",))

    def test_detect_language_c_family_files(self) -> None:
        """Test language detection for C/C++ files."""
        # C files
        result = LanguageUtils._detect_language(Filename("main.c"))
        assert result == LanguageTuple(("c",))

        # C++ files
        result = LanguageUtils._detect_language(Filename("main.cpp"))
        assert result == LanguageTuple(("c++",))

        result = LanguageUtils._detect_language(Filename("main.cxx"))
        assert result == LanguageTuple(("c++",))

        result = LanguageUtils._detect_language(Filename("main.cc"))
        assert result == LanguageTuple(("c++",))

        # Header files (can be both C and C++)
        result = LanguageUtils._detect_language(Filename("header.h"))
        assert result == LanguageTuple(("c", "c++"))

        result = LanguageUtils._detect_language(Filename("header.hpp"))
        assert result == LanguageTuple(("c++", "c"))

    def test_detect_language_other_programming_languages(self) -> None:
        """Test language detection for other programming languages."""
        # Java
        result = LanguageUtils._detect_language(Filename("Main.java"))
        assert result == LanguageTuple(("java",))

        # Go
        result = LanguageUtils._detect_language(Filename("main.go"))
        assert result == LanguageTuple(("go",))

        # Ruby
        result = LanguageUtils._detect_language(Filename("app.rb"))
        assert result == LanguageTuple(("ruby",))

        # PHP
        result = LanguageUtils._detect_language(Filename("index.php"))
        assert result == LanguageTuple(("php",))

        result = LanguageUtils._detect_language(Filename("page.php5"))
        assert result == LanguageTuple(("php",))

        # C#
        result = LanguageUtils._detect_language(Filename("Program.cs"))
        assert result == LanguageTuple(("csharp",))

        # Swift
        result = LanguageUtils._detect_language(Filename("main.swift"))
        assert result == LanguageTuple(("swift",))

        # Kotlin
        result = LanguageUtils._detect_language(Filename("Main.kt"))
        assert result == LanguageTuple(("kotlin",))

        result = LanguageUtils._detect_language(Filename("script.kts"))
        assert result == LanguageTuple(("kotlin",))

        # Rust
        result = LanguageUtils._detect_language(Filename("main.rs"))
        assert result == LanguageTuple(("rust",))

        # Scala
        result = LanguageUtils._detect_language(Filename("Main.scala"))
        assert result == LanguageTuple(("scala",))

    def test_detect_language_special_files(self) -> None:
        """Test language detection for special configuration files."""
        # Docker files
        result = LanguageUtils._detect_language(Filename("Dockerfile"))
        assert result == LanguageTuple(("dockerfile",))

        result = LanguageUtils._detect_language(Filename(".dockerignore"))
        assert result == LanguageTuple(("dockerfile",))

        # Git files
        result = LanguageUtils._detect_language(Filename(".gitignore"))
        assert result == LanguageTuple(("git",))

        result = LanguageUtils._detect_language(Filename(".gitattributes"))
        assert result == LanguageTuple(("git",))

        # Environment files
        result = LanguageUtils._detect_language(Filename(".env"))
        assert result == LanguageTuple(("dotenv",))

        result = LanguageUtils._detect_language(Filename(".env.example"))
        assert result == LanguageTuple(("dotenv",))

        # TOML
        result = LanguageUtils._detect_language(Filename("pyproject.toml"))
        assert result == LanguageTuple(("toml",))

        # INI
        result = LanguageUtils._detect_language(Filename("config.ini"))
        assert result == LanguageTuple(("ini",))

        result = LanguageUtils._detect_language(Filename("settings.cfg"))
        assert result == LanguageTuple(("ini",))

        # SQL
        result = LanguageUtils._detect_language(Filename("query.sql"))
        assert result == LanguageTuple(("sql",))

    def test_detect_language_no_extension(self) -> None:
        """Test language detection for files without extensions."""
        result = LanguageUtils._detect_language(Filename("README"))
        assert result == LanguageTuple(())

        result = LanguageUtils._detect_language(Filename("Makefile"))
        assert result == LanguageTuple(())

        result = LanguageUtils._detect_language(Filename("LICENSE"))
        assert result == LanguageTuple(())

    def test_detect_language_unknown_extension(self) -> None:
        """Test language detection for unknown file extensions."""
        result = LanguageUtils._detect_language(Filename("file.unknown"))
        assert result == LanguageTuple(())

        result = LanguageUtils._detect_language(Filename("test.xyz"))
        assert result == LanguageTuple(())

    def test_detect_language_case_insensitive(self) -> None:
        """Test that language detection is case insensitive."""
        result = LanguageUtils._detect_language(Filename("Script.PY"))
        assert result == LanguageTuple(("python",))

        result = LanguageUtils._detect_language(Filename("App.JS"))
        assert result == LanguageTuple(("javascript",))

        result = LanguageUtils._detect_language(Filename("Style.CSS"))
        assert result == LanguageTuple(("css",))

    def test_detect_language_multiple_dots(self) -> None:
        """Test language detection for files with multiple dots."""
        result = LanguageUtils._detect_language(Filename("test.spec.ts"))
        assert result == LanguageTuple(("typescript", "javascript"))

        result = LanguageUtils._detect_language(Filename("config.development.json"))
        assert result == LanguageTuple(("json",))

        result = LanguageUtils._detect_language(Filename("component.test.js"))
        assert result == LanguageTuple(("javascript",))

    def test_get_file_languages_single_file(self) -> None:
        """Test get_file_languages with a single file."""
        files_path = FilesPath(("path/to/test.py",))

        with patch("os.path.basename", return_value="test.py"):
            result = LanguageUtils.get_file_languages(files_path)

        assert isinstance(result, Languages)
        assert "path/to/test.py" in result
        assert result["path/to/test.py"] == {"python"}

    def test_get_file_languages_multiple_files(self) -> None:
        """Test get_file_languages with multiple files."""
        files_path = FilesPath(
            ("src/main.py", "frontend/app.js", "styles/main.css", "docs/README.md")
        )

        def mock_basename(path):
            return path.split("/")[-1]

        with patch("os.path.basename", side_effect=mock_basename):
            result = LanguageUtils.get_file_languages(files_path)

        assert isinstance(result, Languages)
        assert len(result) == 4
        assert result["src/main.py"] == {"python"}
        assert result["frontend/app.js"] == {"javascript"}
        assert result["styles/main.css"] == {"css"}
        assert result["docs/README.md"] == {"markdown"}

    def test_get_file_languages_typescript_files(self) -> None:
        """Test get_file_languages with TypeScript files that have multiple
        languages."""
        files_path = FilesPath(("src/component.ts", "src/component.tsx"))

        def mock_basename(path):
            return path.split("/")[-1]

        with patch("os.path.basename", side_effect=mock_basename):
            result = LanguageUtils.get_file_languages(files_path)

        assert isinstance(result, Languages)
        assert result["src/component.ts"] == {"typescript", "javascript"}
        assert result["src/component.tsx"] == {"typescript", "javascript"}

    def test_get_file_languages_mixed_extensions(self) -> None:
        """Test get_file_languages with mixed known and unknown extensions."""
        files_path = FilesPath(("known.py", "unknown.xyz", "noext", "config.json"))

        def mock_basename(path):
            return path.split("/")[-1]

        with patch("os.path.basename", side_effect=mock_basename):
            result = LanguageUtils.get_file_languages(files_path)

        assert isinstance(result, Languages)
        # Only files with detected languages should be in result
        assert "known.py" in result
        assert result["known.py"] == {"python"}
        assert "config.json" in result
        assert result["config.json"] == {"json"}
        # Files without detected languages should not be in result
        assert "unknown.xyz" not in result
        assert "noext" not in result

    def test_get_file_languages_empty_input(self) -> None:
        """Test get_file_languages with empty file list."""
        files_path = FilesPath(())
        result = LanguageUtils.get_file_languages(files_path)

        assert isinstance(result, Languages)
        assert len(result) == 0

    def test_get_file_languages_duplicate_files(self) -> None:
        """Test get_file_languages with duplicate file paths."""
        files_path = FilesPath(("test.py", "test.py", "other.js"))  # Duplicate

        def mock_basename(path):
            return path.split("/")[-1]

        with patch("os.path.basename", side_effect=mock_basename):
            result = LanguageUtils.get_file_languages(files_path)

        assert isinstance(result, Languages)
        # Should handle duplicates correctly
        assert "test.py" in result
        assert result["test.py"] == {"python"}
        assert "other.js" in result
        assert result["other.js"] == {"javascript"}

    def test_get_file_languages_complex_paths(self) -> None:
        """Test get_file_languages with complex file paths."""
        files_path = FilesPath(
            (
                "/absolute/path/to/file.py",
                "../relative/path/script.js",
                "./current/dir/style.css",
                "simple.go",
            )
        )

        def mock_basename(path):
            return path.split("/")[-1]

        with patch("os.path.basename", side_effect=mock_basename):
            result = LanguageUtils.get_file_languages(files_path)

        assert isinstance(result, Languages)
        assert len(result) == 4
        assert result["/absolute/path/to/file.py"] == {"python"}
        assert result["../relative/path/script.js"] == {"javascript"}
        assert result["./current/dir/style.css"] == {"css"}
        assert result["simple.go"] == {"go"}

    @pytest.mark.parametrize(
        "extension,expected_languages",
        [
            ("py", ("python",)),
            ("js", ("javascript",)),
            ("ts", ("typescript", "javascript")),
            ("css", ("css",)),
            ("html", ("html",)),
            ("java", ("java",)),
            ("go", ("go",)),
            ("rb", ("ruby",)),
            ("php", ("php",)),
            ("cs", ("csharp",)),
            ("unknown", ()),
        ],
    )
    def test_detect_language_parametrized(self, extension, expected_languages) -> None:
        """Parametrized test for language detection."""
        filename = f"test.{extension}"
        result = LanguageUtils._detect_language(Filename(filename))
        assert result == LanguageTuple(expected_languages)
