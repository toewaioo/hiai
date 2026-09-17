"""Stdlib-only .env file loader.

Parses simple KEY=VALUE files and populates os.environ for keys that are
not already set, so explicit environment variables always take precedence.
"""

from __future__ import annotations

import os
from pathlib import Path


def load_dotenv(path: Path) -> bool:
    """Load environment variables from a .env file.

    Existing environment variables are never overridden. Returns True if the
    file was loaded, False if it was missing/unreadable.
    """
    try:
        if not path.is_file():
            return False
        text = path.read_text(encoding="utf-8")
    except OSError:
        return False

    for raw_line in text.splitlines():
        line = raw_line.strip()
        # Skip blank lines and comments
        if not line or line.startswith("#"):
            continue
        # Strip optional "export " prefix
        if line.startswith("export "):
            line = line[7:].lstrip()
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        # Strip surrounding quotes and inline comments after value
        value = value.strip()
        if "#" in value and not (value.startswith('"') or value.startswith("'")):
            value = value.split("#", 1)[0].rstrip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
            value = value[1:-1]
        if not key:
            continue
        # Never override variables already present in the environment
        if key not in os.environ:
            os.environ[key] = value

    return True


def load_default_env(extra_dirs: list[Path] | None = None) -> None:
    """Load .env from the current directory and any extra directories.

    Best-effort: missing files are silently ignored.
    """
    candidates = [Path.cwd() / ".env"]
    if extra_dirs:
        for d in extra_dirs:
            candidates.append(Path(d) / ".env")
    for candidate in candidates:
        load_dotenv(candidate)
