"""Factory for the standalone AI News agent."""

from __future__ import annotations

import os
from typing import Optional, Union

from pydantic import BaseModel, Field

from google.adk.agents import LlmAgent
from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.models import Gemini
from google.adk.tools.mcp_tool import (
  McpToolset,
  SseConnectionParams,
  StreamableHTTPConnectionParams,
  StdioConnectionParams,
)

ConnectionParams = Union[
  StreamableHTTPConnectionParams,
  SseConnectionParams,
  StdioConnectionParams,
]

_DEFAULT_MODEL = "gemini-2.0-flash"
_AGENT_NAME = "AiNewsAgent"
_AGENT_DESCRIPTION = (
  "Fetches the latest AI-specific news and summarizes it in ≤200 words."
)
_OUTPUT_STATE_KEY = "ai_news_post"
_TOPIC_STATE_KEY = "topic"

_SYSTEM_PROMPT_HEADER = (
  "You are \"AI News\", a journalist-grade research agent focused on artificial "
  "intelligence developments."
)

_SYSTEM_PROMPT_RULES = """Follow these policies every time:
1. Only cover verifiable AI news published within the last 30 days.
2. Prioritize launch updates from OpenAI, Anthropic, Google DeepMind, Meta, and other top labs.
3. Discard anything unrelated to artificial intelligence.
4. Perform focused searches with `web_search` and inspect promising links via `url_reader` to confirm recency, source, and AI relevance.
5. Attribute launches, features, or metrics to their organizations or products.
6. Cap the final story at 200 words and keep it factual, concise, and high-signal.
7. Write the finished copy to the session key `ai_news_post`.
"""

_SYSTEM_PROMPT_DELIVERABLE = """Structure the final answer as:
- A punchy headline referencing the topic.
- 1–2 tight paragraphs (≤200 words total) synthesizing the freshest AI news found.
- Optional bullets for notable metrics or quotes.
Avoid filler, speculation, or stale history."
"""

class AiNewsInput(BaseModel):
  """Input schema for the AI News agent."""

  topic: str = Field(..., description="AI-focused topic or keyword supplied by the user.")


def _resolve_connection_params(
  *, connection_params: Optional[ConnectionParams]
) -> ConnectionParams:
  """Resolve MCP connection parameters from input or environment."""

  if connection_params is not None:
    return connection_params

  server_url = os.getenv("MCP_SERVER_WEB_URL")
  if not server_url:
    raise ValueError(
      "MCP_SERVER_WEB_URL must be set when no MCP connection_params are provided."
    )
  return StreamableHTTPConnectionParams(url=server_url)


def _build_toolset(
  *,
  connection_params: Optional[ConnectionParams],
  existing_toolset: Optional[McpToolset],
) -> McpToolset:
  """Create or reuse the MCP toolset for web research."""

  if existing_toolset is not None:
    return existing_toolset

  resolved_params = _resolve_connection_params(
    connection_params=connection_params
  )
  return McpToolset(
    connection_params=resolved_params,
    tool_filter=["web_search", "url_reader"],
    tool_name_prefix="ai_news",
  )


def _render_instruction(context: ReadonlyContext) -> str:
  """Compose the runtime instruction block for the agent."""

  topic = context.state.get(_TOPIC_STATE_KEY, "").strip()
  focus_line = (
    f"Focus topic: {topic}" if topic else "No topic provided; request clarification."
  )
  return (
    f"{_SYSTEM_PROMPT_HEADER}\n\n"
    f"{_SYSTEM_PROMPT_RULES}\n\n"
    f"{_SYSTEM_PROMPT_DELIVERABLE}\n\n"
    f"{focus_line}\n"
    "Log every source consulted and double-check publish dates before writing."
  )


def build_agent(
  *,
  connection_params: Optional[ConnectionParams] = None,
  toolset: Optional[McpToolset] = None,
  model: Optional[str] = None,
) -> LlmAgent:
  """Instantiate the AI News `LlmAgent` with MCP research tooling."""

  resolved_toolset = _build_toolset(
    connection_params=connection_params, existing_toolset=toolset
  )
  resolved_model = Gemini(model=model or _DEFAULT_MODEL)
  return LlmAgent(
    name=_AGENT_NAME,
    description=_AGENT_DESCRIPTION,
    instruction=_render_instruction,
    model=resolved_model,
    tools=[resolved_toolset],
    input_schema=AiNewsInput,
    output_key=_OUTPUT_STATE_KEY,
  )

