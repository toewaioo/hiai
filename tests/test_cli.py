"""Tests for CLI commands."""

import os
import subprocess
import sys
import unittest

PYTHONPATH = os.path.join(os.path.dirname(__file__), "..", "src")
ENV = {**os.environ, "PYTHONPATH": PYTHONPATH}


class TestCLIHelp(unittest.TestCase):
    """Test CLI help output."""

    def test_help_flag(self):
        result = subprocess.run(
            [sys.executable, "-m", "hiai", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
            env=ENV,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("HIAI", result.stdout)
        self.assertIn("--project", result.stdout)

    def test_version_flag(self):
        result = subprocess.run(
            [sys.executable, "-m", "hiai", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            env=ENV,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("HIAI", result.stdout)


class TestCLIConfigShow(unittest.TestCase):
    """Test config show command."""

    def test_config_show(self):
        result = subprocess.run(
            [sys.executable, "-m", "hiai", "config", "show"],
            capture_output=True,
            text=True,
            timeout=10,
            env=ENV,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("model", result.stdout.lower())


class TestCLIMissingKey(unittest.TestCase):
    """Test behavior with missing API key."""

    def test_one_shot_without_key_exits(self):
        result = subprocess.run(
            [sys.executable, "-m", "hiai", "hello"],
            capture_output=True,
            text=True,
            timeout=10,
            env={**ENV, "PATH": "/usr/bin:/bin", "HOME": "/tmp"},
        )
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
