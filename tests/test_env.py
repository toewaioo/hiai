"""Tests for the stdlib .env loader."""

import os
import tempfile
import unittest
from pathlib import Path

from hiai.utils.env import load_default_env, load_dotenv


class TestLoadDotenv(unittest.TestCase):
    """Test .env parsing."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self._saved_env = dict(os.environ)

    def tearDown(self):
        # Restore the environment exactly as it was.
        os.environ.clear()
        os.environ.update(self._saved_env)

    def test_missing_file_is_noop(self):
        # Should not raise and should not create the file.
        self.assertFalse(load_dotenv(self.tmpdir / "missing.env"))

    def test_loads_simple_key_value(self):
        env = self.tmpdir / ".env"
        env.write_text("MY_TEST_VAR=hello\n", encoding="utf-8")
        os.environ.pop("MY_TEST_VAR", None)

        self.assertTrue(load_dotenv(env))
        self.assertEqual(os.environ.get("MY_TEST_VAR"), "hello")

    def test_does_not_override_existing(self):
        os.environ["PRESET_VAR"] = "from-shell"
        env = self.tmpdir / ".env"
        env.write_text("PRESET_VAR=from-file\n", encoding="utf-8")

        load_dotenv(env)
        self.assertEqual(os.environ.get("PRESET_VAR"), "from-shell")

    def test_strips_quotes_and_comments(self):
        env = self.tmpdir / ".env"
        env.write_text(
            'QUOTED="double quoted"\n'
            "SINGLE='single quoted'\n"
            "WITH_COMMENT=value # trailing comment\n"
            "export EXPORTED=exported_val\n"
            "# full line comment\n"
            "BARE=bare_val\n",
            encoding="utf-8",
        )
        for k in ("QUOTED", "SINGLE", "WITH_COMMENT", "EXPORTED", "BARE"):
            os.environ.pop(k, None)

        load_dotenv(env)
        self.assertEqual(os.environ["QUOTED"], "double quoted")
        self.assertEqual(os.environ["SINGLE"], "single quoted")
        self.assertEqual(os.environ["WITH_COMMENT"], "value")
        self.assertEqual(os.environ["EXPORTED"], "exported_val")
        self.assertEqual(os.environ["BARE"], "bare_val")

    def test_blank_and_invalid_lines_ignored(self):
        env = self.tmpdir / ".env"
        env.write_text("\nNO_EQUALS_LINE\n=BADKEY\nKEY=val\n", encoding="utf-8")
        os.environ.pop("KEY", None)
        os.environ.pop("NO_EQUALS_LINE", None)
        os.environ.pop("BADKEY", None)

        load_dotenv(env)
        self.assertEqual(os.environ.get("KEY"), "val")
        self.assertNotIn("NO_EQUALS_LINE", os.environ)

    def test_load_default_env_with_extra_dir(self):
        env = self.tmpdir / ".env"
        env.write_text("DIR_TEST_VAR=dirval\n", encoding="utf-8")
        os.environ.pop("DIR_TEST_VAR", None)

        load_default_env([self.tmpdir])
        self.assertEqual(os.environ.get("DIR_TEST_VAR"), "dirval")


if __name__ == "__main__":
    unittest.main()
