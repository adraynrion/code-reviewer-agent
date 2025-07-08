"""Rich text utilities for the code reviewer agent."""

import os
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.theme import Theme
from rich.traceback import install as install_rich_traceback

# Define a custom theme for consistent styling
custom_theme = Theme(
    {
        "info": "cyan",
        "success": "green",
        "warning": "yellow",
        "error": "red",
        "highlight": "magenta",
        "dim": "dim",
        "code": "blue",
    }
)

# Global console instance with custom theme and settings
console = Console(theme=custom_theme, highlight=False)

# Install rich traceback handler
install_rich_traceback(show_locals=True)


def print_header(text: str) -> None:
    """Print a styled header.

    Args:
        text: Header text to display

    """
    console.rule(f"[bold blue]{text}")
    console.print()


def print_section(text: str, emoji: str = "") -> None:
    """Print a section header with an optional emoji.

    Args:
        text: Section header to display
        emoji: Optional emoji to display before the text

    """
    prefix = f"{emoji} " if emoji else ""
    console.print(f"[bold cyan]{prefix}{text}")
    # Calculate display width: most emojis have display width of 2
    emoji_display_width = (
        2 if emoji and len(emoji.encode()) > len(emoji) else len(emoji)
    )
    console.print("-" * (len(text) + (emoji_display_width + 1 if emoji else 0)))


def print_success(text: str) -> None:
    """Print a success message.

    Args:
        text: Success message to display

    """
    console.print(f"[success]✓ {text}[/]")


def print_warning(text: str) -> None:
    """Print a warning message.

    Args:
        text: Warning message to display

    """
    console.print(f"[warning]! {text}[/]")


def print_error(text: str) -> None:
    """Print an error message.

    Args:
        text: Error message to display

    """
    console.print(f"[error]✗ {text}[/]")


def print_info(text: str) -> None:
    """Print an informational message.

    Args:
        text: Info message to display

    """
    console.print(f"[info]ℹ {text}[/]")


def print_debug(text: str) -> None:
    """Print a debug message. ONLY if DEBUG is enabled.

    Args:
        text: Debug message to display

    """
    if os.getenv("DEBUG") == "True":
        console.print(f"[dim]{text}[/]")


def print_code_block(code: str, language: str = "text") -> None:
    """Print a block of code with syntax highlighting.

    Args:
        code: The code to display
        language: Language for syntax highlighting

    """
    console.print(Syntax(code, language, theme="monokai"))


def print_diff(diff_content: str) -> None:
    """Print a diff with proper formatting.

    Args:
        diff_content: The diff content to display

    """
    console.print(Syntax(diff_content, "diff", theme="monokai", line_numbers=True))


def print_panel(
    text: str, title: str = "", border_style: str = "blue", expand: bool = False
) -> None:
    """Print text in a panel.

    Args:
        text: Text to display in the panel
        title: Optional panel title
        border_style: Style for the panel border
        expand: Whether to expand the panel to full width

    """
    console.print(Panel(text, title=title, border_style=border_style, expand=expand))


def print_table(
    data: list[dict], title: str = "", columns: list[str] | None = None
) -> None:
    """Print tabular data.

    Args:
        data: List of dictionaries containing row data
        title: Optional table title
        columns: List of column names (uses dict keys if not provided)

    """
    if not data:
        return

    if columns is None:
        columns = list(data[0].keys())

    table = Table(title=title, show_lines=True)

    # Add columns
    for col in columns:
        table.add_column(col, style="code")

    # Add rows
    for row in data:
        table.add_row(*[str(row.get(col, "")) for col in columns])

    console.print(table)


def confirm(prompt: str, default: bool = True) -> bool:
    """Prompt for confirmation with a default value.

    Args:
        prompt: The prompt to display
        default: Default value if user just presses Enter

    Returns:
        bool: User's confirmation

    """
    suffix = "[Y/n]" if default else "[y/N]"
    while True:
        response = console.input(f"{prompt} {suffix} ").strip().lower()
        if not response:
            return default
        if response in ("y", "yes"):
            return True
        if response in ("n", "no"):
            return False
        console.print("Please respond with 'y' or 'n'.")


def print_exception() -> None:
    """Print the current exception with rich formatting.

    ONLY if DEBUG is enabled.

    """
    if os.getenv("DEBUG") == "True":
        console.print_exception(show_locals=True)


def print_json(data: Any) -> None:
    """Pretty print JSON data.

    Args:
        data: JSON-serializable data to print

    """
    console.print_json(data=data)
