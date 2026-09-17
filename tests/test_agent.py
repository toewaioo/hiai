"""Tests for the agent loop."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from hiai.agent import Agent
from hiai.exceptions import MaxIterationsError
from hiai.models import AppConfig


class MockResponse:
    """Mock HTTP response."""

    def __init__(self, data, status=200):
        self.data = json.dumps(data).encode("utf-8")
        self.status = status

    def read(self):
        return self.data


def make_chat_response(content=None, tool_calls=None):
    """Create a mock chat completion response."""
    msg = {"role": "assistant", "content": content or ""}
    if tool_calls:
        msg["tool_calls"] = tool_calls
    return {"choices": [{"message": msg}]}


def make_tool_call(tool_id, name, arguments):
    """Create a mock tool call."""
    return {
        "id": tool_id,
        "type": "function",
        "function": {
            "name": name,
            "arguments": json.dumps(arguments) if isinstance(arguments, dict) else arguments,
        },
    }


class TestAgentSimpleResponse(unittest.TestCase):
    """Test agent with simple text response."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.config = AppConfig(api_key="test-key", model="test-model")

    @patch("hiai.client.AIClient.chat_completion")
    def test_simple_text_response(self, mock_chat):
        mock_chat.return_value = make_chat_response(content="Hello! How can I help?")

        agent = Agent(self.config, self.tmpdir)
        response = agent.chat("Hi")
        self.assertEqual(response, "Hello! How can I help?")

    @patch("hiai.client.AIClient.chat_completion")
    def test_conversation_history_grows(self, mock_chat):
        mock_chat.return_value = make_chat_response(content="OK")

        agent = Agent(self.config, self.tmpdir)
        agent.chat("First message")
        self.assertEqual(len(agent.messages), 3)  # system + user + assistant


class TestAgentToolCalls(unittest.TestCase):
    """Test agent with tool calling."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.config = AppConfig(api_key="test-key", model="test-model")

    @patch("hiai.client.AIClient.chat_completion")
    def test_tool_call_and_result(self, mock_chat):
        (self.tmpdir / "test.py").write_text("print('hello')")

        tool_response = make_chat_response(
            content="",
            tool_calls=[make_tool_call("call_1", "read_file", {"path": "test.py"})],
        )
        final_response = make_chat_response(content="The file contains a hello print.")

        mock_chat.side_effect = [tool_response, final_response]

        agent = Agent(self.config, self.tmpdir)
        response = agent.chat("Read test.py")
        self.assertEqual(response, "The file contains a hello print.")

    @patch("hiai.client.AIClient.chat_completion")
    def test_multiple_tool_calls(self, mock_chat):
        (self.tmpdir / "a.py").write_text("a")
        (self.tmpdir / "b.py").write_text("b")

        tool_response = make_chat_response(
            content="",
            tool_calls=[
                make_tool_call("call_1", "read_file", {"path": "a.py"}),
                make_tool_call("call_2", "read_file", {"path": "b.py"}),
            ],
        )
        final_response = make_chat_response(content="Done reading both files.")

        mock_chat.side_effect = [tool_response, final_response]

        agent = Agent(self.config, self.tmpdir)
        response = agent.chat("Read both files")
        self.assertEqual(response, "Done reading both files.")


class TestAgentMaxIterations(unittest.TestCase):
    """Test agent max iteration limit."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.config = AppConfig(api_key="test-key", max_iterations=2)

    @patch("hiai.client.AIClient.chat_completion")
    def test_max_iterations_reached(self, mock_chat):
        tool_response = make_chat_response(
            content="",
            tool_calls=[make_tool_call("call_1", "list_files", {"path": "."})],
        )
        mock_chat.return_value = tool_response

        agent = Agent(self.config, self.tmpdir)
        with self.assertRaises(MaxIterationsError):
            agent.chat("Do something")


class TestAgentClearHistory(unittest.TestCase):
    """Test clearing conversation history."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.config = AppConfig(api_key="test-key")

    @patch("hiai.client.AIClient.chat_completion")
    def test_clear_keeps_system_prompt(self, mock_chat):
        mock_chat.return_value = make_chat_response(content="OK")

        agent = Agent(self.config, self.tmpdir)
        agent.chat("Hello")
        agent.clear_history()

        self.assertEqual(len(agent.messages), 1)
        self.assertEqual(agent.messages[0]["role"], "system")


class TestAgentIterationReset(unittest.TestCase):
    """Test that the iteration counter resets between chat turns (bug A1)."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.config = AppConfig(api_key="test-key", max_iterations=3)

    @patch("hiai.client.AIClient.chat_completion")
    def test_iteration_resets_between_chats(self, mock_chat):
        # Each turn returns immediately (no tool calls) using exactly 1 iteration.
        mock_chat.return_value = make_chat_response(content="ok")

        agent = Agent(self.config, self.tmpdir)
        # Without the reset, the counter would accumulate and a 4th turn would
        # exceed max_iterations=3 and raise MaxIterationsError.
        agent.chat("turn 1")
        agent.chat("turn 2")
        agent.chat("turn 3")
        agent.chat("turn 4")  # would raise if counter leaked
        self.assertEqual(agent._iteration, 1)


class TestAgentRetry(unittest.TestCase):
    """Test retry_last_turn (B5)."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.config = AppConfig(api_key="test-key")

    @patch("hiai.client.AIClient.chat_completion")
    def test_retry_pops_last_turn(self, mock_chat):
        mock_chat.return_value = make_chat_response(content="first answer")
        agent = Agent(self.config, self.tmpdir)
        agent.chat("hello")
        self.assertEqual(len(agent.messages), 3)  # system + user + assistant

        mock_chat.return_value = make_chat_response(content="second answer")
        result = agent.retry_last_turn()
        self.assertEqual(result, "second answer")
        # The old assistant "first answer" must have been dropped; only one assistant remains.
        roles = [m["role"] for m in agent.messages]
        self.assertEqual(roles.count("user"), 1)
        self.assertEqual(roles.count("assistant"), 1)
        self.assertEqual(agent.messages[-1]["content"], "second answer")

    def test_retry_with_no_prior_turn_returns_none(self):
        agent = Agent(self.config, self.tmpdir)
        self.assertIsNone(agent.retry_last_turn())


class TestAgentGetStatus(unittest.TestCase):
    """Test agent status reporting."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.config = AppConfig(api_key="test-key", model="test-model")

    def test_status_fields(self):
        agent = Agent(self.config, self.tmpdir, auto_approve=True)
        status = agent.get_status()
        self.assertEqual(status["model"], "test-model")
        self.assertEqual(status["project"], str(self.tmpdir))
        self.assertEqual(status["auto_approve"], "True")


if __name__ == "__main__":
    unittest.main()
