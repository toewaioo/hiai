"""Tests for conversation history save/load (B4)."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from hiai.agent import Agent
from hiai.models import AppConfig


def _make_response(content="ok"):
    return {"choices": [{"message": {"role": "assistant", "content": content}}]}


class TestHistorySaveLoad(unittest.TestCase):
    """Test Agent.save_history / load_history."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.config = AppConfig(api_key="test-key", model="test-model")

    @patch("hiai.client.AIClient.chat_completion")
    def test_save_then_load_round_trip(self, mock_chat):
        mock_chat.return_value = _make_response("answer")

        agent = Agent(self.config, self.tmpdir)
        agent.chat("hello")
        self.assertEqual(len(agent.messages), 3)  # system + user + assistant

        # Save to a custom path
        path = self.tmpdir / "sub" / "session.json"
        saved = agent.save_history(path)
        self.assertEqual(saved, path)
        self.assertTrue(path.is_file())

        # Load into a fresh agent
        agent2 = Agent(self.config, self.tmpdir)
        self.assertEqual(len(agent2.messages), 1)  # just system prompt
        self.assertTrue(agent2.load_history(path))
        # system (rebuilt) + user + assistant
        self.assertEqual(len(agent2.messages), 3)
        self.assertEqual(agent2.messages[0]["role"], "system")
        self.assertEqual(agent2.messages[1]["role"], "user")
        self.assertEqual(agent2.messages[1]["content"], "hello")
        self.assertEqual(agent2.messages[2]["role"], "assistant")
        self.assertEqual(agent2.messages[2]["content"], "answer")

    @patch("hiai.client.AIClient.chat_completion")
    def test_save_excludes_system_prompt(self, mock_chat):
        mock_chat.return_value = _make_response("answer")
        agent = Agent(self.config, self.tmpdir)
        agent.chat("hello")

        path = self.tmpdir / "s.json"
        agent.save_history(path)
        data = json.loads(path.read_text(encoding="utf-8"))
        roles = [m["role"] for m in data["messages"]]
        self.assertNotIn("system", roles)

    def test_load_missing_file_is_noop(self):
        agent = Agent(self.config, self.tmpdir)
        self.assertFalse(agent.load_history(self.tmpdir / "does-not-exist.json"))
        # Messages unchanged: only the system prompt.
        self.assertEqual(len(agent.messages), 1)
        self.assertEqual(agent.messages[0]["role"], "system")

    @patch("hiai.client.AIClient.chat_completion")
    def test_default_path_under_hiai_dir(self, mock_chat):
        mock_chat.return_value = _make_response("ok")
        agent = Agent(self.config, self.tmpdir)
        agent.chat("hi")

        saved = agent.save_history()
        self.assertEqual(saved, self.tmpdir / ".hiai" / "session.json")
        self.assertTrue(saved.is_file())

        # list_history finds it
        sessions = agent.list_history()
        self.assertEqual(len(sessions), 1)
        self.assertEqual(sessions[0].name, "session.json")

    @patch("hiai.client.AIClient.chat_completion")
    def test_load_rebuilds_system_prompt_for_current_root(self, mock_chat):
        mock_chat.return_value = _make_response("answer")
        agent = Agent(self.config, self.tmpdir)
        agent.chat("hello")
        path = self.tmpdir / "s.json"
        agent.save_history(path)

        # New agent on a different project root — system prompt must reflect
        # the new root, not the saved one.
        other_dir = Path(tempfile.mkdtemp())
        agent2 = Agent(self.config, other_dir)
        self.assertTrue(agent2.load_history(path))
        self.assertIn(str(other_dir), agent2.messages[0]["content"])


if __name__ == "__main__":
    unittest.main()
