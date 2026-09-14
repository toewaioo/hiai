"""Tests for path security."""

import tempfile
import unittest
from pathlib import Path

from hiai.utils.paths import get_platform_config_dir, is_sensitive_file, resolve_safe_path


class TestResolveSafePath(unittest.TestCase):
    """Test safe path resolution."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.project = self.tmpdir / "project"
        self.project.mkdir()

    def test_valid_relative_path(self):
        result = resolve_safe_path(self.project, "src/main.py")
        self.assertEqual(result, self.project / "src" / "main.py")

    def test_nested_path(self):
        result = resolve_safe_path(self.project, "a/b/c/file.txt")
        self.assertEqual(result, self.project / "a" / "b" / "c" / "file.txt")

    def test_reject_dotdot(self):
        with self.assertRaises(ValueError):
            resolve_safe_path(self.project, "../etc/passwd")

    def test_reject_absolute_escape(self):
        with self.assertRaises(ValueError):
            resolve_safe_path(self.project, "/etc/passwd")

    def test_reject_complex_escape(self):
        with self.assertRaises(ValueError):
            resolve_safe_path(self.project, "src/../../etc/passwd")

    def test_empty_path_returns_root(self):
        result = resolve_safe_path(self.project, "")
        self.assertEqual(result, self.project)

    def test_current_dir_path(self):
        result = resolve_safe_path(self.project, ".")
        self.assertEqual(result.resolve(), self.project.resolve())


class TestPlatformConfigDir(unittest.TestCase):
    """Test platform config directory detection."""

    def test_returns_pathlib(self):
        result = get_platform_config_dir()
        self.assertIsInstance(result, Path)

    def test_ends_with_hiai(self):
        result = get_platform_config_dir()
        self.assertEqual(result.name, "hiai")


class TestSensitiveFileDetection(unittest.TestCase):
    """Test sensitive file pattern matching."""

    def test_env_file(self):
        self.assertTrue(is_sensitive_file(Path(".env")))

    def test_pem_file(self):
        self.assertTrue(is_sensitive_file(Path("cert.pem")))

    def test_key_file(self):
        self.assertTrue(is_sensitive_file(Path("private.key")))

    def test_id_rsa(self):
        self.assertTrue(is_sensitive_file(Path("id_rsa")))

    def test_credentials_json(self):
        self.assertTrue(is_sensitive_file(Path("credentials.json")))

    def test_regular_file_not_sensitive(self):
        self.assertFalse(is_sensitive_file(Path("main.py")))

    def test_readme_not_sensitive(self):
        self.assertFalse(is_sensitive_file(Path("README.md")))


if __name__ == "__main__":
    unittest.main()
