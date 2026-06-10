# One Agent, One Job: Why My Research Pipeline Has Four Agents Instead of One Mega-Prompt

*Part 2 of 3 in the "Agents in Practice" series. Part 1 covered building the MCP server; this part covers the agents that consume it.*

---

Ask a single LLM to "research this topic on the web and write me a cited report" and you usually get one of two outcomes: a fluent essay with shaky citations, or a tool-calling loop that's impossible to debug when step three fails.

I wanted something more boring — in a good way. A pipeline where each stage has one job, tools live behind a standard protocol, and when something breaks I can tell you *which agent* broke. That experiment became **Sage**, an open-source research assistant: question in, structured cited markdown report out.

**Repo:** https://github.com/kushagra-2240/sage

## Pipeline, not swarm

"Multi-agent" is an overloaded term. It can mean autonomous agents negotiating in a loop until done (exciting, hard to debug), or an orchestrated pipeline where a coordinator runs stages in order (less glamorous, predictable). Sage is deliberately the second — the same conclusion Anthropic reaches in [Building effective agents](https://www.anthropic.com/research/building-effective-agents): use the simplest pattern that works, and for most workflows that's a workflow, not a swarm.

Four roles, strict boundaries:

| Agent | Job | Explicitly does *not* do |
|-------|-----|--------------------------|
| **Orchestrator** | Produce a 3–5 step research plan | Web search, final report |
| **Researcher** | Execute the plan via MCP tools | Thematic analysis, polished writing |
| **Analyst** | Synthesize findings across sources | New searches |
| **Writer** | Markdown report with summary and citations | New research |

The Orchestrator never calls the search API. The Researcher never writes prose for a reader. The Writer never invents a source. Each boundary is enforced twice — in code (an agent literally has no access to tools outside its stage) and in its system prompt.

```
User query
    ▼
Orchestrator ──► LLM plans 3–5 search steps (structured output)
    ▼
Researcher ──stdio MCP──► sage-tools server
    │                      ├── web_search (Tavily)
    │                      ├── extract_content (httpx + BeautifulSoup)
    │                      └── save_note (per-step paper trail)
    ▼
Analyst ──► LLM synthesizes themes, conflicts, gaps
    ▼
Writer ──► LLM produces the final markdown report
```

Note what this data flow gives you for free: **only the Researcher touches the network.** The Analyst and Writer reason over text compiled upstream — retrieval-augmented generation without a vector database. Search and extract at runtime, then synthesize.

## The plan is a contract, not a vibe

The pipeline's reliability hinges on one thing: the Orchestrator's plan must be machine-readable *before* any web access happens. Sage forces the model to emit structured steps (more on how in Part 3), then validates them ruthlessly:

```python
def validate_plan(plan: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Ensure the orchestrator plan has 3-5 steps with required fields."""
    if len(plan) < MIN_PLAN_STEPS or len(plan) > MAX_PLAN_STEPS:
        raise ValueError("plan must have between 3 and 5 steps")

    validated = []
    for item in plan:
        query = (item.get("search_query") or item.get("query") or "").strip()
        if not query:
            raise ValueError("each plan step must include a search_query")
        validated.append({
            "step": item.get("step", len(validated) + 1),
            "search_query": query,
            "goal": (item.get("goal") or item.get("rationale") or "").strip(),
        })
    return validated
```

Two details worth stealing. First, the validator **tolerates near-miss field names** (`query` for `search_query`, `rationale` for `goal`) — models drift, especially smaller ones, and a cheap alias check saves a re-roll. Second, it **fails loudly on what matters**: no query, no step. A plan that passes validation is a contract the Researcher can execute mechanically.

## The Researcher: a deterministic tool loop

Here's a design decision that surprises people: **the Researcher contains no LLM call.** Once the plan exists, executing it — search, extract top URLs, save a note — is deterministic orchestration:

```python
async def _execute_step(self, session, step):
    search_results = await self._call_tool(
        session, "web_search",
        {"query": step["search_query"], "max_results": self.max_search_results},
    )

    extractions = []
    for result in search_results[: self.top_urls_per_search]:
        try:
            content = await self._call_tool(
                session, "extract_content", {"url": result["url"]}
            )
            extractions.append({"url": result["url"], "content": str(content)})
        except RuntimeError:
            # Extraction failed (paywall, 404, JS-only page):
            # degrade to the search snippet instead of dying.
            extractions.append({"url": result["url"], "content": result.get("snippet", "")})

    note_key = f"step-{step['step']}-{_slugify(step['search_query'])}"
    await self._call_tool(session, "save_note", {"key": note_key, "content": note_body})
```

Every LLM call you remove from a pipeline is a failure mode you remove. The intelligence lives at the edges — planning before, synthesis after. The middle is plumbing, and plumbing should be boring. The `try/except` around extraction is the single most valuable line in the file: real web pages fail constantly, and degrading to the search snippet keeps one dead URL from killing a four-minute run.

## Prompts as versioned code

Each agent's system prompt is a ~150-word constant in `skills/prompts.py` — not a string literal buried in application logic. Each prompt states the role, the deliverable, and crucially the **negative space**:

> *"You are the Analyst… Do not conduct new web searches, invent citations, or write for a public audience yet; the Writer handles presentation."*

When the Writer started sounding like the Analyst — analytical hedging instead of reader-facing prose — I knew exactly which file to open and could diff the fix in git. Treating prompts as first-class, versioned artifacts is the cheapest engineering discipline you can add to an agent project.

## What separation bought me (and what it cost)

**Worked:**

- **Debuggability.** Bad report? Read the plan, the notes, and the analysis independently. The failing stage identifies itself.
- **Composability.** Adding an MCP tool doesn't touch agent logic; changing the Writer's voice doesn't risk the Researcher.
- **Testability.** Each stage mocks cleanly — pytest runs the whole suite without an API key.

**Didn't (yet):**

- **No re-planning.** If step 2 finds nothing useful, the pipeline doesn't adapt — a strict pipeline trades adaptivity for predictability.
- **Notes are write-only.** The Analyst reads compiled context, not the note store; persistent notes (SQLite) would enable cross-run memory.
- **No critic.** Citation quality depends on extraction luck; a verification agent is the obvious fifth role.

These are honest costs. For a research task, predictability won. For a task needing mid-course correction, you'd add a feedback edge from Researcher back to Orchestrator — and that one edge, not a framework, is what people usually mean by "agentic."

---

**Part 3** covers the layer that makes all of this run on Claude *or* any OpenAI-compatible model (OpenRouter, Groq, Ollama) with one env var — including why "force a tool call" and "ask for JSON" are the same idea wearing different APIs.

*What's the fifth agent you'd add? Open an issue on the repo — I read all of them.*

**Repo:** https://github.com/kushagra-2240/sage
