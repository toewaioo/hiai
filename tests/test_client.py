"""Tests for the HTTP client."""

import io
import json
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from hiai.client import AIClient, OpenRouterClient, RateLimiter
from hiai.exceptions import (
    APIRequestError,
    APIResponseError,
    AuthenticationError,
    RateLimitError,
)


class TestClientURLBuilding(unittest.TestCase):
    """Test URL construction."""

    def test_base_url_with_api_v1(self):
        client = OpenRouterClient("https://openrouter.ai/api/v1", "key")
        url = client._build_url("/chat/completions")
        self.assertEqual(url, "https://openrouter.ai/api/v1/chat/completions")

    def test_base_url_without_api_v1(self):
        client = OpenRouterClient("https://custom.api.com", "key")
        url = client._build_url("/chat/completions")
        self.assertEqual(url, "https://custom.api.com/chat/completions")

    def test_no_double_v1(self):
        client = OpenRouterClient("https://openrouter.ai/api/v1", "key")
        url = client._build_url("/v1/chat/completions")
        self.assertNotIn("/v1/v1/", url)


class TestClientHeaders(unittest.TestCase):
    """Test request headers."""

    @patch("urllib.request.urlopen")
    def test_auth_header(self, mock_open):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "choices": [{"message": {"content": "ok"}}]
        }).encode()
        mock_open.return_value = mock_response

        client = OpenRouterClient("https://test.com/api/v1", "secret-key")
        client.chat_completion([{"role": "user", "content": "hi"}], "model")

        call_args = mock_open.call_args
        request = call_args[0][0]
        self.assertEqual(request.get_header("Authorization"), "Bearer secret-key")
        self.assertEqual(request.get_header("Content-type"), "application/json")


class TestGroqClient(unittest.TestCase):
    """Test AIClient with Groq provider."""

    def test_groq_url_building(self):
        client = AIClient(
            base_url="https://api.groq.com/openai/v1",
            api_key="gsk-test",
            provider="groq",
        )
        url = client._build_url("/chat/completions")
        self.assertEqual(url, "https://api.groq.com/openai/v1/chat/completions")

    def test_groq_headers_no_referer(self):
        client = AIClient(
            base_url="https://api.groq.com/openai/v1",
            api_key="gsk-test",
            provider="groq",
        )
        headers = client._get_headers()
        self.assertIn("Authorization", headers)
        self.assertNotIn("HTTP-Referer", headers)
        self.assertNotIn("X-Title", headers)

    def test_openrouter_headers_include_referer(self):
        client = AIClient(
            base_url="https://openrouter.ai/api/v1",
            api_key="sk-or-test",
            provider="openrouter",
        )
        headers = client._get_headers()
        self.assertIn("Authorization", headers)
        self.assertEqual(headers["HTTP-Referer"], "https://github.com/toewaioo/hiai")
        self.assertEqual(headers["X-Title"], "HIAI")

    def test_groq_url_no_double_v1(self):
        client = AIClient(
            base_url="https://api.groq.com/openai/v1",
            api_key="gsk-test",
            provider="groq",
        )
        url = client._build_url("/chat/completions")
        self.assertEqual(url, "https://api.groq.com/openai/v1/chat/completions")
        self.assertNotIn("/v1/v1/", url)

    @patch("urllib.request.urlopen")
    def test_groq_auth_header(self, mock_open):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "choices": [{"message": {"content": "ok"}}]
        }).encode()
        mock_open.return_value = mock_response

        client = AIClient(
            base_url="https://api.groq.com/openai/v1",
            api_key="gsk-test-key",
            provider="groq",
        )
        client.chat_completion([{"role": "user", "content": "hi"}], "llama-3.3-70b-versatile")

        call_args = mock_open.call_args
        request = call_args[0][0]
        self.assertEqual(request.get_header("Authorization"), "Bearer gsk-test-key")


class TestRateLimiter(unittest.TestCase):
    """Test RateLimiter class."""

    def test_allows_requests_under_limit(self):
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        for _ in range(5):
            limiter.wait()
        self.assertEqual(limiter.remaining, 0)

    def test_remaining_decreases(self):
        limiter = RateLimiter(max_requests=10, window_seconds=60)
        self.assertEqual(limiter.remaining, 10)
        limiter.record()
        self.assertEqual(limiter.remaining, 9)
        limiter.record()
        self.assertEqual(limiter.remaining, 8)

    def test_record_does_not_block(self):
        limiter = RateLimiter(max_requests=1, window_seconds=60)
        limiter.record()
        # record() should not block even at limit
        start = time.monotonic()
        limiter.record()
        elapsed = time.monotonic() - start
        self.assertLess(elapsed, 0.1)

    def test_window_expiration(self):
        limiter = RateLimiter(max_requests=2, window_seconds=0.1)
        limiter.record()
        limiter.record()
        self.assertEqual(limiter.remaining, 0)
        time.sleep(0.15)
        self.assertEqual(limiter.remaining, 2)

    def test_custom_window(self):
        limiter = RateLimiter(max_requests=3, window_seconds=10)
        self.assertEqual(limiter.max_requests, 3)
        self.assertEqual(limiter.window_seconds, 10)


class TestRateLimitIntegration(unittest.TestCase):
    """Test rate limiter integration with AIClient."""

    def test_client_has_rate_limiter(self):
        client = AIClient(
            base_url="https://test.com/api/v1",
            api_key="key",
            rate_limit=10,
        )
        self.assertEqual(client.rate_limiter.max_requests, 10)

    def test_client_default_rate_limit(self):
        client = AIClient(
            base_url="https://test.com/api/v1",
            api_key="key",
        )
        self.assertEqual(client.rate_limiter.max_requests, 20)

    @patch("urllib.request.urlopen")
    def test_rate_limiter_blocks_after_limit(self, mock_open):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "choices": [{"message": {"content": "ok"}}]
        }).encode()
        mock_open.return_value = mock_response

        client = AIClient(
            base_url="https://test.com/api/v1",
            api_key="key",
            rate_limit=2,
        )
        # Use a short window so the test doesn't hang
        client.rate_limiter = RateLimiter(max_requests=2, window_seconds=0.1)
        # First two calls should work
        client.chat_completion([{"role": "user", "content": "hi"}], "model")
        client.chat_completion([{"role": "user", "content": "hi"}], "model")
        # Third call should also work (rate limiter waits, window expires quickly)
        client.chat_completion([{"role": "user", "content": "hi"}], "model")
        self.assertEqual(mock_open.call_count, 3)

    def test_parse_retry_after_seconds(self):
        client = AIClient(
            base_url="https://test.com/api/v1",
            api_key="key",
        )
        error = RateLimitError("Rate limited. Retry-After: 5")
        result = client._parse_retry_after(error)
        self.assertEqual(result, 5.0)

    def test_parse_retry_after_try_again(self):
        client = AIClient(
            base_url="https://test.com/api/v1",
            api_key="key",
        )
        error = RateLimitError("Too many requests, try again in 10 seconds")
        result = client._parse_retry_after(error)
        self.assertEqual(result, 10.0)

    def test_parse_retry_after_none(self):
        client = AIClient(
            base_url="https://test.com/api/v1",
            api_key="key",
        )
        error = RateLimitError("Rate limited")
        result = client._parse_retry_after(error)
        self.assertIsNone(result)


class TestStreamingChatCompletion(unittest.TestCase):
    """Test SSE streaming support in chat_completion."""

    @staticmethod
    def _sse_stream(chunks: list[dict], done: bool = True) -> io.BytesIO:
        """Build a fake SSE response body from chunk dicts."""
        lines = []
        for c in chunks:
            lines.append(b"data: " + json.dumps(c).encode("utf-8") + b"\n")
        if done:
            lines.append(b"data: [DONE]\n")
        return io.BytesIO(b"".join(lines))

    @patch("urllib.request.urlopen")
    def test_stream_assembles_content(self, mock_open):
        chunks = [
            {"choices": [{"delta": {"content": "Hello"}}]},
            {"choices": [{"delta": {"content": ", world"}}]},
            {"choices": [{"delta": {}}], "usage": {"prompt_tokens": 5, "completion_tokens": 2, "total_tokens": 7}},
        ]
        mock_open.return_value = self._sse_stream(chunks)

        client = AIClient(base_url="https://test.com/api/v1", api_key="key")
        received: list[str] = []
        result = client.chat_completion(
            messages=[{"role": "user", "content": "hi"}],
            model="m",
            stream=True,
            on_delta=received.append,
        )

        self.assertEqual(received, ["Hello", ", world"])
        msg = result["choices"][0]["message"]
        self.assertEqual(msg["content"], "Hello, world")
        self.assertNotIn("tool_calls", msg)
        self.assertEqual(result["usage"]["total_tokens"], 7)

    @patch("urllib.request.urlopen")
    def test_stream_assembles_tool_calls(self, mock_open):
        chunks = [
            {"choices": [{"delta": {"tool_calls": [{"index": 0, "id": "call_1", "type": "function", "function": {"name": "read_file", "arguments": ""}}]}}]},
            {"choices": [{"delta": {"tool_calls": [{"index": 0, "function": {"arguments": '{"path": "a.py"}'}}]}}]},
            {"choices": [{"delta": {"content": "done"}}]},
        ]
        mock_open.return_value = self._sse_stream(chunks)

        client = AIClient(base_url="https://test.com/api/v1", api_key="key")
        result = client.chat_completion(
            messages=[{"role": "user", "content": "hi"}],
            model="m",
            stream=True,
        )

        msg = result["choices"][0]["message"]
        self.assertEqual(msg["content"], "done")
        self.assertIn("tool_calls", msg)
        self.assertEqual(msg["tool_calls"][0]["id"], "call_1")
        self.assertEqual(msg["tool_calls"][0]["function"]["name"], "read_file")
        self.assertEqual(msg["tool_calls"][0]["function"]["arguments"], '{"path": "a.py"}')

    @patch("urllib.request.urlopen")
    def test_stream_falls_back_when_not_sse(self, mock_open):
        # Server ignored stream=true and returned a plain JSON body
        buffered = {"choices": [{"message": {"role": "assistant", "content": "buffered"}}]}
        mock_open.return_value = io.BytesIO(json.dumps(buffered).encode("utf-8"))

        client = AIClient(base_url="https://test.com/api/v1", api_key="key")
        result = client.chat_completion(
            messages=[{"role": "user", "content": "hi"}],
            model="m",
            stream=True,
        )
        self.assertEqual(result["choices"][0]["message"]["content"], "buffered")


if __name__ == "__main__":
    unittest.main()
