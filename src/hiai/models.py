"""Typed data structures for HIAI."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AppConfig:
    """Application configuration."""

    model: str = "openrouter/free"
    base_url: str = "https://openrouter.ai/api/v1"
    api_key: str = ""
    timeout: int = 120
    max_iterations: int = 20
    max_read_bytes: int = 1_000_000
    max_write_bytes: int = 2_000_000
    theme: str = "auto"


@dataclass
class ToolResult:
    """Result from a tool execution."""

    status: str
    path: str = ""
    content: str = ""
    bytes: int = 0
    message: str = ""
    files: list[str] = field(default_factory=list)
    matches: list[dict[str, Any]] = field(default_factory=list)
    operation: str = ""
    query: str = ""

    def to_json(self) -> dict[str, Any]:
        d: dict[str, Any] = {"status": self.status}
        if self.path:
            d["path"] = self.path
        if self.content:
            d["content"] = self.content
        if self.bytes:
            d["bytes"] = self.bytes
        if self.message:
            d["message"] = self.message
        if self.files:
            d["files"] = self.files
        if self.matches:
            d["matches"] = self.matches
        if self.operation:
            d["operation"] = self.operation
        if self.query:
            d["query"] = self.query
        return d


@dataclass
class APIMessage:
    """OpenRouter/OpenAI compatible message."""

    role: str
    content: str = ""
    tool_calls: list[dict[str, Any]] | None = None
    tool_call_id: str | None = None
    name: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"role": self.role}
        if self.content:
            d["content"] = self.content
        if self.tool_calls:
            d["tool_calls"] = self.tool_calls
        if self.tool_call_id:
            d["tool_call_id"] = self.tool_call_id
        if self.name:
            d["name"] = self.name
        return d


@dataclass
class APIError:
    """Structured API error."""

    message: str
    code: int | None = None
    error_type: str = ""


@dataclass
class ToolDefinition:
    """Definition of a tool for the AI model."""

    name: str
    description: str
    parameters: dict[str, Any]

    def to_schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }
