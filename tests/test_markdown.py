"""Tests for markdown formatter."""

import unittest

from hiai.markdown import (
    _colorize_code_line,
    _format_inline,
    _highlight_json,
    _highlight_python,
    format_markdown,
)


class TestInlineFormatting(unittest.TestCase):
    """Test inline markdown formatting."""

    def test_inline_code(self):
        result = _format_inline("Use `pip install` to install")
        self.assertIn("pip install", result)

    def test_bold(self):
        result = _format_inline("This is **bold** text")
        self.assertIn("bold", result)

    def test_italic(self):
        result = _format_inline("This is *italic* text")
        self.assertIn("italic", result)

    def test_bold_italic(self):
        result = _format_inline("This is ***both*** text")
        self.assertIn("both", result)

    def test_strikethrough(self):
        result = _format_inline("This is ~~deleted~~ text")
        self.assertIn("deleted", result)

    def test_link(self):
        result = _format_inline("[Google](https://google.com)")
        self.assertIn("Google", result)
        self.assertIn("https://google.com", result)


class TestCodeBlockFormatting(unittest.TestCase):
    """Test code block formatting."""

    def test_code_block_with_lang(self):
        text = "```python\nprint('hello')\n```"
        result = format_markdown(text)
        self.assertIn("code", result)
        self.assertIn("print", result)

    def test_code_block_without_lang(self):
        text = "```\nsome code\n```"
        result = format_markdown(text)
        self.assertIn("some code", result)

    def test_code_block_preserves_content(self):
        text = "```bash\n#!/bin/bash\necho hello\n```"
        result = format_markdown(text)
        self.assertIn("#!/bin/bash", result)
        self.assertIn("echo hello", result)


class TestHeadings(unittest.TestCase):
    """Test heading formatting."""

    def test_h1(self):
        result = format_markdown("# Title")
        self.assertIn("Title", result)

    def test_h2(self):
        result = format_markdown("## Subtitle")
        self.assertIn("Subtitle", result)

    def test_h3(self):
        result = format_markdown("### Section")
        self.assertIn("Section", result)


class TestListFormatting(unittest.TestCase):
    """Test list formatting."""

    def test_unordered_list(self):
        text = "- item one\n- item two"
        result = format_markdown(text)
        self.assertIn("item one", result)
        self.assertIn("item two", result)

    def test_ordered_list(self):
        text = "1. first\n2. second"
        result = format_markdown(text)
        self.assertIn("first", result)
        self.assertIn("second", result)


class TestBlockquote(unittest.TestCase):
    """Test blockquote formatting."""

    def test_blockquote(self):
        text = "> This is a quote"
        result = format_markdown(text)
        self.assertIn("This is a quote", result)


class TestHorizontalRule(unittest.TestCase):
    """Test horizontal rule."""

    def test_horizontal_rule(self):
        text = "---"
        result = format_markdown(text)
        self.assertIn("─", result)


class TestPythonHighlighting(unittest.TestCase):
    """Test Python syntax highlighting."""

    def test_highlight_def(self):
        result = _highlight_python("def hello():", "green")
        self.assertIn("def", result)

    def test_highlight_import(self):
        result = _highlight_python("import os", "green")
        self.assertIn("import", result)

    def test_highlight_comment(self):
        result = _highlight_python("# comment", "green")
        self.assertIn("comment", result)


class TestJsonHighlighting(unittest.TestCase):
    """Test JSON syntax highlighting."""

    def test_highlight_key(self):
        result = _highlight_json('"name": "value"')
        self.assertIn("name", result)

    def test_highlight_string(self):
        result = _highlight_json('"key": "hello"')
        self.assertIn("hello", result)

    def test_highlight_number(self):
        result = _highlight_json('"count": 42')
        self.assertIn("42", result)


class TestMixedContent(unittest.TestCase):
    """Test mixed markdown content."""

    def test_headers_and_code(self):
        text = "# Title\n\n```python\ncode\n```\n\nSome text"
        result = format_markdown(text)
        self.assertIn("Title", result)
        self.assertIn("code", result)
        self.assertIn("Some text", result)

    def test_list_with_inline_code(self):
        text = "- Use `pip install` to install\n- Run `python main.py`"
        result = format_markdown(text)
        self.assertIn("pip install", result)
        self.assertIn("python main.py", result)


if __name__ == "__main__":
    unittest.main()
