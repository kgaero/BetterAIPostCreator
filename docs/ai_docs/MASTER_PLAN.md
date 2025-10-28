# MASTER_PLAN — AI News Multi-Agent Upgrade

## Feedback Integration

1. **Session state writes** — Addressed by implementing a lightweight custom
   `BaseAgent` orchestrator (`AiNewsPipelineManager`) that executes the three
   specialists sequentially, captures their emissions, and updates
   `ctx.session.state[...]` in Python (no reliance on LLM prompts for state).
2. **Reviewer remediation loop** — Manager inspects the reviewer payload; if
   `ready_for_publish` is false, it re-invokes the writer with reviewer notes
   (max one retry) before streaming the final post.
3. **Telemetry & budgeting** — Each agent will emit INFO logs via
   `ctx.logger.info`, and `RunConfig(max_llm_calls=4, max_output_tokens=2048)`
   will bound calls. Search agent enforces a single `google_search` invocation.
4. **Failure handling** — Manager short-circuits execution when search returns
   zero articles, propagating the fallback message without invoking writer or
   reviewer.
5. **Prompt specificity** — Detailed instruction blocks (with JSON examples and
   edge-case guidance) will back each specialist’s contract.

## Target Architecture

### Orchestration Layer — `AiNewsPipelineManager`

* **Type**: `BaseAgent` subclass (custom, deterministic)
* **Purpose**: Deterministically run search → draft → review, manage retries,
  enforce branch logic, and surface telemetry.
* **Sub-agents**: `ai_news_searcher`, `ai_news_writer`, `ai_news_reviewer`
  (invoked via direct `await sub_agent.run_async(ctx)` calls).
* **Tools**: none
* **Session State Writes**:
  * `user_topic` from invocation input.
  * `search_results` (dict) from search agent JSON.
  * `draft_post` (dict) from writer output.
  * `review_feedback` + `final_post` from reviewer output.
* **RunConfig**: `RunConfig(max_llm_calls=4, max_output_tokens=2048,
  max_execution_time_s=90)`
* **Logging**: emits stage start/end and fallback decisions with elapsed times.
* **Control Flow**:
  1. Persist `user_topic`.
  2. Call searcher; handle empty `articles` by publishing fallback message.
  3. Call writer; store draft; on reviewer rejection, re-call writer once using
     reviewer notes.
  4. Emit reviewer summary + final post.

### Agent 1 — `ai_news_searcher`

* **Type**: `Agent`
* **Model**: `gemini-1.5-flash`
* **Tools**: `[google_search]`
* **Instruction Highlights**:
  * Issue exactly one search call focused on AI developments in last 30 days.
  * Return JSON matching schema; include confidence note per article.
  * When no relevant hits, respond with `{"articles": [], "message": "..."}`
    using the mandated fallback string.
* **RunConfig**: `RunConfig(max_llm_calls=1, temperature=0.3)`

### Agent 2 — `ai_news_writer`

* **Type**: `Agent`
* **Model**: `gemini-1.5-flash`
* **Tools**: none
* **Inputs**: `search_results` (manager attaches JSON), optional
  `review_feedback.review_notes` for retry.
* **Instruction Highlights**:
  * Produce <=200 word markdown with inline numeric citations `[1]`.
  * Decline gracefully if `articles` empty by returning the fallback message
    payload instead of prose.
  * Output schema:
    ```json
    {"post_markdown": "...", "sources_used": [0,1], "word_count": 187}
    ```
* **RunConfig**: `RunConfig(max_llm_calls=1, temperature=0.4)`

### Agent 3 — `ai_news_reviewer`

* **Type**: `Agent`
* **Model**: `gemini-1.5-pro`
* **Tools**: none
* **Inputs**: `draft_post`, `search_results`
* **Instruction Highlights**:
  * Validate factual grounding versus provided article summaries.
  * Check word count, tone, citation coverage, and recency.
  * Return:
    ```json
    {
      "review_notes": "...",
      "issues_found": ["over 200 words"],
      "revised_post_markdown": "...",
      "ready_for_publish": true
    }
    ```
* **RunConfig**: `RunConfig(max_llm_calls=1, temperature=0.2)`
* **Manager Handling**: If `ready_for_publish` false, manager forwards
  `review_notes` back to writer for a single revision and re-runs reviewer once.

## Control Diagram

```
AiNewsPipelineManager (BaseAgent) ✅
├─ ai_news_searcher (Agent + google_search) → search_results
├─ ai_news_writer (Agent) → draft_post
└─ ai_news_reviewer (Agent) → review_feedback, final_post
    ↺ (optional) manager-triggered rewrite loop (max 1 iteration)
```

## Failure & Retry Matrix

| Stage   | Failure Condition                          | Manager Response                    |
|---------|---------------------------------------------|-------------------------------------|
| Search  | `articles` empty / tool error               | Emit fallback message; stop.        |
| Writer  | JSON parse fails / missing citations        | Retry once with tightened prompt.   |
| Review  | `ready_for_publish` false or JSON invalid   | Request rewrite (one loop), else surface reviewer notes plus fallback message. |

All retries are bounded to keep within `max_llm_calls`.

## Telemetry & Observability

- `ctx.logger.info` for stage start/end, article counts, retry decisions.
- Structured debug entries for JSON payloads (truncated to avoid PII).
- Future hook: integrate with ADK tracing once available; scaffolding left in
  place via `ctx.tracer`.

## Testing Strategy

1. **Happy Path**: seeded search payload with >=3 articles produces final post.
2. **No Results**: searcher returns empty list; ensure manager outputs fallback.
3. **Reviewer Rejects**: first draft over 200 words triggers rewrite loop; confirm final output obeys cap and reviewer marks publishable.
4. **Malformed Writer Output**: simulate invalid JSON → manager logs error and surfaces diagnostic while staying within retry budget.

Tests will use ADK `FakeTool` patterns from `refs/adk-samples` (read-only) for deterministic tool responses.

## Implementation Sequence

1. Create specialist agents (`ai_news_searcher`, `ai_news_writer`, `ai_news_reviewer`) in `agents/ai_news/agent.py` using `Agent` class and RunConfigs above.
2. Implement `AiNewsPipelineManager(BaseAgent)` to orchestrate specialists, manage state writes, retries, and logging.
3. Export `root_agent = AiNewsPipelineManager(...)`.
4. Update documentation (`docs/ai_docs/google-adk.md`) to mirror new architecture.
5. Add regression tests under `tests/ai_news/` covering scenarios listed.

## Reuse Statement

- Agents continue to rely on `google.adk.agents.Agent`, `BaseAgent`,
  `google.adk.tools.google_search`, `RunConfig`, and logging utilities supplied
  by ADK—no bespoke frameworks introduced.

## Sign-off Request

Please review and approve this MASTER_PLAN. Implementation will begin only after your explicit confirmation.
