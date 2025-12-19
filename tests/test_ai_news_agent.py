"""Tests for the AI News agent factory."""

from __future__ import annotations

import pathlib
import sys
import types
from unittest import mock

import pytest

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
  sys.path.insert(0, str(PROJECT_ROOT))

from agents.ai_news import build_agent
from agents.ai_news.agent import _AGENT_NAME, _OUTPUT_STATE_KEY
from google.adk.tools.mcp_tool import McpToolset, StreamableHTTPConnectionParams


def _make_context(topic: str) -> types.SimpleNamespace:
  """Create a lightweight context object with session state."""

  state = {"topic": topic}
  return types.SimpleNamespace(state=state)


def test_build_agent_uses_provided_toolset() -> None:
  """Factory should reuse the caller-supplied MCP toolset."""

  toolset = mock.MagicMock(spec=McpToolset)
  agent = build_agent(toolset=toolset)

  assert agent.name == _AGENT_NAME
  assert agent.output_key == _OUTPUT_STATE_KEY
  assert agent.model.model == "gemini-2.0-flash"
  assert agent.tools == [toolset]


def test_instruction_includes_topic_and_rules() -> None:
  """Instruction text should mention the topic and critical policies."""

  toolset = mock.MagicMock(spec=McpToolset)
  agent = build_agent(toolset=toolset)
  context = _make_context("frontier model safety")

  instruction = agent.instruction(context)

  assert "AI News" in instruction
  assert "200 words" in instruction
  assert "Focus topic" in instruction
  assert "frontier model safety" in instruction


def test_build_agent_requires_connection_details(monkeypatch: pytest.MonkeyPatch) -> None:
  """When no toolset is provided, a connection hint must be available."""

  monkeypatch.delenv("MCP_SERVER_WEB_URL", raising=False)

  with pytest.raises(ValueError):
    build_agent()


def test_build_agent_constructs_toolset(monkeypatch: pytest.MonkeyPatch) -> None:
  """Factory should create a filtered MCP toolset from connection params."""

  monkeypatch.delenv("MCP_SERVER_WEB_URL", raising=False)
  params = StreamableHTTPConnectionParams(url="http://localhost:8900")

  agent = build_agent(connection_params=params)

  assert isinstance(agent.tools[0], McpToolset)
  assert agent.tools[0].tool_filter == ["web_search", "url_reader"]
  assert agent.tools[0].tool_name_prefix == "ai_news"

