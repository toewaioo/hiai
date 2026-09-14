"""Tests for the HTTP client."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from hiai.client import OpenRouterClient
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


if __name__ == "__main__":
    unittest.main()
