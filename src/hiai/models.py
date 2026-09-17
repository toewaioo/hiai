"""Typed data structures for HIAI."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Provider(Enum):
    """Supported AI providers."""

    OPENROUTER = "openrouter"
    GROQ = "groq"


class AgentState(Enum):
    """Agent execution states."""

    IDLE = "idle"
    THINKING = "thinking"
    READING = "reading"
    WRITING = "writing"
    EXECUTING = "executing"
    SEARCHING = "searching"
    WAITING_APPROVAL = "waiting_approval"
    ERROR = "error"
    DEAD = "dead"

    @property
    def icon(self) -> str:
        """Return display icon for state."""
        icons = {
            AgentState.IDLE: "○",
            AgentState.THINKING: "◎",
            AgentState.READING: "📄",
            AgentState.WRITING: "✏️",
            AgentState.EXECUTING: "⌘",
            AgentState.SEARCHING: "🔎",
            AgentState.WAITING_APPROVAL: "?",
            AgentState.ERROR: "✗",
            AgentState.DEAD: "💀",
        }
        return icons.get(self, "·")

    @property
    def description(self) -> str:
        """Return human-readable description."""
        descriptions = {
            AgentState.IDLE: "Idle",
            AgentState.THINKING: "Thinking",
            AgentState.READING: "Reading file",
            AgentState.WRITING: "Writing file",
            AgentState.EXECUTING: "Executing command",
            AgentState.SEARCHING: "Searching",
            AgentState.WAITING_APPROVAL: "Waiting for approval",
            AgentState.ERROR: "Error occurred",
            AgentState.DEAD: "Agent stopped",
        }
        return descriptions.get(self, "Unknown")


@dataclass
class AppConfig:
    """Application configuration."""

    provider: str = "openrouter"
    model: str = "openrouter/free"
    base_url: str = "https://openrouter.ai/api/v1"
    api_key: str = ""
    timeout: int = 120
    max_iterations: int = 20
    max_read_bytes: int = 1_000_000
    max_write_bytes: int = 2_000_000
    rate_limit: int = 20  # max API requests per minute
    theme: str = "auto"
    search_provider: str = "tavily"
    search_api_key: str = ""
    search_max_results: int = 5


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
    command: str = ""

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
        if self.command:
            d["command"] = self.command
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
