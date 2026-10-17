"""Terminal output formatting and user interaction."""

from __future__ import annotations

import os
import sys
import threading
import time
from typing import TextIO

from hiai.constants import ANSI_COLORS


def _is_tty(stream: TextIO | None = None) -> bool:
    """Check whether a stream is an interactive terminal."""
    stream = stream or sys.stdout
    return hasattr(stream, "isatty") and stream.isatty()


def _supports_color() -> bool:
    """Check if the terminal supports color output."""
    if os.environ.get("NO_COLOR"):
        return False
    if not _is_tty():
        return False
    term = os.environ.get("TERM", "")
    return "dumb" not in term


USE_COLOR = _supports_color()


def _c(code: str, text: str) -> str:
    """Wrap text with ANSI color code if colors are supported."""
    if not USE_COLOR:
        return text
    return f"{ANSI_COLORS.get(code, '')}{text}{ANSI_COLORS['reset']}"


class Spinner:
    """Animated single-line status indicator with a live elapsed timer.

    Rewrites one terminal line instead of printing a new line per status
    update, keeping the transcript clean. No-op when stdout is not a TTY.
    """

    FRAMES = ("⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏")

    def __init__(self, enabled: bool | None = None) -> None:
        self._enabled = _is_tty() if enabled is None else enabled
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._message = ""
        self._started_at = 0.0
        self._active = False

    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def active(self) -> bool:
        return self._active

    def start(self, message: str = "") -> None:
        """Start (or update) the spinner with an initial message."""
        if not self._enabled:
            return
        if self._active:
            self.update(message)
            return
        self._message = message
        self._started_at = time.monotonic()
        self._active = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def update(self, message: str) -> None:
        """Update the spinner message (no-op if not running)."""
        if not self._active:
            return
        with self._lock:
            self._message = message

    def stop(self, final: str | None = None) -> None:
        """Stop the spinner, clear its line, optionally print a final message."""
        if not self._active:
            return
        self._active = False
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=0.25)
            self._thread = None
        self._clear_line()
        if final:
            print(final)

    def _run(self) -> None:
        idx = 0
        while not self._stop_event.wait(0.09):
            frame = self.FRAMES[idx % len(self.FRAMES)]
            idx += 1
            with self._lock:
                message = self._message
            elapsed = _format_elapsed(time.monotonic() - self._started_at)
            line = f"{_c('cyan', frame)} {_c('dim', message)} {_c('dim', elapsed)}"
            try:
                sys.stdout.write("\r\033[K" + line)
                sys.stdout.flush()
            except OSError:
                break

    @staticmethod
    def _clear_line() -> None:
        try:
            sys.stdout.write("\r\033[K")
            sys.stdout.flush()
        except OSError:
            pass


def info(message: str) -> None:
    """Print an informational message."""
    print(_c("cyan", f"ℹ {message}"))


def success(message: str) -> None:
    """Print a success message."""
    print(_c("green", f"✓ {message}"))


def error(message: str) -> None:
    """Print an error message."""
    print(_c("red", f"✗ {message}"), file=sys.stderr)


def warning(message: str) -> None:
    """Print a warning message."""
    print(_c("yellow", f"⚠ {message}"))


def thinking() -> None:
    """Show thinking indicator."""
    print(_c("dim", "HIAI is thinking..."))


def stream_token(text: str) -> None:
    """Write a streaming token to stdout without a trailing newline.

    Callers opt in via the agent's stream mode; tokens are written as they
    arrive so piped output also receives the full response.
    """
    try:
        sys.stdout.write(text)
        sys.stdout.flush()
    except OSError:
        pass


def print_stats(tokens_in: int, tokens_out: int, elapsed: float) -> None:
    """Print a compact per-turn stats line (tokens and timing)."""
    if not _is_tty():
        return
    parts = [f"done in {_format_elapsed(elapsed)}"]
    if tokens_in or tokens_out:
        parts.append(f"{tokens_in:,} in / {tokens_out:,} out tokens")
    print(_c("dim", "  ✓ " + " · ".join(parts)))


def tool_start(tool_name: str) -> None:
    """Show tool execution start."""
    print(_c("cyan", f"⚙ Tool: {tool_name}"))


def tool_complete(tool_name: str) -> None:
    """Show tool execution complete."""
    print(_c("green", f"✓ Tool completed: {tool_name}"))


def tool_error(tool_name: str, message: str) -> None:
    """Show tool execution error."""
    print(_c("red", f"✗ Tool error ({tool_name}): {message}"))


def prompt_command(command: str, project_root: str, timeout: int) -> bool:
    """Prompt user to approve a command execution."""
    print(_c("yellow", "┌─ Command execution requested " + "─" * 20))
    print(_c("yellow", f"│ Command: {command}"))
    print(_c("yellow", f"│ Directory: {project_root}"))
    print(_c("yellow", f"│ Timeout: {timeout} seconds"))
    print(_c("yellow", "└" + "─" * 40))

    try:
        answer = input(_c("bold", "Allow command? [y/N]: ")).strip().lower()
        return answer in ("y", "yes")
    except (EOFError, KeyboardInterrupt):
        return False


def tool_search_start(query: str) -> None:
    """Show search execution start."""
    print(_c("cyan", "⚙ Tool: web_search"))
    print(_c("dim", f"  🔎 Query: {query}"))


def tool_command_start(command: str) -> None:
    """Show command execution start."""
    print(_c("cyan", "⚙ Tool: run_command"))
    print(_c("dim", f"  ⌘ Command: {command}"))


def prompt_write(path: str, is_new: bool, size: int) -> bool:
    """Prompt user to approve a file write."""
    op = "Create" if is_new else "Update"
    size_str = _format_size(size)

    print(_c("yellow", "┌─ File write requested " + "─" * 30))
    print(_c("yellow", f"│ Path: {path}"))
    print(_c("yellow", f"│ Operation: {op}"))
    print(_c("yellow", f"│ Size: {size_str}"))
    print(_c("yellow", "└" + "─" * 40))

    try:
        answer = input(_c("bold", "Allow write? [y/N]: ")).strip().lower()
        return answer in ("y", "yes")
    except (EOFError, KeyboardInterrupt):
        return False


def prompt_sensitive_read(path: str) -> bool:
    """Prompt user to approve reading a sensitive file."""
    print(_c("yellow", f"⚠ Sensitive file detected: {path}"))
    try:
        answer = input(_c("bold", "Allow read? [y/N]: ")).strip().lower()
        return answer in ("y", "yes")
    except (EOFError, KeyboardInterrupt):
        return False


def prompt_api_key(provider: str = "openrouter") -> str | None:
    """Prompt user to enter an API key."""
    provider_name = "Groq" if provider == "groq" else "OpenRouter"
    try:
        print(_c("yellow", f"Enter your {provider_name} API key:"))
        key = input(_c("bold", "API Key: ")).strip()
        return key if key else None
    except (EOFError, KeyboardInterrupt):
        return None


def print_banner(project_dir: str, model: str) -> None:
    """Print the HIAI banner."""
    from hiai.constants import BANNER

    print(_c("cyan", BANNER))
    print(_c("dim", "HIAI — Local AI Coding Agent"))
    print()
    print(f"  Project: {_c('white', project_dir)}")
    print(f"  Model:   {_c('white', model)}")
    print()


def print_config_display(config: dict[str, str]) -> None:
    """Print configuration in a formatted way."""
    print(_c("bold", "HIAI Configuration"))
    print("─" * 40)
    for key, value in config.items():
        print(f"  {_c('cyan', key + ':'):25s} {value}")
    print()


def _format_size(size_bytes: int) -> str:
    """Format byte size to human-readable string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def _count_lines(text: str) -> int:
    """Count lines in text content."""
    return len(text.splitlines())


def _format_elapsed(seconds: float) -> str:
    """Format elapsed time to human-readable string."""
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    else:
        m = int(seconds // 60)
        s = seconds % 60
        return f"{m}m {s:.0f}s"


def agent_status(state: str, detail: str = "", elapsed: float = 0.0) -> None:
    """Show live agent status with state, detail, and elapsed time."""
    from hiai.models import AgentState

    try:
        agent_state = AgentState(state)
        icon = agent_state.icon
    except ValueError:
        icon = "·"

    elapsed_str = f" ({_format_elapsed(elapsed)})" if elapsed > 0 else ""
    detail_str = f" — {detail}" if detail else ""
    print(_c("dim", f"  {icon} {state}{elapsed_str}{detail_str}"))


def agent_alive(iteration: int, max_iterations: int, state: str) -> None:
    """Show agent alive heartbeat."""
    from hiai.models import AgentState

    try:
        agent_state = AgentState(state)
        icon = agent_state.icon
    except ValueError:
        icon = "·"

    print(_c("dim", f"  ♥ Agent alive | iter {iteration}/{max_iterations} | {icon} {state}"))


def agent_dead(reason: str, iteration: int) -> None:
    """Show agent dead notification."""
    print(_c("red", f"  💀 Agent stopped: {reason} (iteration {iteration})"))


def agent_error_recovery(attempt: int, max_attempts: int, error_msg: str) -> None:
    """Show error recovery attempt."""
    print(_c("yellow", f"  ⚠ Recovery attempt {attempt}/{max_attempts}: {error_msg}"))


def agent_state_changed(old_state: str, new_state: str, detail: str = "") -> None:
    """Show agent state transition."""
    from hiai.models import AgentState

    try:
        old_s = AgentState(old_state)
        new_s = AgentState(new_state)
        old_icon = old_s.icon
        new_icon = new_s.icon
    except ValueError:
        old_icon = "·"
        new_icon = "·"

    detail_str = f" ({detail})" if detail else ""
    print(_c("dim", f"  {old_icon} → {new_icon} {new_state}{detail_str}"))


def tool_detail(tool_name: str, result_data: dict) -> None:
    """Show detailed tool result information after execution."""
    status = result_data.get("status", "")
    if status in ("error", "cancelled", "timeout"):
        return

    if tool_name == "read_file":
        _detail_read_file(result_data)
    elif tool_name == "write_file":
        _detail_write_file(result_data)
    elif tool_name == "list_files":
        _detail_list_files(result_data)
    elif tool_name == "search_files":
        _detail_search_files(result_data)
    elif tool_name == "run_command":
        _detail_run_command(result_data)
    elif tool_name == "web_search":
        _detail_web_search(result_data)


def _detail_read_file(data: dict) -> None:
    """Display read_file details."""
    path = data.get("path", "")
    content = data.get("content", "")
    size = data.get("bytes", 0)

    if content:
        lines = _count_lines(content)
        size_str = _format_size(size) if size else f"{len(content.encode('utf-8'))} B"
        print(_c("dim", f"  📄 {path} ({lines} lines, {size_str})"))
    else:
        print(_c("dim", f"  📄 {path} (empty)"))


def _detail_write_file(data: dict) -> None:
    """Display write_file details."""
    path = data.get("path", "")
    size = data.get("bytes", 0)
    op = data.get("operation", "")

    op_label = "created" if op == "created" else "updated"
    size_str = _format_size(size) if size else ""
    suffix = f", {size_str}" if size_str else ""
    print(_c("dim", f"  ✏️  {path} ({op_label}{suffix})"))


def _detail_list_files(data: dict) -> None:
    """Display list_files details."""
    path = data.get("path", "")
    files = data.get("files", [])
    status = data.get("status", "")

    count = len(files)
    trunc = " (truncated)" if status == "truncated" else ""
    print(_c("dim", f"  📁 {count} items in {path}{trunc}"))

    if count > 0:
        show = files[:8]
        remaining = count - len(show)
        for f in show:
            print(_c("dim", f"     {f}"))
        if remaining > 0:
            print(_c("dim", f"     ... and {remaining} more"))


def _detail_search_files(data: dict) -> None:
    """Display search_files details."""
    query = data.get("query", "")
    matches = data.get("matches", [])
    status = data.get("status", "")

    count = len(matches)
    trunc = " (truncated)" if status == "truncated" else ""
    print(_c("dim", f"  🔎 {count} matches for \"{query}\"{trunc}"))

    if count > 0:
        show = matches[:5]
        for m in show:
            mpath = m.get("path", "")
            line = m.get("line", 0)
            text = m.get("text", "").strip()[:80]
            print(_c("dim", f"     {mpath}:{line} — {text}"))
        remaining = count - len(show)
        if remaining > 0:
            print(_c("dim", f"     ... and {remaining} more matches"))


def _detail_run_command(data: dict) -> None:
    """Display run_command details."""
    command = data.get("command", "")
    content = data.get("content", "")

    print(_c("dim", f"  ⌘ $ {command}"))

    if content:
        lines = content.strip().splitlines()
        max_lines = 20
        for line in lines[:max_lines]:
            print(_c("dim", f"     {line}"))
        remaining = len(lines) - max_lines
        if remaining > 0:
            print(_c("dim", f"     ... {remaining} more lines"))


def _detail_web_search(data: dict) -> None:
    """Display web_search details."""
    query = data.get("query", "")

    content_str = data.get("content", "")
    if content_str:
        try:
            import json
            results_data = json.loads(content_str)
            results = results_data.get("results", [])
            count = len(results)
            print(_c("dim", f"  🔎 {count} results for \"{query}\""))

            if count > 0:
                for r in results[:3]:
                    title = r.get("title", "")[:60]
                    url = r.get("url", "")
                    print(_c("dim", f"     {title}"))
                    if url:
                        print(_c("dim", f"       {url}"))
                remaining = count - 3
                if remaining > 0:
                    print(_c("dim", f"     ... and {remaining} more"))
        except (json.JSONDecodeError, AttributeError):
            pass
    else:
        message = data.get("message", "")
        if message:
            print(_c("dim", f"  🔎 {message}"))
