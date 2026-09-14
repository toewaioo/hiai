"""Base search provider interface."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SearchResult:
    """A single search result."""

    title: str
    url: str
    snippet: str


@dataclass
class SearchResponse:
    """Normalized search response."""

    status: str
    query: str
    results: list[SearchResult] = field(default_factory=list)
    message: str = ""

    def to_json(self) -> dict[str, Any]:
        d: dict[str, Any] = {"status": self.status, "query": self.query}
        if self.results:
            d["results"] = [
                {"title": r.title, "url": r.url, "snippet": r.snippet}
                for r in self.results
            ]
        if self.message:
            d["message"] = self.message
        return d


class SearchProvider:
    """Base class for search providers."""

    def search(self, query: str, max_results: int = 5) -> SearchResponse:
        """Perform a web search.

        Returns a SearchResponse with normalized results.
        """
        raise NotImplementedError
