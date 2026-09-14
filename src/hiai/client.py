"""OpenRouter HTTP client using only stdlib."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any

from hiai.constants import USER_AGENT
from hiai.exceptions import (
    APIRequestError,
    APIResponseError,
    AuthenticationError,
    RateLimitError,
    TimeoutError,
)


class OpenRouterClient:
    """HTTP client for OpenRouter API."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout: int = 120,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

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

    def chat_completion(
        self,
        messages: list[dict[str, Any]],
        model: str,
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.7,
        max_retries: int = 3,
    ) -> dict[str, Any]:
        """Send a chat completion request.

        Returns the parsed JSON response.
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

        body = json.dumps(payload).encode("utf-8")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": USER_AGENT,
            "HTTP-Referer": "https://github.com/hiai-ai/hiai",
            "X-Title": "HIAI",
        }

        request = urllib.request.Request(
            url, data=body, headers=headers, method="POST"
        )

        last_error: Exception | None = None
        for attempt in range(max_retries):
            try:
                return self._do_request(request)
            except RateLimitError:
                if attempt < max_retries - 1:
                    wait = 2 ** attempt
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

    def _handle_http_error(self, error: urllib.error.HTTPError) -> None:
        """Handle HTTP error responses."""
        code = error.code
        try:
            body = error.read().decode("utf-8")
            error_data = json.loads(body)
            message = error_data.get("error", {}).get("message", str(body))
        except (json.JSONDecodeError, OSError):
            message = str(error.reason) if hasattr(error, "reason") else f"HTTP {code}"

        if code == 401:
            raise AuthenticationError(message, code=code)
        elif code == 429:
            raise RateLimitError(message, code=code)
        else:
            raise APIResponseError(message, code=code)
