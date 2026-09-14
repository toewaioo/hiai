"""Custom exceptions for HIAI."""


class HIAIError(Exception):
    """Base exception for HIAI."""


class ConfigError(HIAIError):
    """Configuration-related errors."""


class APIKeyError(ConfigError):
    """API key not configured or invalid."""


class ClientError(HIAIError):
    """HTTP client errors."""


class APIRequestError(ClientError):
    """API request failed."""


class APIResponseError(ClientError):
    """API returned an error response."""


class RateLimitError(APIResponseError):
    """Rate limit exceeded."""


class AuthenticationError(APIResponseError):
    """Authentication failed."""


class TimeoutError(ClientError):
    """Request timed out."""


class ToolError(HIAIError):
    """Tool execution errors."""


class PathSecurityError(ToolError):
    """Path escapes project root."""


class FileReadError(ToolError):
    """File read failed."""


class FileWriteError(ToolError):
    """File write failed."""


class PermissionDeniedError(ToolError):
    """User denied the operation."""


class AgentError(HIAIError):
    """Agent loop errors."""


class MaxIterationsError(AgentError):
    """Agent exceeded maximum iterations."""


class MalformedToolCallError(AgentError):
    """Model returned malformed tool call arguments."""
