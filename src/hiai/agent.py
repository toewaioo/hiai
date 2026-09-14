"""AI agent loop with tool calling."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from hiai.client import OpenRouterClient
from hiai.exceptions import (
    AgentError,
    MaxIterationsError,
    MalformedToolCallError,
)
from hiai.models import AppConfig
from hiai.prompts import build_system_prompt
from hiai.terminal import error, success, thinking, tool_complete, tool_error, tool_start
from hiai.tools.executor import ToolRegistry


class Agent:
    """Conversational agent with tool-calling loop."""

    def __init__(
        self,
        config: AppConfig,
        project_root: Path,
        auto_approve: bool = False,
    ) -> None:
        self.config = config
        self.project_root = project_root
        self.auto_approve = auto_approve
        self.client = OpenRouterClient(
            base_url=config.base_url,
            api_key=config.api_key,
            timeout=config.timeout,
        )
        self.registry = ToolRegistry(project_root, auto_approve=auto_approve)
        self.messages: list[dict[str, Any]] = []
        self._init_messages()

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

    def chat(self, user_message: str) -> str:
        """Process a user message and return the assistant's response.

        Runs the full agent loop with tool calling.
        """
        self.messages.append({
            "role": "user",
            "content": user_message,
        })

        tools = self.registry.get_definitions()
        iteration = 0

        while iteration < self.config.max_iterations:
            iteration += 1
            thinking()

            try:
                response = self.client.chat_completion(
                    messages=self.messages,
                    model=self.config.model,
                    tools=tools,
                )
            except Exception as e:
                error(f"API error: {e}")
                return f"Error communicating with AI: {e}"

            choice = response.get("choices", [{}])[0]
            message = choice.get("message", {})

            content = message.get("content", "")
            tool_calls = message.get("tool_calls")

            if content:
                self.messages.append({
                    "role": "assistant",
                    "content": content,
                    **({"tool_calls": tool_calls} if tool_calls else {}),
                })

            if not tool_calls:
                return content or ""

            self.messages.append({
                "role": "assistant",
                "content": content or "",
                "tool_calls": tool_calls,
            })

            for tc in tool_calls:
                tc_id = tc.get("id", "")
                func = tc.get("function", {})
                tool_name = func.get("name", "")
                tool_args_raw = func.get("arguments", "{}")

                tool_start(tool_name)

                try:
                    result_str = self.registry.execute(tool_name, tool_args_raw)
                    result_data = json.loads(result_str)
                    tool_complete(tool_name)
                except MalformedToolCallError as e:
                    result_str = json.dumps({
                        "status": "error",
                        "message": str(e),
                    })
                    tool_error(tool_name, str(e))
                    result_data = {"status": "error", "message": str(e)}
                except Exception as e:
                    result_str = json.dumps({
                        "status": "error",
                        "message": f"Tool execution failed: {e}",
                    })
                    tool_error(tool_name, str(e))
                    result_data = {"status": "error", "message": str(e)}

                status = result_data.get("status", "")
                if status in ("cancelled",):
                    warning_msg = result_data.get("message", "Operation cancelled")
                    success(f"Tool result: {warning_msg}")
                elif status == "error":
                    pass
                else:
                    success(f"Tool completed: {tool_name}")

                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tc_id,
                    "content": result_str,
                })

        raise MaxIterationsError(
            f"Agent exceeded maximum iterations ({self.config.max_iterations})."
        )

    def get_status(self) -> dict[str, str]:
        """Return current session status."""
        return {
            "model": self.config.model,
            "project": str(self.project_root),
            "messages": str(len(self.messages)),
            "auto_approve": str(self.auto_approve),
        }
