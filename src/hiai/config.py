"""Configuration management for HIAI."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from hiai.constants import (
    DEFAULT_BASE_URL,
    DEFAULT_MAX_ITERATIONS,
    DEFAULT_MAX_READ_BYTES,
    DEFAULT_MAX_WRITE_BYTES,
    DEFAULT_MODEL,
    DEFAULT_TIMEOUT,
)
from hiai.exceptions import APIKeyError, ConfigError
from hiai.models import AppConfig
from hiai.utils.paths import get_platform_config_dir


def get_config_path() -> Path:
    """Get the platform-appropriate config file path."""
    return get_platform_config_dir() / "config.json"


def load_config() -> AppConfig:
    """Load configuration from file and environment."""
    config = AppConfig()
    config_path = get_config_path()

    if config_path.exists():
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                config.model = data.get("model", config.model)
                config.base_url = data.get("base_url", config.base_url)
                config.api_key = data.get("api_key", config.api_key)
                config.timeout = data.get("timeout", config.timeout)
                config.max_iterations = data.get("max_iterations", config.max_iterations)
                config.max_read_bytes = data.get("max_read_bytes", config.max_read_bytes)
                config.max_write_bytes = data.get("max_write_bytes", config.max_write_bytes)
                config.theme = data.get("theme", config.theme)
                config.search_provider = data.get("search_provider", config.search_provider)
                config.search_api_key = data.get("search_api_key", config.search_api_key)
                config.search_max_results = data.get("search_max_results", config.search_max_results)
        except (json.JSONDecodeError, OSError):
            pass

    env_key = os.environ.get("OPENROUTER_API_KEY", "")
    if env_key:
        config.api_key = env_key

    env_model = os.environ.get("HIAI_MODEL", "")
    if env_model:
        config.model = env_model

    env_base_url = os.environ.get("HIAI_BASE_URL", "")
    if env_base_url:
        config.base_url = env_base_url

    env_search_key = os.environ.get("TAVILY_API_KEY", "")
    if env_search_key:
        config.search_api_key = env_search_key

    env_search_provider = os.environ.get("HIAI_SEARCH_PROVIDER", "")
    if env_search_provider:
        config.search_provider = env_search_provider

    return config


def save_config(config: AppConfig) -> None:
    """Save configuration to disk."""
    config_path = get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "model": config.model,
        "base_url": config.base_url,
        "api_key": config.api_key,
        "timeout": config.timeout,
        "max_iterations": config.max_iterations,
        "max_read_bytes": config.max_read_bytes,
        "max_write_bytes": config.max_write_bytes,
        "theme": config.theme,
        "search_provider": config.search_provider,
        "search_api_key": config.search_api_key,
        "search_max_results": config.search_max_results,
    }

    config_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    if sys.platform != "win32":
        try:
            config_path.chmod(0o600)
        except OSError:
            pass


def reset_config() -> None:
    """Reset configuration to defaults."""
    config = AppConfig()
    save_config(config)


def set_api_key(key: str) -> None:
    """Set the API key in config."""
    if not key or not key.strip():
        raise ConfigError("API key cannot be empty.")
    config = load_config()
    config.api_key = key.strip()
    save_config(config)


def set_model(model: str) -> None:
    """Set the model in config."""
    if not model or not model.strip():
        raise ConfigError("Model cannot be empty.")
    config = load_config()
    config.model = model.strip()
    save_config(config)


def set_base_url(url: str) -> None:
    """Set the base URL in config."""
    if not url or not url.strip():
        raise ConfigError("Base URL cannot be empty.")
    config = load_config()
    config.base_url = url.strip().rstrip("/")
    save_config(config)


def show_config() -> dict[str, str]:
    """Return config display dict (hides API key)."""
    config = load_config()
    key_display = "configured" if config.api_key else "not configured"
    return {
        "model": config.model,
        "base_url": config.base_url,
        "api_key": key_display,
        "timeout": str(config.timeout),
        "max_iterations": str(config.max_iterations),
        "max_read_bytes": str(config.max_read_bytes),
        "max_write_bytes": str(config.max_write_bytes),
        "theme": config.theme,
        "search_provider": config.search_provider,
        "search_api_key": "configured" if config.search_api_key else "not configured",
        "search_max_results": str(config.search_max_results),
    }


def require_api_key(config: AppConfig) -> str:
    """Return the API key or raise APIKeyError."""
    if not config.api_key:
        raise APIKeyError(
            "API key not configured. Run: hiai config set-key\n"
            "Or set the OPENROUTER_API_KEY environment variable."
        )
    return config.api_key


def set_search_provider(provider: str) -> None:
    """Set the search provider in config."""
    if not provider or not provider.strip():
        raise ConfigError("Search provider cannot be empty.")
    config = load_config()
    config.search_provider = provider.strip()
    save_config(config)


def set_search_key(key: str) -> None:
    """Set the search API key in config."""
    if not key or not key.strip():
        raise ConfigError("Search API key cannot be empty.")
    config = load_config()
    config.search_api_key = key.strip()
    save_config(config)


def set_search_max_results(max_results: int) -> None:
    """Set the max search results in config."""
    config = load_config()
    config.search_max_results = max(1, min(10, max_results))
    save_config(config)
