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
    "sh": "cyan",
}


def _colorize_inline_code(code: str) -> str:
    """Colorize inline code."""
    return _c("cyan", code)


def _colorize_code_line(line: str, lang: str) -> str:
    """Colorize a single line of code based on language."""
    lang_lower = lang.lower().strip()
    color = LANG_COLORS.get(lang_lower, "white")

    # Highlight keywords for common languages
    if lang_lower in ("python", "py"):
        return _highlight_python(line, color)
    elif lang_lower in ("javascript", "js", "typescript", "ts"):
        return _highlight_js(line, color)
    elif lang_lower in ("bash", "sh", "shell", "zsh"):
        return _highlight_shell(line, color)
    elif lang_lower == "json":
        return _highlight_json(line)
    elif lang_lower in ("yaml", "yml"):
        return _highlight_yaml(line)
    elif lang_lower == "rust":
        return _highlight_rust(line, color)
    elif lang_lower == "go":
        return _highlight_go(line, color)

    return _c(color, line)


def _highlight_python(line: str, base_color: str) -> str:
    """Basic Python syntax highlighting."""
    keywords = (
        "def ", "class ", "import ", "from ", "return ", "if ", "elif ", "else:",
        "for ", "while ", "with ", "as ", "try:", "except ", "finally:",
        "raise ", "yield ", "lambda ", "pass ", "break ", "continue ",
        "and ", "or ", "not ", "in ", "is ", "True", "False", "None",
        "self", "async ", "await ",
    )
    decorators = re.compile(r"^(\s*)(@\w+)")
    strings = re.compile(r'(\"\"\".*?\"\"\"|\'\'\'.*?\'\'\'|"[^"]*"|\'[^\']*\')')
    comments = re.compile(r"(\s*#.*)$")
    numbers = re.compile(r"\b(\d+\.?\d*)\b")
    funcs = re.compile(r"\b(\w+)\s*\(")

    # Handle decorators
    m = decorators.match(line)
    if m:
        return m.group(1) + _magenta(m.group(2)) + _c(base_color, line[m.end():])

    # Handle comments at end
    cm = comments.search(line)
    code_part = line[:cm.start()] if cm else line
    comment_part = cm.group(0) if cm else ""

    result = code_part

    # Strings
    def replace_string(m):
        return _yellow(m.group(0))
    result = strings.sub(replace_string, result)

    # Numbers
    result = numbers.sub(lambda m: _magenta(m.group(0)), result)

    # Function calls
    result = funcs.sub(lambda m: _cyan(m.group(1)) + "(", result)

    # Keywords
    for kw in keywords:
        result = result.replace(kw, _green(kw))

    if comment_part:
        result += _dim(comment_part)

    return result


def _highlight_js(line: str, base_color: str) -> str:
    """Basic JS/TS syntax highlighting."""
    keywords = (
        "const ", "let ", "var ", "function ", "return ", "if ", "else ",
        "for ", "while ", "do ", "switch ", "case ", "break ", "continue ",
        "class ", "extends ", "new ", "this ", "super ", "import ", "export ",
        "default ", "from ", "async ", "await ", "try ", "catch ", "finally ",
        "throw ", "typeof ", "instanceof ", "in ", "of ", "true", "false",
        "null", "undefined", "void ", "delete ", "yield ",
    )
    strings = re.compile(r'(`[^`]*`|"[^"]*"|\'[^\']*\')')
    comments = re.compile(r"(//.*$|/\*.*?\*/)")
    numbers = re.compile(r"\b(\d+\.?\d*)\b")
    funcs = re.compile(r"\b(\w+)\s*\(")

    cm = comments.search(line)
    code_part = line[:cm.start()] if cm else line
    comment_part = cm.group(0) if cm else ""

    result = code_part
    result = strings.sub(lambda m: _yellow(m.group(0)), result)
    result = numbers.sub(lambda m: _magenta(m.group(0)), result)
    result = funcs.sub(lambda m: _cyan(m.group(1)) + "(", result)
    for kw in keywords:
        result = result.replace(kw, _green(kw))

    if comment_part:
        result += _dim(comment_part)

    return result


def _highlight_shell(line: str, base_color: str) -> str:
    """Basic shell syntax highlighting."""
    result = line
    # Comments
    if "#" in result and not result.strip().startswith("#"):
        idx = result.index("#")
        code = result[:idx]
        comment = result[idx:]
        result = _highlight_shell_code(code) + _dim(comment)
    elif result.strip().startswith("#"):
        return _dim(result)
    else:
        result = _highlight_shell_code(result)
    return result


def _highlight_shell_code(code: str) -> str:
    """Highlight shell code portion."""
    keywords = (
        "if ", "then ", "else ", "elif ", "fi", "for ", "do ", "done",
        "while ", "case ", "esac", "function ", "return ", "exit ",
        "echo ", "printf ", "read ", "local ", "export ", "source ",
        "cd ", "ls ", "grep ", "sed ", "awk ", "find ", "mkdir ",
        "rm ", "cp ", "mv ", "cat ", "chmod ", "chown ",
    )
    strings = re.compile(r'("[^"]*"|\'[^\']*\')')
    variables = re.compile(r"(\$\w+|\$\{[^}]+\})")
    numbers = re.compile(r"\b(\d+)\b")

    result = code
    result = strings.sub(lambda m: _yellow(m.group(0)), result)
    result = variables.sub(lambda m: _magenta(m.group(0)), result)
    result = numbers.sub(lambda m: _cyan(m.group(0)), result)
    for kw in keywords:
        result = result.replace(kw, _green(kw))

    return result


def _highlight_json(line: str) -> str:
    """JSON syntax highlighting."""
    result = line
    # Keys
    result = re.sub(r'"([^"]+)"(\s*:)', lambda m: _cyan(f'"{m.group(1)}"') + m.group(2), result)
    # String values
    result = re.sub(r':\s*"([^"]*)"', lambda m: ": " + _yellow(f'"{m.group(1)}"'), result)
    # Numbers
    result = re.sub(r":\s*(\d+\.?\d*)", lambda m: ": " + _magenta(m.group(1)), result)
    # Booleans/null
    result = re.sub(r"\b(true|false|null)\b", lambda m: _green(m.group(0)), result)
    return result


def _highlight_yaml(line: str) -> str:
    """YAML syntax highlighting."""
    result = line
    # Comments
    if "#" in result:
        idx = result.index("#")
        code = result[:idx]
        comment = result[idx:]
        result = code + _dim(comment)
    # Keys
    result = re.sub(r"^(\s*)([\w-]+)(:)", lambda m: m.group(1) + _cyan(m.group(2)) + m.group(3), result)
    # Strings
    result = re.sub(r':\s*"([^"]*)"', lambda m: ": " + _yellow(f'"{m.group(1)}"'), result)
    # Booleans
    result = re.sub(r"\b(true|false|yes|no|null)\b", lambda m: _green(m.group(0)), result)
    return result


def _highlight_rust(line: str, base_color: str) -> str:
    """Basic Rust syntax highlighting."""
    keywords = (
        "fn ", "let ", "mut ", "pub ", "struct ", "enum ", "impl ", "trait ",
        "use ", "mod ", "crate ", "self ", "super ", "return ", "if ", "else ",
        "for ", "while ", "loop ", "match ", "break ", "continue ",
        "async ", "await ", "move ", "where ", "type ", "const ", "static ",
        "true", "false",
    )
    strings = re.compile(r'("(?:[^"\\]|\\.)*")')
    comments = re.compile(r"(//.*$|/\*.*?\*/)")
    numbers = re.compile(r"\b(\d+\.?\d*)\b")

    cm = comments.search(line)
    code_part = line[:cm.start()] if cm else line
    comment_part = cm.group(0) if cm else ""

    result = code_part
    result = strings.sub(lambda m: _yellow(m.group(0)), result)
    result = numbers.sub(lambda m: _magenta(m.group(0)), result)
    for kw in keywords:
        result = result.replace(kw, _green(kw))

    if comment_part:
        result += _dim(comment_part)

    return result


def _highlight_go(line: str, base_color: str) -> str:
    """Basic Go syntax highlighting."""
    keywords = (
        "func ", "package ", "import ", "return ", "if ", "else ", "for ",
        "range ", "switch ", "case ", "default ", "var ", "const ", "type ",
        "struct ", "interface ", "map ", "chan ", "go ", "defer ", "select ",
        "break ", "continue ", "fallthrough ", "nil", "true", "false",
    )
    strings = re.compile(r'("(?:[^"\\]|\\.)*"|`[^`]*`)')
    comments = re.compile(r"(//.*$|/\*.*?\*/)")
    numbers = re.compile(r"\b(\d+\.?\d*)\b")

    cm = comments.search(line)
    code_part = line[:cm.start()] if cm else line
    comment_part = cm.group(0) if cm else ""

    result = code_part
    result = strings.sub(lambda m: _yellow(m.group(0)), result)
    result = numbers.sub(lambda m: _magenta(m.group(0)), result)
    for kw in keywords:
        result = result.replace(kw, _green(kw))

    if comment_part:
        result += _dim(comment_part)

    return result


def _format_inline(text: str) -> str:
    """Format inline markdown (bold, italic, code, links)."""
    result = text

    # Inline code (must be first to avoid interference)
    result = re.sub(r"`([^`]+)`", lambda m: _colorize_inline_code(m.group(1)), result)

    # Bold + Italic
    result = re.sub(r"\*\*\*(.+?)\*\*\*", lambda m: _bold(_c("white", m.group(1))), result)
    result = re.sub(r"___(.+?)___", lambda m: _bold(_c("white", m.group(1))), result)

    # Bold
    result = re.sub(r"\*\*(.+?)\*\*", lambda m: _bold(m.group(1)), result)
    result = re.sub(r"__(.+?)__", lambda m: _bold(m.group(1)), result)

    # Italic
    result = re.sub(r"\*(.+?)\*", lambda m: _c("white", m.group(1)), result)
    result = re.sub(r"_(.+?)_", lambda m: _c("white", m.group(1)), result)

    # Strikethrough
    result = re.sub(r"~~(.+?)~~", lambda m: _dim(m.group(1)), result)

    # Links [text](url)
    result = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        lambda m: _cyan(m.group(1)) + _dim(f" ({m.group(2)})"),
        result,
    )

    # Images ![alt](url) → show as dimmed link
    result = re.sub(
        r"!\[([^\]]*)\]\(([^)]+)\)",
        lambda m: _dim(f"[image: {m.group(1) or m.group(2)}]"),
        result,
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
        if re.match(r"^[-*_]{3,}\s*$", line.strip()):
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
        m = re.match(r"^(\s*)([-*+])\s+(.+)$", line)
        if m:
            indent = m.group(1)
            bullet = m.group(2)
            content = m.group(3)
            formatted = _format_inline(content)
            output_lines.append(f"{indent}{_green(bullet)} {formatted}")
            i += 1
            continue

        # Ordered list
        m = re.match(r"^(\s*)(\d+[.)])\s+(.+)$", line)
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
            if re.match(r"^\s*\|[\s:|-]+\|\s*$", line):
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
