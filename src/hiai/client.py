"""HTTP client for AI providers (OpenRouter, Groq)."""

from __future__ import annotations

import io
import json
import threading
import time
import urllib.error
import urllib.request
from collections import deque
from typing import Any, Callable

from hiai.constants import USER_AGENT
from hiai.exceptions import (
    APIRequestError,
    APIResponseError,
    AuthenticationError,
    RateLimitError,
    TimeoutError,
)


class RateLimiter:
    """Token-bucket rate limiter: max requests per rolling window."""

    def __init__(self, max_requests: int = 20, window_seconds: int = 60) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._timestamps: deque[float] = deque()
        self._lock = threading.Lock()

    def wait(self) -> None:
        """Block until a request slot is available."""
        while True:
            with self._lock:
                now = time.monotonic()
                # Purge timestamps outside the window
                while self._timestamps and self._timestamps[0] <= now - self.window_seconds:
                    self._timestamps.popleft()

                if len(self._timestamps) < self.max_requests:
                    self._timestamps.append(now)
                    return

                # Calculate wait time until the oldest request expires
                wait_until = self._timestamps[0] + self.window_seconds
                wait_seconds = wait_until - now

            if wait_seconds > 0:
                time.sleep(wait_seconds)

    def record(self) -> None:
        """Record a request timestamp without blocking."""
        with self._lock:
            now = time.monotonic()
            while self._timestamps and self._timestamps[0] <= now - self.window_seconds:
                self._timestamps.popleft()
            self._timestamps.append(now)

    @property
    def remaining(self) -> int:
        """Return remaining requests in the current window."""
        with self._lock:
            now = time.monotonic()
            while self._timestamps and self._timestamps[0] <= now - self.window_seconds:
                self._timestamps.popleft()
            return max(0, self.max_requests - len(self._timestamps))


class AIClient:
    """HTTP client for OpenAI-compatible APIs (OpenRouter, Groq)."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout: int = 120,
        provider: str = "openrouter",
        rate_limit: int = 20,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.provider = provider
        self.rate_limiter = RateLimiter(max_requests=rate_limit)

    def _build_url(self, endpoint: str) -> str:
        """Build the full URL, avoiding double /v1/v1."""
        base = self.base_url
        if base.endswith("/api/v1"):
            if endpoint.startswith("/v1/"):
                endpoint = endpoint[3:]
            elif endpoint.startswith("/v1"):
                endpoint = endpoint[3:]
            return f"{base}/{endpoint.lstrip('/')}"
        else:
            if not endpoint.startswith("/"):
                endpoint = f"/{endpoint}"
            return f"{base}{endpoint}"

    def _get_headers(self) -> dict[str, str]:
        """Get request headers based on provider."""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": USER_AGENT,
        }
        if self.provider == "openrouter":
            headers["HTTP-Referer"] = "https://github.com/toewaioo/hiai"
            headers["X-Title"] = "HIAI"
        return headers

    def chat_completion(
        self,
        messages: list[dict[str, Any]],
        model: str,
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.7,
        max_retries: int = 3,
        stream: bool = False,
        on_delta: Callable[[str], None] | None = None,
    ) -> dict[str, Any]:
        """Send a chat completion request.

        Returns the parsed JSON response. When ``stream`` is True, the response
        is consumed as an SSE stream; content deltas are forwarded to
        ``on_delta`` (if provided) and a fully-assembled response dict in the
        same shape as the non-streaming path is returned.

        Raises APIRequestError on network errors.
        Raises APIResponseError on API errors.
        """
        url = self._build_url("/chat/completions")

        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        if tools:
            payload["tools"] = tools
        if stream:
            payload["stream"] = True

        body = json.dumps(payload).encode("utf-8")

        headers = self._get_headers()
        if stream:
            # Accept SSE and disable buffering where supported
            headers["Accept"] = "text/event-stream"
            headers["Cache-Control"] = "no-cache"

        request = urllib.request.Request(
            url, data=body, headers=headers, method="POST"
        )

        last_error: Exception | None = None
        for attempt in range(max_retries):
            # Wait for rate limit slot before each attempt
            self.rate_limiter.wait()

            try:
                if stream:
                    result = self._do_stream_request(request, on_delta)
                else:
                    result = self._do_request(request)
                self.rate_limiter.record()
                return result
            except RateLimitError as e:
                self.rate_limiter.record()
                wait = self._parse_retry_after(e) or (2 ** attempt)
                if attempt < max_retries - 1:
                    time.sleep(wait)
                    continue
                raise
            except (APIRequestError, TimeoutError) as e:
                last_error = e
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                raise
            except APIResponseError as e:
                if e.code and 500 <= e.code < 600 and attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                raise

        raise last_error or APIRequestError("All retries failed")

    def _parse_retry_after(self, error: RateLimitError) -> float | None:
        """Extract Retry-After value from a rate limit error."""
        # Try to parse retry-after from error message
        # Common formats: "Retry-After: 30" or "retry after 30 seconds"
        msg = str(error).lower()
        for keyword in ("retry-after:", "retry after", "try again in"):
            if keyword in msg:
                idx = msg.index(keyword) + len(keyword)
                # Skip whitespace
                original = str(error)
                while idx < len(original) and original[idx] == " ":
                    idx += 1
                digits = ""
                for ch in original[idx:]:
                    if ch.isdigit() or ch == ".":
                        digits += ch
                    else:
                        break
                if digits:
                    try:
                        return min(float(digits), 60.0)
                    except ValueError:
                        pass
        return None

    def _do_request(self, request: urllib.request.Request) -> dict[str, Any]:
        """Execute a single HTTP request."""
        try:
            response = urllib.request.urlopen(request, timeout=self.timeout)
            data = response.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            self._handle_http_error(e)
        except urllib.error.URLError as e:
            raise APIRequestError(f"Network error: {e.reason}") from e
        except TimeoutError:
            raise
        except OSError as e:
            raise APIRequestError(f"Connection error: {e}") from e

        try:
            result = json.loads(data)
        except json.JSONDecodeError as e:
            raise APIRequestError(f"Invalid JSON response: {e}") from e

        if not result.get("choices"):
            raise APIResponseError("No choices in API response")

        return result

    def _do_stream_request(
        self,
        request: urllib.request.Request,
        on_delta: Callable[[str], None] | None,
    ) -> dict[str, Any]:
        """Execute a streaming SSE request and assemble a non-stream-shaped dict.

        Accumulates content and tool_call deltas. Calls on_delta(text) for each
        content chunk. Falls back to buffered JSON if the server ignores the
        stream flag and returns a single JSON body instead of SSE.
        """
        try:
            response = urllib.request.urlopen(request, timeout=self.timeout)
        except urllib.error.HTTPError as e:
            self._handle_http_error(e)
        except urllib.error.URLError as e:
            raise APIRequestError(f"Network error: {e.reason}") from e
        except TimeoutError:
            raise
        except OSError as e:
            raise APIRequestError(f"Connection error: {e}") from e

        content_parts: list[str] = []
        tool_calls_by_index: dict[int, dict[str, Any]] = {}
        usage: dict[str, Any] = {}
        saw_sse = False
        raw_buffer: list[str] = []

        try:
            wrapper = io.TextIOWrapper(response, encoding="utf-8", errors="replace")
            for raw_line in wrapper:
                line = raw_line.rstrip("\r\n")
                if not line:
                    continue
                if not line.startswith("data:"):
                    # Could be a non-SSE JSON body if the server ignored
                    # stream=true. Buffer raw lines for fallback parsing.
                    raw_buffer.append(raw_line)
                    continue
                saw_sse = True
                data_str = line[5:].strip()
                if data_str == "[DONE]":
                    break
                try:
                    chunk = json.loads(data_str)
                except json.JSONDecodeError:
                    continue

                # Capture usage if the final chunk carries it.
                chunk_usage = chunk.get("usage")
                if isinstance(chunk_usage, dict):
                    usage = chunk_usage

                choices = chunk.get("choices") or []
                if not choices:
                    continue
                delta = choices[0].get("delta", {})
                if not isinstance(delta, dict):
                    continue

                text = delta.get("content")
                if text:
                    content_parts.append(text)
                    if on_delta is not None:
                        try:
                            on_delta(text)
                        except Exception:
                            # A failing callback must not break the stream.
                            pass

                for tc_delta in delta.get("tool_calls") or []:
                    if not isinstance(tc_delta, dict):
                        continue
                    idx = tc_delta.get("index", 0)
                    slot = tool_calls_by_index.setdefault(
                        idx,
                        {"id": "", "type": "function", "function": {"name": "", "arguments": ""}},
                    )
                    if tc_delta.get("id"):
                        slot["id"] = tc_delta["id"]
                    if tc_delta.get("type"):
                        slot["type"] = tc_delta["type"]
                    fn = tc_delta.get("function", {}) or {}
                    if fn.get("name"):
                        slot["function"]["name"] += fn["name"]
                    if fn.get("arguments"):
                        slot["function"]["arguments"] += fn["arguments"]
        except TimeoutError:
            raise
        except OSError as e:
            raise APIRequestError(f"Stream read error: {e}") from e
        finally:
            try:
                response.close()
            except OSError:
                pass

        # If the server ignored stream=True and returned plain JSON, saw_sse is
        # False and we reconstruct the body from the buffered raw lines.
        if not saw_sse and raw_buffer:
            body = "".join(raw_buffer)
            try:
                buffered = json.loads(body)
                if isinstance(buffered, dict) and buffered.get("choices"):
                    return buffered
            except json.JSONDecodeError:
                pass

        message: dict[str, Any] = {"role": "assistant", "content": "".join(content_parts)}
        if tool_calls_by_index:
            message["tool_calls"] = [tool_calls_by_index[i] for i in sorted(tool_calls_by_index)]

        result: dict[str, Any] = {"choices": [{"message": message}]}
        if usage:
            result["usage"] = usage
        return result

    def _handle_http_error(self, error: urllib.error.HTTPError) -> None:
        """Handle HTTP error responses."""
        code = error.code
        try:
            body = error.read().decode("utf-8")
            error_data = json.loads(body)
            err_obj = error_data.get("error", {})
            if isinstance(err_obj, dict):
                message = err_obj.get("message", str(body))
                err_code = err_obj.get("code", "")
                err_type = err_obj.get("type", "")
                if err_code:
                    message = f"{message} (code: {err_code})"
                if err_type:
                    message = f"{message} (type: {err_type})"
            else:
                message = str(err_obj) if err_obj else str(body)
        except (json.JSONDecodeError, OSError):
            message = str(error.reason) if hasattr(error, "reason") else f"HTTP {code}"

        if code == 401:
            raise AuthenticationError(message, code=code)
        elif code == 429:
            raise RateLimitError(message, code=code)
        else:
            raise APIResponseError(message, code=code)


class OpenRouterClient(AIClient):
    """HTTP client for OpenRouter API (backward compatibility)."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout: int = 120,
    ) -> None:
        super().__init__(base_url, api_key, timeout, provider="openrouter")
