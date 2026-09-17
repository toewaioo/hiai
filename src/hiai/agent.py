"""AI agent loop with tool calling."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from hiai.client import AIClient
from hiai.exceptions import (
    AgentError,
    MaxIterationsError,
    MalformedToolCallError,
    ToolError,
)
from hiai.models import AgentState, AppConfig
from hiai.prompts import build_system_prompt
from hiai.terminal import (
    agent_alive,
    agent_dead,
    agent_error_recovery,
    agent_state_changed,
    agent_status,
    error,
    stream_token,
    success,
    thinking,
    tool_complete,
    tool_detail,
    tool_error,
    tool_start,
    warning,
)
from hiai.tools.executor import ToolRegistry

# Transient errors that can be retried
_TRANSIENT_ERRORS = (ConnectionError, TimeoutError, OSError)


class Agent:
    """Conversational agent with tool-calling loop."""

    def __init__(
        self,
        config: AppConfig,
        project_root: Path,
        auto_approve: bool = False,
        stream: bool = False,
    ) -> None:
        self.config = config
        self.project_root = project_root
        self.auto_approve = auto_approve
        self.stream = stream
        self.client = AIClient(
            base_url=config.base_url,
            api_key=config.api_key,
            timeout=config.timeout,
            provider=config.provider,
            rate_limit=config.rate_limit,
        )
        self.registry = ToolRegistry(project_root, auto_approve=auto_approve, config=config)
        self.messages: list[dict[str, Any]] = []
        self._init_messages()

        # State tracking
        self._state = AgentState.IDLE
        self._state_changed_at = time.time()
        self._iteration = 0
        self._last_heartbeat = time.time()
        self._error_count = 0
        self._total_errors = 0
        self._start_time: float | None = None
        # Per-turn stats (B6)
        self._last_tokens_in = 0
        self._last_tokens_out = 0
        self._last_turn_elapsed = 0.0

    @property
    def state(self) -> AgentState:
        """Return current agent state."""
        return self._state

    @property
    def is_alive(self) -> bool:
        """Check if agent is in an active (non-dead) state."""
        return self._state not in (AgentState.DEAD,)

    @property
    def elapsed(self) -> float:
        """Return seconds since state change."""
        return time.time() - self._state_changed_at

    @property
    def total_elapsed(self) -> float:
        """Return total seconds since agent started."""
        if self._start_time is None:
            return 0.0
        return time.time() - self._start_time

    def _set_state(self, new_state: AgentState, detail: str = "") -> None:
        """Transition to a new state and display the change."""
        old_state = self._state
        self._state = new_state
        self._state_changed_at = time.time()
        self._last_heartbeat = time.time()

        if old_state != new_state:
            agent_state_changed(old_state.value, new_state.value, detail)

    def _init_messages(self) -> None:
        """Initialize conversation with system prompt."""
        system_prompt = build_system_prompt(str(self.project_root))
        self.messages.append({
            "role": "system",
            "content": system_prompt,
        })

    def clear_history(self) -> None:
        """Clear conversation history, keeping only the system prompt."""
        system_prompt = build_system_prompt(str(self.project_root))
        self.messages = [{"role": "system", "content": system_prompt}]

    def _history_dir(self) -> Path:
        """Return the project-local history directory."""
        return self.project_root / ".hiai"

    def default_history_path(self) -> Path:
        """Return the default session history path."""
        return self._history_dir() / "session.json"

    def save_history(self, path: Path | str | None = None) -> Path:
        """Save conversation history (minus the system prompt) to JSON.

        Returns the path written to.
        """
        target = Path(path) if path else self.default_history_path()
        target.parent.mkdir(parents=True, exist_ok=True)
        # Drop the leading system prompt; it is rebuilt on load.
        payload = [m for m in self.messages if m.get("role") != "system"]
        data = {
            "version": 1,
            "project_root": str(self.project_root),
            "messages": payload,
        }
        target.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return target

    def load_history(self, path: Path | str | None = None) -> bool:
        """Load conversation history from JSON, rebuilding the system prompt.

        Returns True on success, False if the file was missing/unreadable.
        """
        source = Path(path) if path else self.default_history_path()
        if not source.is_file():
            return False
        try:
            data = json.loads(source.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return False
        messages = data.get("messages") if isinstance(data, dict) else None
        if not isinstance(messages, list):
            return False
        system_prompt = build_system_prompt(str(self.project_root))
        self.messages = [{"role": "system", "content": system_prompt}]
        for m in messages:
            if isinstance(m, dict) and m.get("role") and m.get("content") is not None:
                self.messages.append(m)
        return True

    def list_history(self) -> list[Path]:
        """Return saved session files in the history directory, newest first."""
        d = self._history_dir()
        if not d.is_dir():
            return []
        files = [p for p in d.glob("*.json") if p.is_file()]
        try:
            files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        except OSError:
            pass
        return files

    def retry_last_turn(self) -> str | None:
        """Drop the last user+assistant exchange and re-run the last user prompt.

        Returns the new assistant response, or None if there was no prior turn.
        """
        # Find the last user message index
        last_user_idx = None
        for i in range(len(self.messages) - 1, -1, -1):
            if self.messages[i].get("role") == "user":
                last_user_idx = i
                break
        if last_user_idx is None:
            return None
        last_prompt = self.messages[last_user_idx].get("content", "")
        # Truncate everything from the last user message onward
        self.messages = self.messages[:last_user_idx]
        if not last_prompt:
            return None
        return self.chat(last_prompt)

    def chat(self, user_message: str) -> str:
        """Process a user message and return the assistant's response.

        Runs the full agent loop with tool calling.
        """
        self._start_time = time.time()
        self._iteration = 0
        self._set_state(AgentState.IDLE)
        self._error_count = 0
        # Reset per-turn stats
        self._last_tokens_in = 0
        self._last_tokens_out = 0
        self._last_turn_elapsed = 0.0

        self.messages.append({
            "role": "user",
            "content": user_message,
        })

        tools = self.registry.get_definitions()

        while self._iteration < self.config.max_iterations:
            self._iteration += 1
            self._set_state(AgentState.THINKING, f"iteration {self._iteration}")
            agent_alive(self._iteration, self.config.max_iterations, self._state.value)

            # Call API with retry on transient errors
            response = self._call_api_with_retry(tools)
            if response is None:
                self._set_state(AgentState.DEAD, "API failure")
                agent_dead("API failure after retries", self._iteration)
                return "Error: API request failed. Check your API key (hiai config set-key) and model (hiai config set-model)."

            # Track token usage if the provider reports it
            usage = response.get("usage")
            if isinstance(usage, dict):
                self._last_tokens_in = int(usage.get("prompt_tokens", 0)) or self._last_tokens_in
                self._last_tokens_out = int(usage.get("completion_tokens", 0)) or self._last_tokens_out

            choice = response.get("choices", [{}])[0]
            message = choice.get("message", {})

            content = message.get("content", "")
            tool_calls = message.get("tool_calls")

            if not tool_calls:
                if content:
                    self.messages.append({
                        "role": "assistant",
                        "content": content,
                    })
                self._set_state(AgentState.IDLE, "response ready")
                self._last_turn_elapsed = time.time() - (self._start_time or time.time())
                return content or ""

            self.messages.append({
                "role": "assistant",
                "content": content or "",
                "tool_calls": tool_calls,
            })

            # Execute all tool calls
            self._execute_tool_calls(tool_calls)

        self._set_state(AgentState.DEAD, "max iterations")
        agent_dead("max iterations exceeded", self._iteration)
        raise MaxIterationsError(
            f"Agent exceeded maximum iterations ({self.config.max_iterations})."
        )

    def _call_api_with_retry(self, tools: list[dict]) -> dict | None:
        """Call the API with retry logic for transient errors."""
        max_retries = 3
        last_error = None

        def _on_delta(text: str) -> None:
            stream_token(text)

        for attempt in range(max_retries):
            try:
                return self.client.chat_completion(
                    messages=self.messages,
                    model=self.config.model,
                    tools=tools,
                    stream=self.stream,
                    on_delta=_on_delta if self.stream else None,
                )
            except _TRANSIENT_ERRORS as e:
                last_error = e
                self._error_count += 1
                self._total_errors += 1
                if attempt < max_retries - 1:
                    agent_error_recovery(attempt + 1, max_retries, str(e))
                    time.sleep(min(2 ** attempt, 10))
                    continue
                error(f"API error (after {max_retries} attempts): {e}")
                return None
            except Exception as e:
                error(f"API error: {e}")
                return None

        return None

    def _execute_tool_calls(self, tool_calls: list[dict]) -> None:
        """Execute a list of tool calls and update state."""
        for tc in tool_calls:
            tc_id = tc.get("id", "")
            func = tc.get("function", {})
            tool_name = func.get("name", "")
            tool_args_raw = func.get("arguments", "{}")

            # Map tool name to agent state
            state_map = {
                "read_file": AgentState.READING,
                "write_file": AgentState.WRITING,
                "list_files": AgentState.READING,
                "search_files": AgentState.SEARCHING,
                "run_command": AgentState.EXECUTING,
                "web_search": AgentState.SEARCHING,
            }
            tool_state = state_map.get(tool_name, AgentState.EXECUTING)

            # Extract detail from args
            detail = self._extract_tool_detail(tool_name, tool_args_raw)
            self._set_state(tool_state, detail)
            tool_start(tool_name)

            result_str, result_data = self._execute_single_tool(tool_name, tool_args_raw)

            status = result_data.get("status", "")
            if status in ("error",):
                self._error_count += 1
                self._total_errors += 1
                tool_error(tool_name, result_data.get("message", "unknown error"))
            elif status in ("cancelled",):
                warning_msg = result_data.get("message", "Operation cancelled")
                warning(f"Tool result: {warning_msg}")
            else:
                tool_complete(tool_name)
                tool_detail(tool_name, result_data)

            self.messages.append({
                "role": "tool",
                "tool_call_id": tc_id,
                "content": result_str,
            })

    def _execute_single_tool(self, tool_name: str, tool_args_raw: str) -> tuple[str, dict]:
        """Execute a single tool call and return (result_str, result_data)."""
        try:
            result_str = self.registry.execute(tool_name, tool_args_raw)
            result_data = json.loads(result_str)
            return result_str, result_data
        except MalformedToolCallError as e:
            result_str = json.dumps({
                "status": "error",
                "message": f"Malformed tool call: {e}",
            })
            return result_str, {"status": "error", "message": str(e)}
        except ToolError as e:
            result_str = json.dumps({
                "status": "error",
                "message": f"Tool error ({tool_name}): {e}",
            })
            return result_str, {"status": "error", "message": str(e)}
        except Exception as e:
            result_str = json.dumps({
                "status": "error",
                "message": f"Unexpected error in {tool_name}: {e}",
            })
            return result_str, {"status": "error", "message": str(e)}

    def _extract_tool_detail(self, tool_name: str, tool_args_raw: str) -> str:
        """Extract human-readable detail from tool arguments."""
        try:
            args = json.loads(tool_args_raw) if isinstance(tool_args_raw, str) else tool_args_raw
        except (json.JSONDecodeError, TypeError):
            return ""

        if tool_name == "read_file":
            return args.get("path", "")
        elif tool_name == "write_file":
            return args.get("path", "")
        elif tool_name == "list_files":
            return args.get("path", ".")
        elif tool_name == "search_files":
            return f'"{args.get("query", "")}"'
        elif tool_name == "run_command":
            return args.get("command", "")
        elif tool_name == "web_search":
            return f'"{args.get("query", "")}"'
        return ""

    def get_status(self) -> dict[str, str]:
        """Return current session status."""
        return {
            "state": self._state.value,
            "model": self.config.model,
            "project": str(self.project_root),
            "messages": str(len(self.messages)),
            "iteration": f"{self._iteration}/{self.config.max_iterations}",
            "errors": str(self._total_errors),
            "elapsed": f"{self.total_elapsed:.1f}s",
            "auto_approve": str(self.auto_approve),
        }
