"""Markdown to terminal formatter with colors."""

from __future__ import annotations

import re
from typing import TextIO

from hiai.constants import ANSI_COLORS
from hiai.terminal import USE_COLOR


def _c(code: str, text: str) -> str:
    """Wrap text with ANSI color if supported."""
    if not USE_COLOR:
        return text
    return f"{ANSI_COLORS.get(code, '')}{text}{ANSI_COLORS['reset']}"


def _bold(text: str) -> str:
    return _c("bold", text)


def _dim(text: str) -> str:
    return _c("dim", text)


def _cyan(text: str) -> str:
    return _c("cyan", text)


def _green(text: str) -> str:
    return _c("green", text)


def _yellow(text: str) -> str:
    return _c("yellow", text)


def _red(text: str) -> str:
    return _c("red", text)


def _blue(text: str) -> str:
    return _c("blue", text)


def _magenta(text: str) -> str:
    return _c("magenta", text)


def _white(text: str) -> str:
    return _c("white", text)


# Language → color mapping for code blocks
LANG_COLORS = {
    "python": "green",
    "py": "green",
    "javascript": "yellow",
    "js": "yellow",
    "typescript": "blue",
    "ts": "blue",
    "bash": "cyan",
    "sh": "cyan",
    "shell": "cyan",
    "zsh": "cyan",
    "json": "magenta",
    "yaml": "magenta",
    "yml": "magenta",
    "toml": "magenta",
    "html": "red",
    "css": "cyan",
    "sql": "yellow",
    "rust": "red",
    "go": "cyan",
    "java": "red",
    "c": "white",
    "cpp": "white",
    "c++": "white",
    "ruby": "red",
    "php": "magenta",
    "swift": "red",
    "kotlin": "magenta",
    "scala": "red",
    "r": "blue",
    "lua": "blue",
    "dart": "cyan",
    "dockerfile": "cyan",
    "makefile": "cyan",
    "markdown": "white",
    "md": "white",
    "txt": "white",
    "text": "white",
    "csv": "white",
    "xml": "yellow",
    "ini": "white",
    "env": "white",
    "gitignore": "white",
}


def _colorize_inline_code(code: str) -> str:
    """Colorize inline code."""
    return _c("cyan", code)


def _build_keyword_pattern(keywords: tuple[str, ...]) -> re.Pattern[str]:
    """Build a single word-boundary alternation for a keyword list."""
    escaped = sorted((re.escape(k) for k in keywords), key=len, reverse=True)
    return re.compile(r"\b(" + "|".join(escaped) + r")\b")


def _make_token_re(
    *,
    strings: str,
    comments: str,
    keywords: re.Pattern[str],
    extra: str = "",
) -> re.Pattern[str]:
    """Build a single-pass tokenizer: strings/comments/numbers/funcs/keywords.

    One combined alternation avoids re-scanning the line per token type and
    prevents ANSI escapes from later passes corrupting earlier ones.
    """
    parts = [
        f"(?P<str>{strings})",
        f"(?P<comment>{comments})",
    ]
    if extra:
        parts.append(f"(?P<extra>{extra})")
    parts.extend(
        [
            r"(?P<func>\b\w+(?=\s*\())",
            r"(?P<num>\b\d+\.?\d*\b)",
            f"(?P<kw>{keywords.pattern})",
        ]
    )
    return re.compile("|".join(parts))


_TOKEN_COLORS = {
    "str": "yellow",
    "comment": "dim",
    "extra": "magenta",
    "func": "cyan",
    "num": "magenta",
    "kw": "green",
}


def _apply_token_re(line: str, token_re: re.Pattern[str]) -> str:
    """Colorize a code line in one pass using a tokenizer regex."""

    def repl(m: re.Match[str]) -> str:
        color = _TOKEN_COLORS.get(m.lastgroup or "", "white")
        if color == "dim":
            return _dim(m.group(0))
        return _c(color, m.group(0))

    return token_re.sub(repl, line)


# --- Precompiled tokenizers (compiled once at import time) -------------------

_PY_KEYWORDS = _build_keyword_pattern(
    (
        "def", "class", "import", "from", "return", "if", "elif", "else",
        "for", "while", "with", "as", "try", "except", "finally",
        "raise", "yield", "lambda", "pass", "break", "continue",
        "and", "or", "not", "in", "is", "True", "False", "None",
        "self", "async", "await", "global", "nonlocal", "assert",
    )
)
_PY_TOKEN_RE = _make_token_re(
    strings=r"'''(?:[^'\\]|\\.)*'''|\"\"\"(?:[^\"\\]|\\.)*\"\"\"|'(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\"",
    comments=r"\#[^\n]*",
    keywords=_PY_KEYWORDS,
    extra=r"@\w+",
)

_JS_KEYWORDS = _build_keyword_pattern(
    (
        "const", "let", "var", "function", "return", "if", "else",
        "for", "while", "do", "switch", "case", "break", "continue",
        "class", "extends", "new", "this", "super", "import", "export",
        "default", "from", "async", "await", "try", "catch", "finally",
        "throw", "typeof", "instanceof", "in", "of", "true", "false",
        "null", "undefined", "void", "delete", "yield",
    )
)
_JS_TOKEN_RE = _make_token_re(
    strings=r"`[^`]*`|\"(?:[^\"\\]|\\.)*\"|'(?:[^'\\]|\\.)*'",
    comments=r"//[^\n]*|/\*.*?\*/",
    keywords=_JS_KEYWORDS,
)

_SHELL_KEYWORDS = _build_keyword_pattern(
    (
        "if", "then", "else", "elif", "fi", "for", "do", "done",
        "while", "case", "esac", "function", "return", "exit",
        "echo", "printf", "read", "local", "export", "source",
        "cd", "ls", "grep", "sed", "awk", "find", "mkdir",
        "rm", "cp", "mv", "cat", "chmod", "chown",
    )
)
_SHELL_TOKEN_RE = _make_token_re(
    strings=r"\"(?:[^\"\\]|\\.)*\"|'(?:[^'\\]|\\.)*'",
    comments=r"\#[^\n]*",
    keywords=_SHELL_KEYWORDS,
    extra=r"\$\w+|\$\{[^}]+\}",
)

_RUST_KEYWORDS = _build_keyword_pattern(
    (
        "fn", "let", "mut", "pub", "struct", "enum", "impl", "trait",
        "use", "mod", "crate", "self", "super", "return", "if", "else",
        "for", "while", "loop", "match", "break", "continue",
        "async", "await", "move", "where", "type", "const", "static",
        "true", "false",
    )
)
_RUST_TOKEN_RE = _make_token_re(
    strings=r"\"(?:[^\"\\]|\\.)*\"",
    comments=r"//[^\n]*|/\*.*?\*/",
    keywords=_RUST_KEYWORDS,
)

_GO_KEYWORDS = _build_keyword_pattern(
    (
        "func", "package", "import", "return", "if", "else", "for",
        "range", "switch", "case", "default", "var", "const", "type",
        "struct", "interface", "map", "chan", "go", "defer", "select",
        "break", "continue", "fallthrough", "nil", "true", "false",
    )
)
_GO_TOKEN_RE = _make_token_re(
    strings=r"\"(?:[^\"\\]|\\.)*\"|`[^`]*`",
    comments=r"//[^\n]*|/\*.*?\*/",
    keywords=_GO_KEYWORDS,
)

# JSON / YAML (kept as ordered substitutions; keys must color before values)
_JSON_KEY_RE = re.compile(r'"([^"]+)"(\s*:)')
_JSON_STR_VAL_RE = re.compile(r':\s*"([^"]*)"')
_JSON_NUM_RE = re.compile(r":\s*(\d+\.?\d*)")
_JSON_BOOL_RE = re.compile(r"\b(true|false|null)\b")
_YAML_COMMENT_RE = re.compile(r"(#.*)$")
_YAML_KEY_RE = re.compile(r"^(\s*)([\w-]+)(:)")
_YAML_STR_VAL_RE = re.compile(r':\s*"([^"]*)"')
_YAML_BOOL_RE = re.compile(r"\b(true|false|yes|no|null)\b")


def _colorize_code_line(line: str, lang: str) -> str:
    """Colorize a single line of code based on language."""
    lang_lower = lang.lower().strip()

    if lang_lower in ("python", "py"):
        return _apply_token_re(line, _PY_TOKEN_RE)
    if lang_lower in ("javascript", "js", "typescript", "ts", "jsx", "tsx"):
        return _apply_token_re(line, _JS_TOKEN_RE)
    if lang_lower in ("bash", "sh", "shell", "zsh"):
        return _apply_token_re(line, _SHELL_TOKEN_RE)
    if lang_lower == "json":
        return _highlight_json(line)
    if lang_lower in ("yaml", "yml"):
        return _highlight_yaml(line)
    if lang_lower == "rust":
        return _apply_token_re(line, _RUST_TOKEN_RE)
    if lang_lower == "go":
        return _apply_token_re(line, _GO_TOKEN_RE)

    return _c(LANG_COLORS.get(lang_lower, "white"), line)


def _highlight_python(line: str, base_color: str) -> str:
    """Basic Python syntax highlighting."""
    return _apply_token_re(line, _PY_TOKEN_RE)


def _highlight_js(line: str, base_color: str) -> str:
    """Basic JS/TS syntax highlighting."""
    return _apply_token_re(line, _JS_TOKEN_RE)


def _highlight_shell(line: str, base_color: str) -> str:
    """Basic shell syntax highlighting."""
    return _apply_token_re(line, _SHELL_TOKEN_RE)


def _highlight_json(line: str) -> str:
    """JSON syntax highlighting."""
    result = _JSON_KEY_RE.sub(
        lambda m: _c("cyan", f'"{m.group(1)}"') + m.group(2), line
    )
    result = _JSON_STR_VAL_RE.sub(
        lambda m: ": " + _yellow(f'"{m.group(1)}"'), result
    )
    result = _JSON_NUM_RE.sub(lambda m: ": " + _magenta(m.group(1)), result)
    return _JSON_BOOL_RE.sub(lambda m: _green(m.group(0)), result)


def _highlight_yaml(line: str) -> str:
    """YAML syntax highlighting."""
    result = line
    cm = _YAML_COMMENT_RE.search(result)
    if cm:
        result = result[: cm.start()] + _dim(cm.group(1))
    result = _YAML_KEY_RE.sub(
        lambda m: m.group(1) + _cyan(m.group(2)) + m.group(3), result
    )
    result = _YAML_STR_VAL_RE.sub(lambda m: ": " + _yellow(f'"{m.group(1)}"'), result)
    return _YAML_BOOL_RE.sub(lambda m: _green(m.group(0)), result)


def _highlight_rust(line: str, base_color: str) -> str:
    """Basic Rust syntax highlighting."""
    return _apply_token_re(line, _RUST_TOKEN_RE)


def _highlight_go(line: str, base_color: str) -> str:
    """Basic Go syntax highlighting."""
    return _apply_token_re(line, _GO_TOKEN_RE)


# Block-level patterns used by format_markdown
_HR_RE = re.compile(r"^[-*_]{3,}\s*$")
_ULIST_RE = re.compile(r"^(\s*)([-*+])\s+(.+)$")
_OLIST_RE = re.compile(r"^(\s*)(\d+[.)])\s+(.+)$")
_TABLE_SEP_RE = re.compile(r"^\s*\|[\s:|-]+\|\s*$")
# Inline markdown patterns (compiled once at import time)
_INLINE_CODE_RE = re.compile(r"`([^`]+)`")
_INLINE_BOLD_ITALIC_RE = re.compile(r"\*\*\*(.+?)\*\*\*|___(.+?)___")
_INLINE_BOLD_RE = re.compile(r"\*\*(.+?)\*\*|__(.+?)__")
_INLINE_ITALIC_RE = re.compile(r"\*(.+?)\*|_(.+?)_")
_INLINE_STRIKE_RE = re.compile(r"~~(.+?)~~")
_INLINE_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
_INLINE_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")


def _format_inline(text: str) -> str:
    """Format inline markdown (bold, italic, code, links)."""
    result = text

    # Inline code (must be first to avoid interference)
    result = _INLINE_CODE_RE.sub(lambda m: _colorize_inline_code(m.group(1)), result)

    # Bold + Italic
    result = _INLINE_BOLD_ITALIC_RE.sub(
        lambda m: _bold(_c("white", m.group(1) or m.group(2))), result
    )

    # Bold
    result = _INLINE_BOLD_RE.sub(lambda m: _bold(m.group(1) or m.group(2)), result)

    # Italic
    result = _INLINE_ITALIC_RE.sub(lambda m: _c("white", m.group(1) or m.group(2)), result)

    # Strikethrough
    result = _INLINE_STRIKE_RE.sub(lambda m: _dim(m.group(1)), result)

    # Images ![alt](url) → show as dimmed link (before links so ! is consumed)
    result = _INLINE_IMAGE_RE.sub(
        lambda m: _dim(f"[image: {m.group(1) or m.group(2)}]"), result
    )

    # Links [text](url)
    result = _INLINE_LINK_RE.sub(
        lambda m: _cyan(m.group(1)) + _dim(f" ({m.group(2)})"), result
    )

    return result


def format_markdown(text: str, file: TextIO | None = None) -> str:
    """Format markdown text for terminal display with colors.

    Returns the formatted string. Also prints to file if provided.
    """
    lines = text.split("\n")
    output_lines: list[str] = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Fenced code block: ```lang ... ```
        if line.strip().startswith("```"):
            lang = line.strip()[3:].strip()
            code_lines: list[str] = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            i += 1  # skip closing ```

            if code_lines:
                # Header line with language
                header = _dim(f"  ┌─ code {'─' * 34}")
                output_lines.append(header)

                for cl in code_lines:
                    colored = _colorize_code_line(cl, lang) if lang else _c("white", cl)
                    output_lines.append(f"  │ {colored}")

                output_lines.append(_dim(f"  └{'─' * 39}"))
                output_lines.append("")
            continue

        # Headers
        if line.startswith("# "):
            output_lines.append(_bold(_cyan(line[2:])))
            output_lines.append(_dim("─" * 50))
            i += 1
            continue
        if line.startswith("## "):
            output_lines.append(_bold(_green(line[3:])))
            i += 1
            continue
        if line.startswith("### "):
            output_lines.append(_bold(_yellow(line[4:])))
            i += 1
            continue
        if line.startswith("#### "):
            output_lines.append(_bold(_magenta(line[5:])))
            i += 1
            continue
        if line.startswith("##### "):
            output_lines.append(_bold(_white(line[6:])))
            i += 1
            continue

        # Horizontal rule
        if _HR_RE.match(line.strip()):
            output_lines.append(_dim("─" * 50))
            i += 1
            continue

        # Blockquote
        if line.strip().startswith("> "):
            content = line.strip()[2:]
            output_lines.append(_dim("│ ") + _format_inline(content))
            i += 1
            continue

        # Unordered list
        m = _ULIST_RE.match(line)
        if m:
            indent = m.group(1)
            bullet = m.group(2)
            content = m.group(3)
            formatted = _format_inline(content)
            output_lines.append(f"{indent}{_green(bullet)} {formatted}")
            i += 1
            continue

        # Ordered list
        m = _OLIST_RE.match(line)
        if m:
            indent = m.group(1)
            num = m.group(2)
            content = m.group(3)
            formatted = _format_inline(content)
            output_lines.append(f"{indent}{_cyan(num)} {formatted}")
            i += 1
            continue

        # Table (simple support)
        if "|" in line and line.strip().startswith("|"):
            # Skip separator lines
            if _TABLE_SEP_RE.match(line):
                i += 1
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            colored_cells = [_cyan(c) for c in cells]
            output_lines.append("  ".join(colored_cells))
            i += 1
            continue

        # Empty line
        if not line.strip():
            output_lines.append("")
            i += 1
            continue

        # Regular text with inline formatting
        output_lines.append(_format_inline(line))
        i += 1

    result = "\n".join(output_lines)

    if file:
        print(result, file=file)

    return result


def print_markdown(text: str) -> None:
    """Format and print markdown to stdout."""
    print(format_markdown(text))
