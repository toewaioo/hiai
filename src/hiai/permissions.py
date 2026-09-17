"""Permission and safety management for file operations."""

from __future__ import annotations

from pathlib import Path

from hiai.constants import SENSITIVE_PATTERNS
from hiai.utils.paths import is_sensitive_file


def needs_write_confirmation(path: Path, auto_approve: bool) -> bool:
    """Check if a write operation needs user confirmation.

    Returns True if the user must be asked before writing.
    """
    if auto_approve:
        return False
    return True


def is_sensitive(path: Path) -> bool:
    """Check if a file is considered sensitive."""
    return is_sensitive_file(path)


def check_path_safety(project_root: Path, target: Path) -> None:
    """Verify the target path is within the project root.

    Raises ValueError if the path escapes the project.
    """
    project_resolved = project_root.resolve()
    target_resolved = target.resolve()

    # Use is_relative_to instead of str().startswith() to avoid sibling-dir
    # bypass (e.g. project "/home/user/proj" matching "/home/user/project-evil").
    if not target_resolved.is_relative_to(project_resolved):
        raise ValueError(f"Path escapes project root: {target}")
