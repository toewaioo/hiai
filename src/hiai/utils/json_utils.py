"""JSON utility functions."""

from __future__ import annotations

import json
from typing import Any


def parse_json_safely(text: str) -> dict[str, Any] | None:
    """Parse JSON string safely, returning None on failure."""
    try:
        result = json.loads(text)
        if isinstance(result, dict):
            return result
        return None
    except (json.JSONDecodeError, TypeError):
        return None


def format_json(data: Any, indent: int = 2) -> str:
    """Format data as a JSON string."""
    return json.dumps(data, indent=indent, ensure_ascii=False)
