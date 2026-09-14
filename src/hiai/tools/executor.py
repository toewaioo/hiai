"""Tool registry and execution dispatcher."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from hiai.exceptions import MalformedToolCallError, ToolError
from hiai.models import ToolResult
from hiai.tools.filesystem import FileSystemTools
from hiai.tools.schemas import get_tool_definitions


class ToolRegistry:
    """Registry and executor for all available tools."""

    def __init__(self, project_root: Path, auto_approve: bool = False) -> None:
        self.project_root = project_root
        self.auto_approve = auto_approve
        self.fs = FileSystemTools(project_root)
        self._handlers: dict[str, Any] = {
            "read_file": self._handle_read_file,
            "write_file": self._handle_write_file,
            "list_files": self._handle_list_files,
            "search_files": self._handle_search_files,
        }

    def get_definitions(self) -> list[dict]:
        """Return tool definitions for the AI model."""
        return get_tool_definitions()

    def execute(self, name: str, arguments: str | dict) -> str:
        """Execute a tool by name and return the JSON result string."""
        handler = self._handlers.get(name)
        if not handler:
            error = ToolResult(
                status="error",
                message=f"Unknown tool: {name}",
            )
            return json.dumps(error.to_json())

        try:
            if isinstance(arguments, str):
                args = json.loads(arguments)
            elif isinstance(arguments, dict):
                args = arguments
            else:
                raise MalformedToolCallError(
                    f"Invalid arguments type: {type(arguments)}"
                )
        except json.JSONDecodeError as e:
            raise MalformedToolCallError(
                f"Invalid JSON in tool arguments: {e}"
            ) from e

        try:
            result = handler(args)
            return json.dumps(result.to_json())
        except ToolError as e:
            error = ToolResult(
                status="error",
                message=str(e),
            )
            return json.dumps(error.to_json())
        except Exception as e:
            error = ToolResult(
                status="error",
                message=f"Tool execution failed: {e}",
            )
            return json.dumps(error.to_json())

    def _handle_read_file(self, args: dict[str, Any]) -> ToolResult:
        """Handle read_file tool call."""
        path = args.get("path", "")
        if not path:
            return ToolResult(status="error", message="Missing required parameter: path")
        return self.fs.read_file(path)

    def _handle_write_file(self, args: dict[str, Any]) -> ToolResult:
        """Handle write_file tool call."""
        path = args.get("path", "")
        content = args.get("content", "")
        if not path:
            return ToolResult(status="error", message="Missing required parameter: path")
        if content is None:
            return ToolResult(status="error", message="Missing required parameter: content")

        from hiai.permissions import is_sensitive
        from hiai.utils.paths import resolve_safe_path
        from hiai.terminal import prompt_write

        try:
            target = resolve_safe_path(self.project_root, path)
        except ValueError as e:
            return ToolResult(status="error", path=path, message=str(e))

        is_new = not target.exists()
        size = len(content.encode("utf-8"))

        if not self.auto_approve:
            approved = prompt_write(path, is_new, size)
            if not approved:
                return ToolResult(
                    status="cancelled",
                    path=path,
                    message="User denied the write operation.",
                )

        return self.fs.write_file(path, content)

    def _handle_list_files(self, args: dict[str, Any]) -> ToolResult:
        """Handle list_files tool call."""
        path = args.get("path", ".")
        recursive = args.get("recursive", True)
        return self.fs.list_files(path, recursive)

    def _handle_search_files(self, args: dict[str, Any]) -> ToolResult:
        """Handle search_files tool call."""
        query = args.get("query", "")
        if not query:
            return ToolResult(status="error", message="Missing required parameter: query")
        path = args.get("path", ".")
        max_results = args.get("max_results", 50)
        return self.fs.search_files(query, path, max_results)
