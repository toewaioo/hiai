"""Tests for web search tool."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from hiai.search.base import SearchProvider, SearchResponse, SearchResult
from hiai.search.provider import get_search_provider, web_search


class TestSearchResponse(unittest.TestCase):
    """Test SearchResponse dataclass."""

    def test_to_json(self):
        resp = SearchResponse(
            status="success",
            query="test",
            results=[SearchResult(title="T", url="U", snippet="S")],
        )
        d = resp.to_json()
        self.assertEqual(d["status"], "success")
        self.assertEqual(d["query"], "test")
        self.assertEqual(len(d["results"]), 1)
        self.assertEqual(d["results"][0]["title"], "T")

    def test_error_response(self):
        resp = SearchResponse(status="error", query="q", message="No key")
        d = resp.to_json()
        self.assertEqual(d["status"], "error")
        self.assertEqual(d["message"], "No key")
        self.assertNotIn("results", d)


class TestSearchProvider(unittest.TestCase):
    """Test search provider factory."""

    def test_get_tavily_provider(self):
        provider = get_search_provider("tavily", "test-key")
        self.assertIsNotNone(provider)

    def test_unknown_provider(self):
        provider = get_search_provider("unknown")
        self.assertIsNone(provider)


class TestWebSearch(unittest.TestCase):
    """Test web_search function."""

    def test_missing_api_key(self):
        result = web_search("test query", "tavily", "")
        self.assertEqual(result.status, "error")
        self.assertIn("not configured", result.message.lower())

    def test_unknown_provider(self):
        result = web_search("test", "nonexistent")
        self.assertEqual(result.status, "error")
        self.assertIn("unknown", result.message.lower())

    @patch("hiai.search.tavily.urllib.request.urlopen")
    def test_successful_search(self, mock_open):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "results": [
                {"title": "FastAPI Docs", "url": "https://fastapi.tiangolo.com", "snippet": "FastAPI framework"}
            ]
        }).encode()
        mock_open.return_value = mock_response

        result = web_search("FastAPI documentation", "tavily", "test-key", max_results=5)
        self.assertEqual(result.status, "success")
        self.assertEqual(len(result.results), 1)
        self.assertEqual(result.results[0].title, "FastAPI Docs")

    @patch("hiai.search.tavily.urllib.request.urlopen")
    def test_http_error_401(self, mock_open):
        import urllib.error
        error = urllib.error.HTTPError(
            url="https://api.tavily.com/search",
            code=401,
            msg="Unauthorized",
            hdrs={},
            fp=MagicMock(read=MagicMock(return_value=json.dumps({"detail": "Invalid key"}).encode())),
        )
        mock_open.side_effect = error

        result = web_search("test", "tavily", "bad-key")
        self.assertEqual(result.status, "error")
        self.assertIn("invalid", result.message.lower())

    @patch("hiai.search.tavily.urllib.request.urlopen")
    def test_rate_limit_error(self, mock_open):
        import urllib.error
        error = urllib.error.HTTPError(
            url="https://api.tavily.com/search",
            code=429,
            msg="Too Many Requests",
            hdrs={},
            fp=MagicMock(read=MagicMock(return_value=b'{"detail": "rate limited"}')),
        )
        mock_open.side_effect = error

        result = web_search("test", "tavily", "test-key")
        self.assertEqual(result.status, "error")
        self.assertIn("rate limit", result.message.lower())

    @patch("hiai.search.tavily.urllib.request.urlopen")
    def test_network_error(self, mock_open):
        import urllib.error
        mock_open.side_effect = urllib.error.URLError("Connection refused")

        result = web_search("test", "tavily", "test-key")
        self.assertEqual(result.status, "error")
        self.assertIn("network", result.message.lower())

    @patch("hiai.search.tavily.urllib.request.urlopen")
    def test_empty_results(self, mock_open):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"results": []}).encode()
        mock_open.return_value = mock_response

        result = web_search("nonexistent", "tavily", "test-key")
        self.assertEqual(result.status, "success")
        self.assertEqual(len(result.results), 0)

    @patch("hiai.search.tavily.urllib.request.urlopen")
    def test_max_results_limit(self, mock_open):
        mock_response = MagicMock()
        results = [{"title": f"R{i}", "url": f"https://{i}.com", "snippet": f"S{i}"} for i in range(15)]
        mock_response.read.return_value = json.dumps({"results": results}).encode()
        mock_open.return_value = mock_response

        result = web_search("test", "tavily", "test-key", max_results=3)
        self.assertEqual(len(result.results), 3)

    @patch("hiai.search.tavily.urllib.request.urlopen")
    def test_api_key_not_exposed(self, mock_open):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"results": []}).encode()
        mock_open.return_value = mock_response

        result = web_search("test", "tavily", "secret-api-key-12345")
        # Check that the API key is not in the result
        result_str = json.dumps(result.to_json())
        self.assertNotIn("secret-api-key-12345", result_str)


class TestTavilyProvider(unittest.TestCase):
    """Test Tavily provider directly."""

    def test_init_with_key(self):
        from hiai.search.tavily import TavilyProvider
        provider = TavilyProvider(api_key="test-key")
        self.assertEqual(provider.api_key, "test-key")

    @patch.dict("os.environ", {"TAVILY_API_KEY": "env-key"})
    def test_init_with_env(self):
        from hiai.search.tavily import TavilyProvider
        provider = TavilyProvider()
        self.assertEqual(provider.api_key, "env-key")


if __name__ == "__main__":
    unittest.main()
