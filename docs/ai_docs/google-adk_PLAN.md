# ai_news Multi-Agent Architecture Plan

## Workflow Summary

- Upgrade the single-purpose `ai_news` agent into a manager-led, three-stage
  workflow that separates news search, post drafting, and quality review.
- Reuse Google ADK primitives only: `google.adk.agents.Agent`,
  `google.adk.tools.agent_tool.AgentTool`, and `google.adk.tools.google_search`.
- Maintain the 200-word cap, enforce <30 day recency, and surface a clear
  fallback when no relevant articles turn up.

## Current Architecture Inventory

- Code today: `agents/ai_news/agent.py` exports `root_agent = NewsAgent(...)`.
- `NewsAgent` subclasses `BaseAgent`, wraps a single `Agent` with the
  `google_search` tool, and intercepts tool responses to emit a fallback message.
- Limitations: no separation of concerns, no independent review phase, direct
  reliance on a custom base-agent subclass that duplicates ADK orchestration.

## Target Agent Architecture

### **Root Agent — `ai_news_manager`**

* **Agent Type**: `Agent`
* **Purpose**: Orchestrate topic intake, delegate to specialist agents in the
  order search → draft → review, consolidate the final response.
* **Sub-agents**: none (delegation uses `AgentTool`)
* **Tools**:
  * `AgentTool(ai_news_searcher)`
  * `AgentTool(ai_news_writer)`
  * `AgentTool(ai_news_reviewer)`
* **Callbacks**: none (reuse existing telemetry defaults)
* **Session State**: reads `user_topic`, writes `search_results`, `draft_post`,
  `review_feedback`, `final_post`
* **Model**: `gemini-1.5-flash`
* **Notes**: Replace the custom `NewsAgent` subclass with direct orchestration
  and explicit tool-call sequencing inside the root instruction prompt.

### **Search Specialist — `ai_news_searcher`**

* **Agent Type**: `Agent`
* **Purpose**: Use `google_search` to gather up to five AI-specific articles
  published within the last 30 days; return normalized JSON.
* **Sub-agents**: none
* **Tools**: `google_search`
* **Callbacks**: none
* **Session State**: reads `user_topic`, writes `search_results`
* **Model**: `gemini-1.5-flash`
* **Output Contract**:
  ```json
  {
    "articles": [
      {
        "title": "...",
        "url": "...",
        "source": "...",
        "published": "YYYY-MM-DD",
        "summary": "...",
        "ai_relevance": "why this matters"
      }
    ],
    "search_window_days": 30
  }
  ```
* **Fallback**: If zero articles returned, emit the existing message
  `"No recent AI news found on this topic."`.

### **Drafting Specialist — `ai_news_writer`**

* **Agent Type**: `Agent`
* **Purpose**: Transform `search_results` into a <=200 word post with inline
  bullet citations referencing article indices.
* **Sub-agents**: none
* **Tools**: none
* **Callbacks**: none
* **Session State**: reads `search_results`, writes `draft_post`
* **Model**: `gemini-1.5-flash`
* **Output Contract**:
  ```json
  {
    "post_markdown": "...",
    "sources_used": [0, 1, 2]
  }
  ```
* **Constraints**: Must decline to write if `articles` is empty and instead pass
  through the fallback message.

### **Quality Reviewer — `ai_news_reviewer`**

* **Agent Type**: `Agent`
* **Purpose**: Critique the draft for recency, factual grounding, tone, and word
  limit compliance; deliver an improved `final_post`.
* **Sub-agents**: none
* **Tools**: none
* **Callbacks**: none
* **Session State**: reads `draft_post`, `search_results`; writes
  `review_feedback`, `final_post`
* **Model**: `gemini-1.5-pro`
* **Output Contract**:
  ```json
  {
    "review_notes": "...",
    "revised_post_markdown": "...",
    "ready_for_publish": true
  }
  ```
* **Guardrails**: Flag posts exceeding 200 words or referencing stale articles,
  instructing the manager to request a rewrite if needed.

## Agent Connection Mapping

```
ai_news_manager (Agent) ✅
├─ AgentTool(ai_news_searcher) → populates session.state["search_results"]
├─ AgentTool(ai_news_writer) → populates session.state["draft_post"]
└─ AgentTool(ai_news_reviewer) → populates session.state["final_post"]
```

## Session State Keys (Target)

```yaml
user_topic: str  # injected from invocation context input.text
search_results:
  articles: list[{title, url, source, summary, published, ai_relevance}]
  search_window_days: int
draft_post:
  post_markdown: str
  sources_used: list[int]
review_feedback:
  review_notes: str
  issues_found: list[str]
final_post:
  revised_post_markdown: str
  ready_for_publish: bool
```

## Implementation Steps

1. Replace `NewsAgent` subclass in `agents/ai_news/agent.py` with a pure
   `Agent`-based hierarchy using the agents above and `AgentTool` delegation.
2. Define the three specialist agents with instructions enforcing JSON outputs,
   recency checks, and fallback behavior.
3. Update the root agent prompt to sequence tool calls and manage session state
   hand-offs via natural-language directives (no custom Python orchestration).
4. Add or update tests under `tests/` to cover success, no-result, and review
   revision scenarios using ADK test helpers.
5. Refresh documentation (`docs/ai_docs/google-adk.md`) after code changes to
  mirror the new hierarchy.

## Risks & Mitigations

- **LLM adherence to JSON schemas**: Mitigate by embedding explicit JSON schema
  instructions and example outputs within prompts.
- **Word-count enforcement**: Have the reviewer agent validate length and flag
  violations; optionally include tokenizer hints in writer instructions.
- **Tool overuse**: Manager instructions enforce single call per stage; avoid
  loops unless review flags issues.

## ADK Reuse Commitments

- `google.adk.agents.Agent` for every agent (no custom subclasses).
- `google.adk.tools.agent_tool.AgentTool` for root delegation.
- `google.adk.tools.google_search` as the sole external lookup tool.
- `InvocationContext.session.state` for lightweight state passing (no custom
  services or new utilities).

## Quality Checklist

- [x] Re-read `AGENTS.md` (2025-10-28) and `llms-full.txt` (2025-10-28) this
  session.
- [x] Referenced only existing ADK classes/tools; no new base classes proposed.
- [x] File paths and agent names match current repository casing.
- [x] State transitions cover success and fallback (“no news”).
- [x] Plan aligns with reuse-first policy; minimal net-new code.
- [x] Word count < 800 and template sections populated.
