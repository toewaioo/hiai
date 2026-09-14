"""Search provider factory."""

from __future__ import annotations

import os

from hiai.search.base import SearchProvider, SearchResponse


def get_search_provider(
    provider_name: str = "tavily",
    api_key: str | None = None,
) -> SearchProvider | None:
    """Get a search provider instance.

    Returns None if the provider cannot be initialized.
    """
    if provider_name == "tavily":
        from hiai.search.tavily import TavilyProvider

        return TavilyProvider(api_key=api_key)
    else:
        return None


def web_search(
    query: str,
    provider_name: str = "tavily",
    api_key: str | None = None,
    max_results: int = 5,
) -> SearchResponse:
    """Perform a web search using the configured provider."""
    provider = get_search_provider(provider_name, api_key)

    if provider is None:
        return SearchResponse(
            status="error",
            query=query,
            message=f"Unknown search provider: {provider_name}",
        )

    return provider.search(query, max_results)
