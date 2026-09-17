"""Tests for configuration management."""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from hiai.config import (
    get_config_path,
    load_config,
    require_api_key,
    reset_config,
    save_config,
    set_api_key,
    set_base_url,
    set_model,
    set_provider,
    set_rate_limit,
    show_config,
)
from hiai.exceptions import APIKeyError, ConfigError
from hiai.models import AppConfig


class TestConfigDefaults(unittest.TestCase):
    """Test default configuration values."""

    def test_default_config(self):
        config = AppConfig()
        self.assertEqual(config.model, "openrouter/free")
        self.assertEqual(config.base_url, "https://openrouter.ai/api/v1")
        self.assertEqual(config.api_key, "")
        self.assertEqual(config.timeout, 120)
        self.assertEqual(config.max_iterations, 20)

    def test_config_path_is_pathlib(self):
        path = get_config_path()
        self.assertIsInstance(path, Path)


class TestConfigSaveLoad(unittest.TestCase):
    """Test saving and loading configuration."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.config_path = Path(self.tmpdir) / "config.json"

    @patch("hiai.config.get_config_path")
    def test_save_and_load(self, mock_path):
        mock_path.return_value = self.config_path
        config = AppConfig(model="test-model", api_key="test-key-123")
        save_config(config)

        loaded = load_config()
        self.assertEqual(loaded.model, "test-model")
        self.assertEqual(loaded.api_key, "test-key-123")

    @patch("hiai.config.get_config_path")
    def test_reset_config(self, mock_path):
        mock_path.return_value = self.config_path
        config = AppConfig(model="custom", api_key="secret")
        save_config(config)

        reset_config()
        loaded = load_config()
        self.assertEqual(loaded.model, "openrouter/free")
        self.assertEqual(loaded.api_key, "")

    @patch("hiai.config.get_config_path")
    def test_show_config_hides_api_key(self, mock_path):
        mock_path.return_value = self.config_path
        config = AppConfig(api_key="super-secret-key")
        save_config(config)

        displayed = show_config()
        self.assertEqual(displayed["api_key"], "configured")

    @patch("hiai.config.get_config_path")
    def test_show_config_shows_not_configured(self, mock_path):
        mock_path.return_value = self.config_path
        reset_config()

        displayed = show_config()
        self.assertEqual(displayed["api_key"], "not configured")


class TestConfigCommands(unittest.TestCase):
    """Test config command functions."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.config_path = Path(self.tmpdir) / "config.json"

    @patch("hiai.config.get_config_path")
    def test_set_model(self, mock_path):
        mock_path.return_value = self.config_path
        set_model("new-model")
        loaded = load_config()
        self.assertEqual(loaded.model, "new-model")

    @patch("hiai.config.get_config_path")
    def test_set_model_empty_raises(self, mock_path):
        mock_path.return_value = self.config_path
        with self.assertRaises(ConfigError):
            set_model("")

    @patch("hiai.config.get_config_path")
    def test_set_base_url(self, mock_path):
        mock_path.return_value = self.config_path
        set_base_url("https://custom.api/v1")
        loaded = load_config()
        self.assertEqual(loaded.base_url, "https://custom.api/v1")

    @patch("hiai.config.get_config_path")
    def test_set_base_url_strips_trailing_slash(self, mock_path):
        mock_path.return_value = self.config_path
        set_base_url("https://custom.api/v1/")
        loaded = load_config()
        self.assertEqual(loaded.base_url, "https://custom.api/v1")

    @patch("hiai.config.get_config_path")
    def test_set_api_key(self, mock_path):
        mock_path.return_value = self.config_path
        set_api_key("my-api-key")
        loaded = load_config()
        self.assertEqual(loaded.api_key, "my-api-key")


class TestAPIKeyRequirement(unittest.TestCase):
    """Test API key requirement."""

    def test_require_api_key_when_set(self):
        config = AppConfig(api_key="test-key")
        result = require_api_key(config)
        self.assertEqual(result, "test-key")

    def test_require_api_key_when_missing(self):
        config = AppConfig(api_key="")
        with self.assertRaises(APIKeyError):
            require_api_key(config)


class TestEnvironmentOverrides(unittest.TestCase):
    """Test environment variable overrides."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    @patch("hiai.config.get_config_path")
    def test_env_key_overrides(self, mock_path):
        mock_path.return_value = Path(self.tmpdir) / "nonexistent.json"
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "env-key"}):
            config = load_config()
            self.assertEqual(config.api_key, "env-key")

    @patch("hiai.config.get_config_path")
    def test_env_model_overrides(self, mock_path):
        mock_path.return_value = Path(self.tmpdir) / "nonexistent.json"
        with patch.dict(os.environ, {"HIAI_MODEL": "env-model"}):
            config = load_config()
            self.assertEqual(config.model, "env-model")


class TestProviderSwitching(unittest.TestCase):
    """Test provider switching between OpenRouter and Groq."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.config_path = Path(self.tmpdir) / "config.json"

    @patch("hiai.config.get_config_path")
    def test_set_provider_groq(self, mock_path):
        mock_path.return_value = self.config_path
        set_provider("groq")
        loaded = load_config()
        self.assertEqual(loaded.provider, "groq")
        self.assertEqual(loaded.base_url, "https://api.groq.com/openai/v1")
        self.assertEqual(loaded.model, "llama-3.3-70b-versatile")

    @patch("hiai.config.get_config_path")
    def test_set_provider_openrouter(self, mock_path):
        mock_path.return_value = self.config_path
        set_provider("groq")
        set_provider("openrouter")
        loaded = load_config()
        self.assertEqual(loaded.provider, "openrouter")
        self.assertEqual(loaded.base_url, "https://openrouter.ai/api/v1")
        self.assertEqual(loaded.model, "openrouter/free")

    @patch("hiai.config.get_config_path")
    def test_set_provider_invalid_raises(self, mock_path):
        mock_path.return_value = self.config_path
        with self.assertRaises(ConfigError):
            set_provider("invalid")

    @patch("hiai.config.get_config_path")
    def test_set_provider_empty_raises(self, mock_path):
        mock_path.return_value = self.config_path
        with self.assertRaises(ConfigError):
            set_provider("")

    @patch("hiai.config.get_config_path")
    def test_set_provider_strips_whitespace(self, mock_path):
        mock_path.return_value = self.config_path
        set_provider("  groq  ")
        loaded = load_config()
        self.assertEqual(loaded.provider, "groq")


class TestGroqEnvironmentOverrides(unittest.TestCase):
    """Test Groq-specific environment variable overrides."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    @patch("hiai.config.get_config_path")
    def test_groq_api_key_overrides_when_provider_groq(self, mock_path):
        mock_path.return_value = Path(self.tmpdir) / "nonexistent.json"
        with patch.dict(os.environ, {
            "OPENROUTER_API_KEY": "or-key",
            "GROQ_API_KEY": "gsk-test",
            "HIAI_PROVIDER": "groq",
        }):
            config = load_config()
            self.assertEqual(config.provider, "groq")
            self.assertEqual(config.api_key, "gsk-test")

    @patch("hiai.config.get_config_path")
    def test_groq_api_key_ignored_when_provider_openrouter(self, mock_path):
        mock_path.return_value = Path(self.tmpdir) / "nonexistent.json"
        with patch.dict(os.environ, {
            "OPENROUTER_API_KEY": "or-key",
            "GROQ_API_KEY": "gsk-test",
        }):
            config = load_config()
            self.assertEqual(config.provider, "openrouter")
            self.assertEqual(config.api_key, "or-key")

    @patch("hiai.config.get_config_path")
    def test_hiai_provider_env_sets_provider(self, mock_path):
        mock_path.return_value = Path(self.tmpdir) / "nonexistent.json"
        with patch.dict(os.environ, {"HIAI_PROVIDER": "groq"}):
            config = load_config()
            self.assertEqual(config.provider, "groq")


class TestRequireAPIKeyGroq(unittest.TestCase):
    """Test API key requirement for Groq provider."""

    def test_require_api_key_groq_when_set(self):
        config = AppConfig(provider="groq", api_key="gsk-test")
        result = require_api_key(config)
        self.assertEqual(result, "gsk-test")

    def test_require_api_key_groq_when_missing(self):
        config = AppConfig(provider="groq", api_key="")
        with self.assertRaises(APIKeyError) as ctx:
            require_api_key(config)
        self.assertIn("GROQ_API_KEY", str(ctx.exception))

    def test_require_api_key_openrouter_when_missing(self):
        config = AppConfig(provider="openrouter", api_key="")
        with self.assertRaises(APIKeyError) as ctx:
            require_api_key(config)
        self.assertIn("OPENROUTER_API_KEY", str(ctx.exception))


class TestRateLimitConfig(unittest.TestCase):
    """Test rate limit configuration."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.config_path = Path(self.tmpdir) / "config.json"

    @patch("hiai.config.get_config_path")
    def test_default_rate_limit(self, mock_path):
        mock_path.return_value = self.config_path
        config = load_config()
        self.assertEqual(config.rate_limit, 20)

    @patch("hiai.config.get_config_path")
    def test_set_rate_limit(self, mock_path):
        mock_path.return_value = self.config_path
        set_rate_limit(10)
        config = load_config()
        self.assertEqual(config.rate_limit, 10)

    @patch("hiai.config.get_config_path")
    def test_set_rate_limit_min(self, mock_path):
        mock_path.return_value = self.config_path
        set_rate_limit(0)
        config = load_config()
        self.assertEqual(config.rate_limit, 1)

    @patch("hiai.config.get_config_path")
    def test_set_rate_limit_max(self, mock_path):
        mock_path.return_value = self.config_path
        set_rate_limit(200)
        config = load_config()
        self.assertEqual(config.rate_limit, 100)

    @patch("hiai.config.get_config_path")
    def test_rate_limit_persists(self, mock_path):
        mock_path.return_value = self.config_path
        set_rate_limit(15)
        loaded = load_config()
        self.assertEqual(loaded.rate_limit, 15)

    @patch("hiai.config.get_config_path")
    def test_show_config_includes_rate_limit(self, mock_path):
        mock_path.return_value = self.config_path
        set_rate_limit(25)
        displayed = show_config()
        self.assertEqual(displayed["rate_limit"], "25/min")


if __name__ == "__main__":
    unittest.main()
