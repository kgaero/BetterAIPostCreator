-----------------------------------------
**S. No.** 1

**Improvement Idea**:
Implement the documented pipeline in `agents/essay_writer/agent.py` (or equivalent) so `EssayWriterPipeline`, `OutlineGenerator`, `WebResearcher`, and `EssayComposer` actually exist as ADK agents exporting `root_agent`.

**Reason why**:
Topic “Objective & Scope Fit” (Finding 1) states the entire hierarchy only lives in documentation with no ADK code, so nothing can satisfy the stated 3-step scope until a concrete module wires the SequentialAgent and sub-agents.

**Additional Note, if any**
Reuse `google.adk.agents.SequentialAgent` and `LlmAgent` plus the standard package layout (`agents/<agent>/agent.py`, `root_agent`) so the architecture matches AGENTS.md deployment rules.

-----------------------------------------
**S. No.** 2

**Improvement Idea**:
Define measurable success criteria and back them with ADK eval/test artifacts (e.g., pytest cases plus `adk eval` sets) that trace from objectives to outputs.

**Reason why**:
Objective & Scope Fit Finding 2 and “Evaluation Hooks & Testability” findings highlight the absence of eval/test connections, so codifying criteria (outline completeness, citation accuracy, tone adherence) and automating them is required to validate outcomes.

**Additional Note, if any**
Leverage existing ADK evaluation scaffolding and add regression suites under `tests/unittests/` so CI can run `pytest` and `adk eval` with documented acceptance thresholds.

-----------------------------------------
**S. No.** 3

**Improvement Idea**:
Split the current WebResearcher responsibilities into dedicated agents (e.g., `OutlineSearcher`, `EvidenceExtractor`, `CitationNormalizer`) orchestrated by the pipeline so each task stays minimal and coherent.

**Reason why**:
Topic “Task Decomposition Quality” Finding 1 and “Specialized vs. Monolithic Design” Finding 2 note that WebResearcher and EssayComposer absorb multiple unrelated duties, so decomposing them removes the over-broad sub-tasks.

**Additional Note, if any**
Reuse ADK’s `AgentTool` to expose specialized agents as tools to the coordinator instead of inventing new abstractions.

-----------------------------------------
**S. No.** 4

**Improvement Idea**:
Introduce a generator–critic stage (e.g., `FactCheckerAgent`) that reads `draft_essay` + `sources`, enforces pass/fail rules, and can trigger a repair cycle or human escalation before publication.

**Reason why**:
“Generator–Critic” findings 1–2 and “Task Decomposition Quality” Finding 2 report no reviewer/fact-check layer, so adding one prevents hallucinations and fills the missing QA sub-task.

**Additional Note, if any**
Wrap the critic as `AgentTool(FactCheckerAgent)` so EssayWriterPipeline can gate final emission without abandoning the existing SequentialAgent structure.

-----------------------------------------
**S. No.** 5

**Improvement Idea**:
Add an explicit human-in-the-loop checkpoint (approval of outline or final essay) with timeout/resume logic captured in session state.

**Reason why**:
Topic “Human-in-the-loop checkpoints” shows zero human touchpoints or resume handling, so critical content can ship without review and the system cannot recover from pending approvals.

**Additional Note, if any**
Use ADK session state keys such as `human_approval_status`, and gate transitions via callbacks or a lightweight `WaitForHumanTool` rather than inventing bespoke plumbing.

-----------------------------------------
**S. No.** 6

**Improvement Idea**:
Document and version concrete agent instructions/prompts (with negative scope, tool usage rules, style constraints) and pin them to files consumed by each `LlmAgent`.

**Reason why**:
Findings under “Agent Role Clarity” and “Prompt & Policy Design” confirm there are no instruction strings, few-shots, or safety clauses, so ADK cannot enforce behavior boundaries without these prompts.

**Additional Note, if any**
Store prompts under `agents/essay_writer/prompts/` (or similar) and load them via existing ADK prompt helpers to avoid duplicating framework code.

-----------------------------------------
**S. No.** 7

**Improvement Idea**:
Harden tool usage by defining MCP tool wrappers with parameter validation, domain allowlists, credential loading from `.env`, and per-call rate budgets.

**Reason why**:
“Tooling Fit,” “Security & Access Control,” and “Resource & Rate Management” findings all note undefined secrets, open-ended queries, and missing limits for `web_search`/`url_reader`, so the tools violate least privilege today.

**Additional Note, if any**
Reuse ADK’s MCP tool interfaces and `ToolContext` validation hooks to enforce query caps and to source credentials from environment variables rather than code.

-----------------------------------------
**S. No.** 8

**Improvement Idea**:
Define typed schemas (Pydantic/dataclasses) for `topic`, `outline`, `sources`, and `draft_essay`, and enforce read/write ownership rules when agents touch session state.

**Reason why**:
“Shared State & Data Passing” and “Data Contracts & Schemas” findings highlight informal YAML with no provenance or immutability rules, so schema enforcement is needed to avoid corrupt handoffs.

**Additional Note, if any**
Leverage ADK’s state services plus Pydantic models referenced in documentation so serialization/validation happens automatically before storing to `session.state`.

-----------------------------------------
**S. No.** 9

**Improvement Idea**:
Add an iterative refinement loop (LoopAgent or explicit retries) that re-runs outline, research, or composition when critic/human feedback flags gaps, with `max_iterations` and stop criteria persisted in state.

**Reason why**:
Topic “Iterative refinement/loops” Finding 1–2 explains that no LoopAgent, counters, or stop conditions exist, so quality issues cannot trigger controlled retries.

**Additional Note, if any**
Adopt ADK’s `LoopAgent` to wrap OutlineGenerator/WebResearcher/Evaluate steps, persisting `iteration_count` and `repair_actions` keys exactly as the evaluation expects.

-----------------------------------------
**S. No.** 10

**Improvement Idea**:
Parallelize independent research tasks (e.g., per-outline heading) via `ParallelAgent` or async tools, cache prior results, and pair this with structured observability (callbacks that emit correlation IDs, cost metrics, RunConfig budgets).

**Reason why**:
“Parallel fan-out/gather,” “Performance Engineering,” “Cost Controls,” and “Observability & Tracing” findings collectively show no parallelism, caching, telemetry, or budget enforcement, so latency, spend, and debugging remain unmanaged.

**Additional Note, if any**
Reuse ADK’s ParallelAgent plus RunConfig (`max_llm_calls`, `max_cost_usd`) and logging callbacks so performance, cost, and tracing improve without inventing new infrastructure.

