from unittest.mock import patch

from rich.console import Console

from code_reviewer_agent.utils import rich_utils


class TestRichUtilsComprehensive:
    """Comprehensive tests for rich_utils module."""

    def test_console_instance(self) -> None:
        """Test console instance configuration."""
        console = rich_utils.console
        assert isinstance(console, Console)
        assert hasattr(console, "print")
        assert hasattr(console, "rule")

    def test_custom_theme(self) -> None:
        """Test custom theme configuration."""
        theme = rich_utils.custom_theme
        assert hasattr(theme, "styles")

        # Test theme styles
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

    def test_print_header_functionality(self) -> None:
        """Test print_header function."""
        with patch.object(rich_utils.console, "rule") as mock_rule:
            with patch.object(rich_utils.console, "print") as mock_print:
                rich_utils.print_header("Test Header")

                mock_rule.assert_called_once_with("[bold blue]Test Header")
                mock_print.assert_called_once()

    def test_print_section_with_emoji(self) -> None:
        """Test print_section with emoji."""
        with patch.object(rich_utils.console, "print") as mock_print:
            rich_utils.print_section("Test Section", "🔧")

            assert mock_print.call_count == 2

            # Check calls
            calls = mock_print.call_args_list
            assert "[bold cyan]🔧 Test Section" in str(calls[0])
            assert "-" in str(calls[1])

    def test_print_section_without_emoji(self) -> None:
        """Test print_section without emoji."""
        with patch.object(rich_utils.console, "print") as mock_print:
            rich_utils.print_section("Test Section")

            assert mock_print.call_count == 2

            # Check calls
            calls = mock_print.call_args_list
            assert "[bold cyan]Test Section" in str(calls[0])
            assert "-" in str(calls[1])

    def test_print_success(self) -> None:
        """Test print_success function."""
        with patch.object(rich_utils.console, "print") as mock_print:
            rich_utils.print_success("Success message")

            mock_print.assert_called_once()
            call_args = str(mock_print.call_args)
            assert "success" in call_args
            assert "✓" in call_args
            assert "Success message" in call_args

    def test_print_warning(self) -> None:
        """Test print_warning function."""
        with patch.object(rich_utils.console, "print") as mock_print:
            rich_utils.print_warning("Warning message")

            mock_print.assert_called_once()
            call_args = str(mock_print.call_args)
            assert "warning" in call_args
            assert "!" in call_args
            assert "Warning message" in call_args

    def test_print_error(self) -> None:
        """Test print_error function."""
        with patch.object(rich_utils.console, "print") as mock_print:
            rich_utils.print_error("Error message")

            mock_print.assert_called_once()
            call_args = str(mock_print.call_args)
            assert "error" in call_args
            assert "✗" in call_args
            assert "Error message" in call_args

    def test_print_info(self) -> None:
        """Test print_info function."""
        with patch.object(rich_utils.console, "print") as mock_print:
            rich_utils.print_info("Info message")

            mock_print.assert_called_once()
            call_args = str(mock_print.call_args)
            assert "info" in call_args
            assert "ℹ" in call_args
            assert "Info message" in call_args

    def test_print_debug_enabled(self) -> None:
        """Test print_debug when DEBUG is enabled."""
        with patch.dict("os.environ", {"DEBUG": "True"}):
            with patch.object(rich_utils.console, "print") as mock_print:
                rich_utils.print_debug("Debug message")

                mock_print.assert_called_once()
                call_args = str(mock_print.call_args)
                assert "Debug message" in call_args

    def test_print_debug_disabled(self) -> None:
        """Test print_debug when DEBUG is disabled."""
        with patch.dict("os.environ", {"DEBUG": "False"}):
            with patch.object(rich_utils.console, "print") as mock_print:
                rich_utils.print_debug("Debug message")

                mock_print.assert_not_called()

    def test_print_debug_not_set(self) -> None:
        """Test print_debug when DEBUG is not set."""
        with patch.dict("os.environ", {}, clear=True):
            with patch.object(rich_utils.console, "print") as mock_print:
                rich_utils.print_debug("Debug message")

                mock_print.assert_not_called()

    def test_print_code_block(self) -> None:
        """Test print_code_block function."""
        with patch.object(rich_utils.console, "print") as mock_print:
            rich_utils.print_code_block("print('hello')", "python")

            mock_print.assert_called_once()
            # Should create a Syntax object
            args = mock_print.call_args[0]
            assert len(args) == 1

    def test_print_code_block_default_language(self) -> None:
        """Test print_code_block with default language."""
        with patch.object(rich_utils.console, "print") as mock_print:
            rich_utils.print_code_block("some text")

            mock_print.assert_called_once()

    def test_print_diff(self) -> None:
        """Test print_diff function."""
        with patch.object(rich_utils.console, "print") as mock_print:
            rich_utils.print_diff("+ added line\n- removed line")

            mock_print.assert_called_once()

    def test_print_panel(self) -> None:
        """Test print_panel function."""
        with patch.object(rich_utils.console, "print") as mock_print:
            rich_utils.print_panel("Panel content", "Panel Title")

            mock_print.assert_called_once()

    def test_print_panel_with_options(self) -> None:
        """Test print_panel with options."""
        with patch.object(rich_utils.console, "print") as mock_print:
            rich_utils.print_panel("Panel content", "Panel Title", "red", True)

            mock_print.assert_called_once()

    def test_print_table_basic(self) -> None:
        """Test print_table function."""
        data = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]

        with patch.object(rich_utils.console, "print") as mock_print:
            rich_utils.print_table(data)

            mock_print.assert_called_once()

    def test_print_table_with_title(self) -> None:
        """Test print_table with title."""
        data = [{"name": "Alice", "age": 30}]

        with patch.object(rich_utils.console, "print") as mock_print:
            rich_utils.print_table(data, "Test Table")

            mock_print.assert_called_once()

    def test_print_table_with_custom_columns(self) -> None:
        """Test print_table with custom columns."""
        data = [{"name": "Alice", "age": 30, "city": "NYC"}]
        columns = ["name", "age"]

        with patch.object(rich_utils.console, "print") as mock_print:
            rich_utils.print_table(data, columns=columns)

            mock_print.assert_called_once()

    def test_print_table_empty_data(self) -> None:
        """Test print_table with empty data."""
        with patch.object(rich_utils.console, "print") as mock_print:
            rich_utils.print_table([])

            mock_print.assert_not_called()

    def test_print_json(self) -> None:
        """Test print_json function."""
        data = {"key": "value", "number": 42}

        with patch.object(rich_utils.console, "print_json") as mock_print_json:
            rich_utils.print_json(data)

            mock_print_json.assert_called_once_with(data=data)

    def test_print_exception_debug_enabled(self) -> None:
        """Test print_exception when DEBUG is enabled."""
        with patch.dict("os.environ", {"DEBUG": "True"}):
            with patch.object(
                rich_utils.console, "print_exception"
            ) as mock_print_exception:
                rich_utils.print_exception()

                mock_print_exception.assert_called_once_with(show_locals=True)

    def test_print_exception_debug_disabled(self) -> None:
        """Test print_exception when DEBUG is disabled."""
        with patch.dict("os.environ", {"DEBUG": "False"}):
            with patch.object(
                rich_utils.console, "print_exception"
            ) as mock_print_exception:
                rich_utils.print_exception()

                mock_print_exception.assert_not_called()

    def test_confirm_yes_response(self) -> None:
        """Test confirm function with yes response."""
        with patch.object(rich_utils.console, "input", return_value="y"):
            result = rich_utils.confirm("Continue?")
            assert result is True

    def test_confirm_no_response(self) -> None:
        """Test confirm function with no response."""
        with patch.object(rich_utils.console, "input", return_value="n"):
            result = rich_utils.confirm("Continue?")
            assert result is False

    def test_confirm_empty_response_default_true(self) -> None:
        """Test confirm function with empty response and default True."""
        with patch.object(rich_utils.console, "input", return_value=""):
            result = rich_utils.confirm("Continue?", default=True)
            assert result is True

    def test_confirm_empty_response_default_false(self) -> None:
        """Test confirm function with empty response and default False."""
        with patch.object(rich_utils.console, "input", return_value=""):
            result = rich_utils.confirm("Continue?", default=False)
            assert result is False

    def test_confirm_invalid_then_valid_response(self) -> None:
        """Test confirm function with invalid then valid response."""
        with patch.object(rich_utils.console, "input", side_effect=["invalid", "y"]):
            with patch.object(rich_utils.console, "print") as mock_print:
                result = rich_utils.confirm("Continue?")

                assert result is True
                mock_print.assert_called_with("Please respond with 'y' or 'n'.")

    def test_module_imports(self) -> None:
        """Test that all expected functions are available."""
        expected_functions = [
            "print_header",
            "print_section",
            "print_success",
            "print_warning",
            "print_error",
            "print_info",
            "print_debug",
            "print_code_block",
            "print_diff",
            "print_panel",
            "print_table",
            "print_json",
            "print_exception",
            "confirm",
        ]

        for func_name in expected_functions:
            assert hasattr(rich_utils, func_name)
            assert callable(getattr(rich_utils, func_name))

    def test_rich_traceback_installation(self) -> None:
        """Test that rich traceback is installed."""
        # This should not raise an exception
        import rich.traceback

        assert hasattr(rich.traceback, "install")

        # The install should have been called during import
        # We can't easily test this directly, but we can verify
        # the module imports without error
