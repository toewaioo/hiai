"""Utility functions for path operations."""

from __future__ import annotations

import fnmatch
import sys
from pathlib import Path

from hiai.constants import IGNORED_DIRS


def get_platform_config_dir() -> Path:
    """Return platform-appropriate configuration directory."""
    if sys.platform == "win32":
        appdata = Path.home() / "AppData" / "Roaming"
        if appdata.exists():
            return appdata / "hiai"
        return Path.home() / ".config" / "hiai"
    elif sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "hiai"
    else:
        return Path.home() / ".config" / "hiai"


def resolve_safe_path(project_root: Path, relative_path: str) -> Path:
    """Resolve a path safely within the project root.

    Returns the resolved path if safe, raises ValueError if it escapes.
    """
    if not relative_path:
        return project_root

    candidate = (project_root / relative_path).resolve()
    project_resolved = project_root.resolve()

    # Use is_relative_to instead of str().startswith() to avoid sibling-dir
    # bypass (e.g. project "/home/user/proj" matching "/home/user/project-evil").
    if not candidate.is_relative_to(project_resolved):
        raise ValueError(f"Path escapes project root: {relative_path}")

    return candidate


def should_ignore_dir(dirname: str) -> bool:
    """Check if a directory name should be ignored."""
    return dirname in IGNORED_DIRS


def match_ignored(name: str) -> bool:
    """Check if a name matches any ignore pattern."""
    for pattern in IGNORED_DIRS:
        if fnmatch.fnmatch(name, pattern):
            return True
    return False


def is_sensitive_file(path: Path) -> bool:
    """Check if a file matches sensitive file patterns."""
    from hiai.constants import SENSITIVE_PATTERNS

    name = path.name
    for pattern in SENSITIVE_PATTERNS:
        if fnmatch.fnmatch(name, pattern):
            return True
    return False
