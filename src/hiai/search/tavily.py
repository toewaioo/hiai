"""Tavily search provider implementation."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from hiai.search.base import SearchProvider, SearchResponse, SearchResult

TAVILY_API_URL = "https://api.tavily.com/search"
DEFAULT_MAX_RESULTS = 5
DEFAULT_TIMEOUT = 30


class TavilyProvider(SearchProvider):
    """Web search using Tavily Search API."""

    def __init__(self, api_key: str | None = None, timeout: int = DEFAULT_TIMEOUT) -> None:
        self.api_key = api_key or os.environ.get("TAVILY_API_KEY", "")
        self.timeout = timeout

    def search(self, query: str, max_results: int = DEFAULT_MAX_RESULTS) -> SearchResponse:
        """Search using Tavily API."""
        if not self.api_key:
            return SearchResponse(
                status="error",
                query=query,
                message="Web search is not configured. Set TAVILY_API_KEY or configure another supported provider.",
            )

        payload = {
            "api_key": self.api_key,
            "query": query,
            "max_results": max_results,
        }

        body = json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"}

        request = urllib.request.Request(
            TAVILY_API_URL, data=body, headers=headers, method="POST"
        )

        try:
            response = urllib.request.urlopen(request, timeout=self.timeout)
            data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            code = e.code
            try:
                err_body = e.read().decode("utf-8")
                err_data = json.loads(err_body)
                msg = err_data.get("detail", err_data.get("error", f"HTTP {code}"))
            except (json.JSONDecodeError, OSError):
                msg = f"HTTP {code}"

            if code == 401:
                return SearchResponse(
                    status="error",
                    query=query,
                    message="Invalid Tavily API key.",
                )
            elif code == 429:
                return SearchResponse(
                    status="error",
                    query=query,
                    message="Tavily rate limit exceeded. Try again later.",
                )
            return SearchResponse(
                status="error",
                query=query,
                message=f"Tavily API error: {msg}",
            )
        except urllib.error.URLError as e:
            return SearchResponse(
                status="error",
                query=query,
                message=f"Network error: {e.reason}",
            )
        except json.JSONDecodeError as e:
            return SearchResponse(
                status="error",
                query=query,
                message=f"Invalid response from Tavily: {e}",
            )
        except OSError as e:
            return SearchResponse(
                status="error",
                query=query,
                message=f"Request failed: {e}",
            )

        # Parse results
        results = []
        for item in data.get("results", [])[:max_results]:
            title = item.get("title", "")
            url = item.get("url", "")
            snippet = item.get("content", item.get("snippet", ""))
            if title and url:
                results.append(SearchResult(title=title, url=url, snippet=snippet))

        return SearchResponse(
            status="success",
            query=query,
            results=results,
        )
