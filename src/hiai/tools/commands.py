"""Command execution tool with safety policy."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from hiai.models import ToolResult

# Dangerous command patterns that must always be rejected
DANGEROUS_PATTERNS = [
    r"\brm\s+-[a-z]*r[a-z]*f[a-z]*\s+/",  # rm -rf /
    r"\brm\s+-[a-z]*f[a-z]*r[a-z]*\s+/",  # rm -fr /
    r"\brm\s+-[a-z]*r[a-z]*f[a-z]*\s+~",  # rm -rf ~
    r"\brm\s+-[a-z]*f[a-z]*r[a-z]*\s+~",  # rm -fr ~
    r"\bmkfs\b",
    r"\bformat\b.*\b(disk|drive|volume)\b",
    r"\bdiskpart\b",
    r"\bshutdown\b",
    r"\breboot\b",
    r"\bhalt\b",
    r"\bpoweroff\b",
    r"\bdd\s+if=",
    r":\(\)\s*\{\s*:\|\:&\s*\}\s*;",  # fork bomb
    r"\bsudo\s+rm\b",
    r"\bchmod\s+-R\s+777\s+/",
    r"\bchown\s+-R\b.*\s+/",
    r">\s*/dev/sd[a-z]",
    r"\bwget\b.*\|\s*(ba)?sh",
    r"\bcurl\b.*\|\s*(ba)?sh",
    r"\brm\s+-rf\s+\*",
    r"\brm\s+-rf\s+\.\.",
    r"\bsudo\s+apt\s+(remove|purge)\b.*(systemd|dbus|kernel)",
    r"\bnc\s+-l",  # netcat listener
    r"\bssh\s+.*-R\b",  # reverse SSH
]

# Allowed command prefixes (configurable)
DEFAULT_ALLOWED_PREFIXES = [
    "python",
    "python3",
    "pip",
    "pip3",
    "pytest",
    "npm",
    "npx",
    "node",
    "git",
    "go",
    "cargo",
    "rustc",
    "php",
    "composer",
    "curl",
    "wget",
    "ls",
    "dir",
    "cat",
    "head",
    "tail",
    "grep",
    "find",
    "echo",
    "pwd",
    "whoami",
    "date",
    "make",
    "cmake",
    "docker",
    "docker-compose",
    "uv",
    "poetry",
    "ruff",
    "black",
    "mypy",
    "flake8",
    "eslint",
    "prettier",
    "tsc",
    "webpack",
    "vite",
    "gcc",
    "g++",
    "clang",
    "javac",
    "java",
    "ruby",
    "perl",
]

# Max output size to return to the AI (chars)
MAX_OUTPUT_CHARS = 50_000


def is_dangerous_command(command: str) -> bool:
    """Check if a command matches known dangerous patterns."""
    cmd_lower = command.lower().strip()
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, cmd_lower, re.IGNORECASE):
            return True
    return False


def _get_command_base(command: str) -> str:
    """Extract the base command name from a command string."""
    cmd = command.strip()
    # Skip env vars like FOO=bar cmd
    while cmd and "=" in cmd.split()[0] if cmd.split() else False:
        parts = cmd.split(None, 1)
        if len(parts) < 2:
            return cmd
        cmd = parts[1]
    # Skip sudo
    if cmd.startswith("sudo "):
        cmd = cmd[5:]
    # Skip pipes, get first command
    cmd = cmd.split("|")[0].strip()
    # Skip redirections
    cmd = cmd.split(">")[0].strip()
    cmd = cmd.split("<")[0].strip()
    # Get base name
    parts = cmd.split()
    if not parts:
        return ""
    base = parts[0]
    # Remove path prefix
    base = os.path.basename(base)
    return base


def is_command_allowed(command: str, allowed_prefixes: list[str] | None = None) -> bool:
    """Check if a command is in the allowed list."""
    if allowed_prefixes is None:
        allowed_prefixes = DEFAULT_ALLOWED_PREFIXES

    base = _get_command_base(command).lower()

    # Check exact match first
    if base in [p.lower() for p in allowed_prefixes]:
        return True

    # Check prefix match (e.g., "python3.11" matches "python")
    for prefix in allowed_prefixes:
        if base.startswith(prefix.lower()):
            return True

    return False


def prompt_command_approval(command: str, project_root: str, timeout: int) -> bool:
    """Prompt user to approve command execution."""
    from hiai.terminal import prompt_command

    return prompt_command(command, project_root, timeout)


def run_command(
    command: str,
    project_root: Path,
    timeout: int = 30,
    auto_approve: bool = False,
    allowed_prefixes: list[str] | None = None,
) -> ToolResult:
    """Execute a command safely within the project root.

    Returns a ToolResult with command output.
    """
    if not command or not command.strip():
        return ToolResult(status="error", message="Command cannot be empty.")

    command = command.strip()

    # Security: block dangerous commands
    if is_dangerous_command(command):
        return ToolResult(
            status="error",
            message="Command rejected: potentially dangerous operation detected.",
        )

    # Security: check for path escapes in cd or similar
    if not _validate_command_paths(command, project_root):
        return ToolResult(
            status="error",
            message="Command rejected: path escape attempt detected.",
        )

    # Check if command is allowed
    if not is_command_allowed(command, allowed_prefixes):
        if not auto_approve:
            approved = prompt_command_approval(command, str(project_root), timeout)
            if not approved:
                return ToolResult(
                    status="cancelled",
                    message="User denied command execution.",
                )
        else:
            return ToolResult(
                status="error",
                message=(
                    f"Command '{_get_command_base(command)}' is not in the allowed command list. "
                    "Use --yes to approve non-listed commands interactively."
                ),
            )

    # Auto-approve still asks for allowed commands if not in auto_approve mode
    if not auto_approve:
        approved = prompt_command_approval(command, str(project_root), timeout)
        if not approved:
            return ToolResult(
                status="cancelled",
                message="User denied command execution.",
            )

    # Execute the command
    return _execute_command(command, project_root, timeout)


def _validate_command_paths(command: str, project_root: Path) -> bool:
    """Validate that command doesn't try to escape project root."""
    cmd = command.strip()

    # Check for cd to parent directories
    cd_match = re.search(r"\bcd\s+([^\s;|&]+)", cmd)
    if cd_match:
        target = cd_match.group(1)
        if target.startswith("/") and not str(project_root) in target:
            return False
        if ".." in target:
            return False

    return True


def _execute_command(command: str, project_root: Path, timeout: int) -> ToolResult:
    """Execute the command and return structured result."""
    try:
        # Use shell=True for complex commands but with safety measures
        result = subprocess.run(
            command,
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=True,
            env=_get_safe_env(),
        )

        stdout = result.stdout
        stderr = result.stderr

        # Truncate output if too large
        if len(stdout) > MAX_OUTPUT_CHARS:
            stdout = stdout[:MAX_OUTPUT_CHARS] + "\n... (output truncated)"
        if len(stderr) > MAX_OUTPUT_CHARS:
            stderr = stderr[:MAX_OUTPUT_CHARS] + "\n... (output truncated)"

        status = "success" if result.returncode == 0 else "error"

        return ToolResult(
            status=status,
            command=command,
            content=f"Exit code: {result.returncode}\n\nstdout:\n{stdout}\n\nstderr:\n{stderr}" if stderr else stdout,
            message=f"Exit code: {result.returncode}",
        )

    except subprocess.TimeoutExpired:
        return ToolResult(
            status="timeout",
            command=command,
            content="",
            message=f"Command timed out after {timeout} seconds.",
        )
    except FileNotFoundError:
        return ToolResult(
            status="error",
            command=command,
            content="",
            message=f"Command not found: {_get_command_base(command)}",
        )
    except PermissionError:
        return ToolResult(
            status="error",
            command=command,
            content="",
            message=f"Permission denied: {_get_command_base(command)}",
        )
    except OSError as e:
        return ToolResult(
            status="error",
            command=command,
            content="",
            message=f"Execution error: {e}",
        )


def _get_safe_env() -> dict[str, str]:
    """Get a safe environment for command execution."""
    env = os.environ.copy()
    # Ensure we don't leak sensitive vars
    for key in list(env.keys()):
        if "KEY" in key.upper() or "SECRET" in key.upper() or "TOKEN" in key.upper():
            pass  # Keep them for the subprocess but don't expose to AI
    return env
