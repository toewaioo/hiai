"""Terminal output formatting and user interaction."""

from __future__ import annotations

import os
import sys
from typing import TextIO

from hiai.constants import ANSI_COLORS


def _supports_color() -> bool:
    """Check if the terminal supports color output."""
    if os.environ.get("NO_COLOR"):
        return False
    if not hasattr(sys.stdout, "isatty"):
        return False
    if not sys.stdout.isatty():
        return False
    term = os.environ.get("TERM", "")
    if "dumb" in term:
        return False
    return True


USE_COLOR = _supports_color()


def _c(code: str, text: str) -> str:
    """Wrap text with ANSI color code if colors are supported."""
    if not USE_COLOR:
        return text
    return f"{ANSI_COLORS.get(code, '')}{text}{ANSI_COLORS['reset']}"


def info(message: str) -> None:
    """Print an informational message."""
    print(_c("cyan", f"ℹ {message}"))


def success(message: str) -> None:
    """Print a success message."""
    print(_c("green", f"✓ {message}"))


def error(message: str) -> None:
    """Print an error message."""
    print(_c("red", f"✗ {message}"), file=sys.stderr)


def warning(message: str) -> None:
    """Print a warning message."""
    print(_c("yellow", f"⚠ {message}"))


def thinking() -> None:
    """Show thinking indicator."""
    print(_c("dim", "HIAI is thinking..."))


def tool_start(tool_name: str) -> None:
    """Show tool execution start."""
    print(_c("cyan", f"⚙ Tool: {tool_name}"))


def tool_complete(tool_name: str) -> None:
    """Show tool execution complete."""
    print(_c("green", f"✓ Tool completed: {tool_name}"))


def tool_error(tool_name: str, message: str) -> None:
    """Show tool execution error."""
    print(_c("red", f"✗ Tool error ({tool_name}): {message}"))


def prompt_write(path: str, is_new: bool, size: int) -> bool:
    """Prompt user to approve a file write."""
    op = "Create" if is_new else "Update"
    size_str = _format_size(size)

    print(_c("yellow", "┌─ File write requested " + "─" * 30))
    print(_c("yellow", f"│ Path: {path}"))
    print(_c("yellow", f"│ Operation: {op}"))
    print(_c("yellow", f"│ Size: {size_str}"))
    print(_c("yellow", "└" + "─" * 40))

    try:
        answer = input(_c("bold", "Allow write? [y/N]: ")).strip().lower()
        return answer in ("y", "yes")
    except (EOFError, KeyboardInterrupt):
        return False


def prompt_sensitive_read(path: str) -> bool:
    """Prompt user to approve reading a sensitive file."""
    print(_c("yellow", f"⚠ Sensitive file detected: {path}"))
    try:
        answer = input(_c("bold", "Allow read? [y/N]: ")).strip().lower()
        return answer in ("y", "yes")
    except (EOFError, KeyboardInterrupt):
        return False


def prompt_api_key() -> str | None:
    """Prompt user to enter an API key."""
    try:
        print(_c("yellow", "Enter your OpenRouter API key:"))
        key = input(_c("bold", "API Key: ")).strip()
        return key if key else None
    except (EOFError, KeyboardInterrupt):
        return None


def print_banner(project_dir: str, model: str) -> None:
    """Print the HIAI banner."""
    from hiai.constants import BANNER

    print(_c("cyan", BANNER))
    print(_c("dim", "HIAI — Local AI Coding Agent"))
    print()
    print(f"  Project: {_c('white', project_dir)}")
    print(f"  Model:   {_c('white', model)}")
    print()


def print_config_display(config: dict[str, str]) -> None:
    """Print configuration in a formatted way."""
    print(_c("bold", "HIAI Configuration"))
    print("─" * 40)
    for key, value in config.items():
        print(f"  {_c('cyan', key + ':'):25s} {value}")
    print()


def _format_size(size_bytes: int) -> str:
    """Format byte size to human-readable string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
