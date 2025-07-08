import os
from unittest.mock import patch

import pytest
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.theme import Theme

from code_reviewer_agent.utils import rich_utils


class TestRichUtilsConstants:
    """Test Rich utils constants and setup."""

    def test_custom_theme_structure(self) -> None:
        """Test that custom_theme has expected colors."""
        theme = rich_utils.custom_theme
        assert isinstance(theme, Theme)

        # Check that all expected styles are defined
        expected_styles = [
            "info",
            "success",
            "warning",
            "error",
            "highlight",
            "dim",
            "code",
        ]

        for style in expected_styles:
            assert style in theme.styles

    def test_console_configuration(self) -> None:
        """Test that console is properly configured."""
        console = rich_utils.console
        assert isinstance(console, Console)
        # Test console configuration without accessing internal attributes
        assert hasattr(console, "print")
        assert hasattr(console, "rule")


class TestPrintFunctions:
    """Test print functions that output to console."""

    def test_print_header(self, capsys) -> None:
        """Test print_header function."""
        with patch.object(rich_utils.console, "rule") as mock_rule:
            with patch.object(rich_utils.console, "print") as mock_print:
                rich_utils.print_header("Test Header")

                mock_rule.assert_called_once_with("[bold blue]Test Header")
                mock_print.assert_called_once_with()

    def test_print_section_with_emoji(self, capsys) -> None:
        """Test print_section with emoji."""
        with patch.object(rich_utils.console, "print") as mock_print:
            rich_utils.print_section("Test Section", "🔧")

            # Should be called twice: once for header, once for separator
            assert mock_print.call_count == 2

            # Check first call (header with emoji)
            first_call = mock_print.call_args_list[0]
            assert "[bold cyan]🔧 Test Section" in str(first_call)

            # Check second call (separator line)
            second_call = mock_print.call_args_list[1]
            # Length should include emoji (2 chars) + space (1 char) + text length
            expected_length = len("Test Section") + 3
            assert "-" * expected_length in str(second_call)

    def test_print_section_without_emoji(self, capsys) -> None:
        """Test print_section without emoji."""
        with patch.object(rich_utils.console, "print") as mock_print:
            rich_utils.print_section("Test Section")

            assert mock_print.call_count == 2

            # Check first call (header without emoji)
            first_call = mock_print.call_args_list[0]
            assert "[bold cyan]Test Section" in str(first_call)
            assert "🔧" not in str(first_call)

            # Check second call (separator line)
            second_call = mock_print.call_args_list[1]
            expected_length = len("Test Section")
            assert "-" * expected_length in str(second_call)

    def test_print_success(self, capsys) -> None:
        """Test print_success function."""
        with patch.object(rich_utils.console, "print") as mock_print:
            rich_utils.print_success("Operation completed")

            mock_print.assert_called_once_with("[success]✓ Operation completed[/]")

    def test_print_warning(self, capsys) -> None:
        """Test print_warning function."""
        with patch.object(rich_utils.console, "print") as mock_print:
            rich_utils.print_warning("This is a warning")

            mock_print.assert_called_once_with("[warning]! This is a warning[/]")

    def test_print_error(self, capsys) -> None:
        """Test print_error function."""
        with patch.object(rich_utils.console, "print") as mock_print:
            rich_utils.print_error("Something went wrong")

            mock_print.assert_called_once_with("[error]✗ Something went wrong[/]")

    def test_print_info(self, capsys) -> None:
        """Test print_info function."""
        with patch.object(rich_utils.console, "print") as mock_print:
            rich_utils.print_info("Information message")

            mock_print.assert_called_once_with("[info]ℹ Information message[/]")

    def test_print_debug_enabled(self, capsys) -> None:
        """Test print_debug when DEBUG is enabled."""
        with patch.dict(os.environ, {"DEBUG": "True"}):
            with patch.object(rich_utils.console, "print") as mock_print:
                rich_utils.print_debug("Debug message")

                mock_print.assert_called_once_with("[dim]Debug message[/]")

    def test_print_debug_disabled(self, capsys) -> None:
        """Test print_debug when DEBUG is disabled."""
        with patch.dict(os.environ, {"DEBUG": "False"}):
            with patch.object(rich_utils.console, "print") as mock_print:
                rich_utils.print_debug("Debug message")

                mock_print.assert_not_called()

    def test_print_debug_not_set(self, capsys) -> None:
        """Test print_debug when DEBUG environment variable is not set."""
        with patch.dict(os.environ, {}, clear=True):
            with patch.object(rich_utils.console, "print") as mock_print:
                rich_utils.print_debug("Debug message")

                mock_print.assert_not_called()

    def test_print_code_block(self, capsys) -> None:
        """Test print_code_block function."""
        code = "def hello():\n    print('Hello, World!')"

        with patch.object(rich_utils.console, "print") as mock_print:
            rich_utils.print_code_block(code, "python")

            mock_print.assert_called_once()
            # Check that a Syntax object was passed
            call_args = mock_print.call_args[0]
            assert len(call_args) == 1
            assert isinstance(call_args[0], Syntax)

    def test_print_code_block_default_language(self, capsys) -> None:
        """Test print_code_block with default language."""
        code = "Some plain text"

        with patch.object(rich_utils.console, "print") as mock_print:
            rich_utils.print_code_block(code)

            mock_print.assert_called_once()
            call_args = mock_print.call_args[0]
            assert isinstance(call_args[0], Syntax)

    def test_print_diff(self, capsys) -> None:
        """Test print_diff function."""
        diff_content = "+++ added line\n--- removed line"

        with patch.object(rich_utils.console, "print") as mock_print:
            rich_utils.print_diff(diff_content)

            mock_print.assert_called_once()
            call_args = mock_print.call_args[0]
            assert isinstance(call_args[0], Syntax)

    def test_print_panel_basic(self, capsys) -> None:
        """Test print_panel with basic parameters."""
        with patch.object(rich_utils.console, "print") as mock_print:
            rich_utils.print_panel("Panel content")

            mock_print.assert_called_once()
            call_args = mock_print.call_args[0]
            assert isinstance(call_args[0], Panel)

    def test_print_panel_with_options(self, capsys) -> None:
        """Test print_panel with all options."""
        with patch.object(rich_utils.console, "print") as mock_print:
            rich_utils.print_panel(
                "Panel content", title="Test Panel", border_style="red", expand=True
            )

            mock_print.assert_called_once()
            call_args = mock_print.call_args[0]
            assert isinstance(call_args[0], Panel)

    def test_print_json(self, capsys) -> None:
        """Test print_json function."""
        test_data = {"key": "value", "number": 42, "list": [1, 2, 3]}

        with patch.object(rich_utils.console, "print_json") as mock_print_json:
            rich_utils.print_json(test_data)

            mock_print_json.assert_called_once_with(data=test_data)


class TestPrintTable:
    """Test print_table function."""

    def test_print_table_basic(self, capsys) -> None:
        """Test print_table with basic data."""
        data = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]

        with patch.object(rich_utils.console, "print") as mock_print:
            rich_utils.print_table(data)

            mock_print.assert_called_once()
            call_args = mock_print.call_args[0]
            assert isinstance(call_args[0], Table)

    def test_print_table_with_title(self, capsys) -> None:
        """Test print_table with title."""
        data = [{"name": "Alice", "age": 30}]

        with patch.object(rich_utils.console, "print") as mock_print:
            rich_utils.print_table(data, title="User Data")

            mock_print.assert_called_once()
            call_args = mock_print.call_args[0]
            assert isinstance(call_args[0], Table)

    def test_print_table_with_custom_columns(self, capsys) -> None:
        """Test print_table with custom column order."""
        data = [
            {"name": "Alice", "age": 30, "city": "New York"},
            {"name": "Bob", "age": 25, "city": "London"},
        ]
        columns = ["age", "name"]  # Different order, exclude city

        with patch.object(rich_utils.console, "print") as mock_print:
            rich_utils.print_table(data, columns=columns)

            mock_print.assert_called_once()
            call_args = mock_print.call_args[0]
            assert isinstance(call_args[0], Table)

    def test_print_table_empty_data(self, capsys) -> None:
        """Test print_table with empty data."""
        with patch.object(rich_utils.console, "print") as mock_print:
            rich_utils.print_table([])

            mock_print.assert_not_called()

    def test_print_table_missing_columns(self, capsys) -> None:
        """Test print_table with missing column data."""
        data = [{"name": "Alice", "age": 30}, {"name": "Bob"}]  # Missing age

        with patch.object(rich_utils.console, "print") as mock_print:
            rich_utils.print_table(data)

            mock_print.assert_called_once()
            call_args = mock_print.call_args[0]
            assert isinstance(call_args[0], Table)


class TestConfirm:
    """Test confirm function."""

    def test_confirm_yes_response(self) -> None:
        """Test confirm with 'yes' response."""
        with patch.object(rich_utils.console, "input", return_value="y"):
            result = rich_utils.confirm("Continue?")
            assert result is True

    def test_confirm_no_response(self) -> None:
        """Test confirm with 'no' response."""
        with patch.object(rich_utils.console, "input", return_value="n"):
            result = rich_utils.confirm("Continue?")
            assert result is False

    def test_confirm_yes_full_response(self) -> None:
        """Test confirm with 'yes' full response."""
        with patch.object(rich_utils.console, "input", return_value="yes"):
            result = rich_utils.confirm("Continue?")
            assert result is True

    def test_confirm_no_full_response(self) -> None:
        """Test confirm with 'no' full response."""
        with patch.object(rich_utils.console, "input", return_value="no"):
            result = rich_utils.confirm("Continue?")
            assert result is False

    def test_confirm_empty_response_default_true(self) -> None:
        """Test confirm with empty response and default=True."""
        with patch.object(rich_utils.console, "input", return_value=""):
            result = rich_utils.confirm("Continue?", default=True)
            assert result is True

    def test_confirm_empty_response_default_false(self) -> None:
        """Test confirm with empty response and default=False."""
        with patch.object(rich_utils.console, "input", return_value=""):
            result = rich_utils.confirm("Continue?", default=False)
            assert result is False

    def test_confirm_case_insensitive(self) -> None:
        """Test confirm is case insensitive."""
        with patch.object(rich_utils.console, "input", return_value="Y"):
            result = rich_utils.confirm("Continue?")
            assert result is True

        with patch.object(rich_utils.console, "input", return_value="N"):
            result = rich_utils.confirm("Continue?")
            assert result is False

    def test_confirm_whitespace_handling(self) -> None:
        """Test confirm handles whitespace."""
        with patch.object(rich_utils.console, "input", return_value="  y  "):
            result = rich_utils.confirm("Continue?")
            assert result is True

    def test_confirm_invalid_then_valid_response(self) -> None:
        """Test confirm with invalid response followed by valid one."""
        with patch.object(rich_utils.console, "input", side_effect=["invalid", "y"]):
            with patch.object(rich_utils.console, "print") as mock_print:
                result = rich_utils.confirm("Continue?")

                assert result is True
                # Should print error message for invalid input
                mock_print.assert_called_with("Please respond with 'y' or 'n'.")

    def test_confirm_prompt_format_default_true(self) -> None:
        """Test confirm prompt format with default=True."""
        with patch.object(rich_utils.console, "input", return_value="") as mock_input:
            rich_utils.confirm("Continue?", default=True)

            # Check that input was called with correct prompt
            mock_input.assert_called_once_with("Continue? [Y/n] ")

    def test_confirm_prompt_format_default_false(self) -> None:
        """Test confirm prompt format with default=False."""
        with patch.object(rich_utils.console, "input", return_value="") as mock_input:
            rich_utils.confirm("Continue?", default=False)

            # Check that input was called with correct prompt
            mock_input.assert_called_once_with("Continue? [y/N] ")


class TestPrintException:
    """Test print_exception function."""

    def test_print_exception_debug_enabled(self) -> None:
        """Test print_exception when DEBUG is enabled."""
        with patch.dict(os.environ, {"DEBUG": "True"}):
            with patch.object(rich_utils.console, "print_exception") as mock_print_exc:
                rich_utils.print_exception()

                mock_print_exc.assert_called_once_with(show_locals=True)

    def test_print_exception_debug_disabled(self) -> None:
        """Test print_exception when DEBUG is disabled."""
        with patch.dict(os.environ, {"DEBUG": "False"}):
            with patch.object(rich_utils.console, "print_exception") as mock_print_exc:
                rich_utils.print_exception()

                mock_print_exc.assert_not_called()

    def test_print_exception_debug_not_set(self) -> None:
        """Test print_exception when DEBUG is not set."""
        with patch.dict(os.environ, {}, clear=True):
            with patch.object(rich_utils.console, "print_exception") as mock_print_exc:
                rich_utils.print_exception()

                mock_print_exc.assert_not_called()


class TestEnvironmentBehavior:
    """Test environment-dependent behavior."""

    @pytest.mark.parametrize(
        "debug_value,expected_calls",
        [
            ("True", 1),
            ("true", 0),  # Case sensitive
            ("False", 0),
            ("false", 0),
            ("1", 0),  # Only "True" is accepted
            ("", 0),
        ],
    )
    def test_debug_functions_environment_sensitivity(
        self, debug_value, expected_calls
    ) -> None:
        """Test that debug functions respond correctly to DEBUG environment variable."""
        with patch.dict(os.environ, {"DEBUG": debug_value}):
            with patch.object(rich_utils.console, "print") as mock_print:
                rich_utils.print_debug("Test message")
                assert mock_print.call_count == expected_calls

            with patch.object(rich_utils.console, "print_exception") as mock_print_exc:
                rich_utils.print_exception()
                assert mock_print_exc.call_count == expected_calls


class TestIntegration:
    """Integration tests for rich_utils functions."""

    def test_multiple_print_calls(self) -> None:
        """Test multiple print function calls."""
        with patch.object(rich_utils.console, "print") as mock_print:
            rich_utils.print_success("Success")
            rich_utils.print_error("Error")
            rich_utils.print_info("Info")

            assert mock_print.call_count == 3

    def test_styled_output_consistency(self) -> None:
        """Test that styled outputs use consistent formatting."""
        with patch.object(rich_utils.console, "print") as mock_print:
            rich_utils.print_success("Success message")
            rich_utils.print_warning("Warning message")
            rich_utils.print_error("Error message")
            rich_utils.print_info("Info message")

            # Check that all calls include proper styling tags
            calls = [str(call) for call in mock_print.call_args_list]

            # Success should have ✓ symbol and [success] tag
            assert any("✓" in call and "[success]" in call for call in calls)
            # Warning should have ! symbol and [warning] tag
            assert any("!" in call and "[warning]" in call for call in calls)
            # Error should have ✗ symbol and [error] tag
            assert any("✗" in call and "[error]" in call for call in calls)
            # Info should have ℹ symbol and [info] tag
            assert any("ℹ" in call and "[info]" in call for call in calls)

    def test_complex_content_handling(self) -> None:
        """Test handling of complex content with special characters."""
        special_text = "Text with [brackets] and {braces} and <tags>"

        with patch.object(rich_utils.console, "print") as mock_print:
            rich_utils.print_success(special_text)

            call_str = str(mock_print.call_args)
            assert special_text in call_str
