"""Tests for filesystem tools."""

import tempfile
import unittest
from pathlib import Path

from hiai.exceptions import PathSecurityError
from hiai.tools.filesystem import FileSystemTools


class TestReadFile(unittest.TestCase):
    """Test file reading."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.fs = FileSystemTools(self.tmpdir)

    def test_read_existing_file(self):
        (self.tmpdir / "test.py").write_text("print('hello')")
        result = self.fs.read_file("test.py")
        self.assertEqual(result.status, "success")
        self.assertEqual(result.content, "print('hello')")

    def test_read_missing_file(self):
        result = self.fs.read_file("missing.py")
        self.assertEqual(result.status, "error")
        self.assertIn("not found", result.message.lower())

    def test_read_directory(self):
        (self.tmpdir / "subdir").mkdir()
        result = self.fs.read_file("subdir")
        self.assertEqual(result.status, "error")
        self.assertIn("directory", result.message.lower())

    def test_read_rejects_escape(self):
        with self.assertRaises(PathSecurityError):
            self.fs.read_file("../../etc/passwd")


class TestWriteFile(unittest.TestCase):
    """Test file writing."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.fs = FileSystemTools(self.tmpdir)

    def test_write_new_file(self):
        result = self.fs.write_file("new.py", "content")
        self.assertEqual(result.status, "written")
        self.assertEqual(result.operation, "created")
        self.assertTrue((self.tmpdir / "new.py").exists())

    def test_write_overwrite_existing(self):
        (self.tmpdir / "existing.py").write_text("old")
        result = self.fs.write_file("existing.py", "new content")
        self.assertEqual(result.status, "written")
        self.assertEqual(result.operation, "updated")
        self.assertEqual((self.tmpdir / "existing.py").read_text(), "new content")

    def test_write_creates_parent_dirs(self):
        result = self.fs.write_file("a/b/c/file.py", "content")
        self.assertEqual(result.status, "written")
        self.assertTrue((self.tmpdir / "a" / "b" / "c" / "file.py").exists())

    def test_write_rejects_escape(self):
        with self.assertRaises(PathSecurityError):
            self.fs.write_file("../../evil.py", "bad")


class TestListFiles(unittest.TestCase):
    """Test directory listing."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.fs = FileSystemTools(self.tmpdir)

    def test_list_empty_directory(self):
        result = self.fs.list_files(".")
        self.assertEqual(result.status, "success")
        self.assertEqual(result.files, [])

    def test_list_files(self):
        (self.tmpdir / "a.py").write_text("")
        (self.tmpdir / "b.py").write_text("")
        result = self.fs.list_files(".")
        self.assertIn("a.py", result.files)
        self.assertIn("b.py", result.files)

    def test_list_with_subdirectory(self):
        (self.tmpdir / "src").mkdir()
        (self.tmpdir / "src" / "app.py").write_text("")
        result = self.fs.list_files(".")
        self.assertIn("src/", result.files)
        self.assertIn("src/app.py", result.files)

    def test_list_nonexistent(self):
        result = self.fs.list_files("nonexistent")
        self.assertEqual(result.status, "error")


class TestSearchFiles(unittest.TestCase):
    """Test file searching."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.fs = FileSystemTools(self.tmpdir)

    def test_search_finds_match(self):
        (self.tmpdir / "main.py").write_text("from fastapi import FastAPI")
        result = self.fs.search_files("FastAPI")
        self.assertEqual(result.status, "success")
        self.assertTrue(len(result.matches) > 0)
        self.assertEqual(result.matches[0]["path"], "main.py")

    def test_search_case_insensitive(self):
        (self.tmpdir / "app.py").write_text("Hello World")
        result = self.fs.search_files("hello")
        self.assertTrue(len(result.matches) > 0)

    def test_search_no_match(self):
        (self.tmpdir / "app.py").write_text("Hello")
        result = self.fs.search_files("xyz")
        self.assertEqual(result.status, "success")
        self.assertEqual(len(result.matches), 0)

    def test_search_ignores_git_dir(self):
        (self.tmpdir / ".git").mkdir()
        (self.tmpdir / ".git" / "config").write_text("secret")
        (self.tmpdir / "app.py").write_text("normal")
        result = self.fs.search_files("secret")
        self.assertEqual(len(result.matches), 0)


if __name__ == "__main__":
    unittest.main()
