# Google ADK Agent Architecture — “Essay Writer (3-Step)”

## 🧭 Agent Hierarchy Overview

```
EssayWriterPipeline (SequentialAgent) ✅
├─ OutlineGenerator (LlmAgent) ✅
├─ WebResearcher (LlmAgent) ✅
└─ EssayComposer (LlmAgent) ✅
```

## 🧠 Root Agent

* **Agent Name:** `EssayWriterPipeline`
* **Type:** `SequentialAgent`
* **Purpose:** Orchestrates a 3-step workflow to (1) draft an outline for topic **X**, (2) perform targeted web research, and (3) compose a citation-aware essay.
* **Sub-agents:** `[OutlineGenerator, WebResearcher, EssayComposer]`
* **Tools:** none
* **Callbacks:** none
* **Session State:** **reads:** `[topic]`, **writes:** `[outline, sources, draft_essay]`
* **Model:** N/A (delegates to sub-agents)
* **Budget / Policy:** `{ max_iterations: inherited from sub-agents }`

## ⚙️ Sub-Agent Specifications

### OutlineGenerator

* **Agent Name:** `OutlineGenerator`
* **Type:** `LlmAgent`
* **Purpose:** Produce a clear, hierarchical outline (H1/H2/H3) and thesis statement for topic **X** with estimated word counts.
* **Sub-agents:** `[]`
* **Tools:** `[]`
* **Callbacks:** `[]`
* **Session State:** **reads:** `[topic]`, **writes:** `[outline]`
* **Model:** `gemini-2.0-flash`
* **Special Notes:** Enforces outline quality rules (logical flow, coverage, non-redundancy). Adds an “evidence needed” bullet under each major section to guide research.

### WebResearcher

* **Agent Name:** `WebResearcher`
* **Type:** `LlmAgent`
* **Purpose:** Execute focused web searches based on the outline’s “evidence needed,” extract key facts/quotes, and normalize citations.
* **Sub-agents:** `[]`
* **Tools:**

  * `web_search (McpToolset via @modelcontextprotocol/server-web)` — targeted queries using outline headings
  * `url_reader (McpToolset via @modelcontextprotocol/server-web)` — fetch & summarize pages into structured notes
* **Callbacks:**

  * `before_tool_callback`, `after_tool_callback` — trace search queries and captured notes
* **Session State:** **reads:** `[outline]`, **writes:** `[sources]`
* **Model:** `gemini-2.0-flash`
* **Special Notes:** Produces structured research notes: `{ heading, claim, evidence, quote?, url, author?, date?, reliability_score }`. Deduplicates URLs and flags low-credibility sources.

### EssayComposer

* **Agent Name:** `EssayComposer`
* **Type:** `LlmAgent`
* **Purpose:** Write a fluent essay aligned to the outline, weaving in research notes with in-text citations and a references section.
* **Sub-agents:** `[]`
* **Tools:** `[]`
* **Callbacks:** `before_model_callback`, `after_model_callback` — capture final token counts and safety filters
* **Session State:** **reads:** `[outline, sources]`, **writes:** `[draft_essay]`
* **Model:** `gemini-2.0-flash`
* **Special Notes:** Supports styles: academic, explanatory, persuasive. Enforces length bounds via prompt constraints and emits bibliography in chosen style (APA/MLA/Chicago) with available metadata.

## 🔗 Agent Connection Mapping

```
EssayWriterPipeline (SequentialAgent)
├─ OutlineGenerator (LlmAgent)
├─ WebResearcher (LlmAgent) — tools: web_search, url_reader; callbacks: before/after tool
└─ EssayComposer (LlmAgent) — callbacks: before/after model
```

## 🧱 Session State (Canonical Keys)

```yaml
topic: The essay subject provided by the user (string).
outline: Hierarchical outline with thesis and “evidence needed” prompts (markdown/json).
sources:
  - heading: Outline section the source supports
    claim: Specific claim being supported or challenged
    evidence: Short summary of the evidence
    quote: Optional exact quote
    url: Source URL
    author: Optional author/organization
    date: Optional publication date
    reliability_score: 0–1 confidence
draft_essay: Final composed essay text (markdown) with in-text citations and references.
```

## 🔄 Update Protocol & Consistency Checks

* Re-read the ADK documentation notes and this file before editing orchestration code.
* Confirm agent names, types, tools, callbacks, and session keys match constants in implementation modules.
* Validate that `WebResearcher` produces normalized `sources` entries used by `EssayComposer`.
* If adding plagiarism checks or citation formatting tools, update the **Tools** and **Session State** for affected agents.
* When changing essay style or citation style, version the prompt blocks and record in the repo CHANGELOG.

*Format & sectioning mirror the project’s prior ADK agent spec template.* 
