# One Env Var, Any Model: Making an Agent Pipeline Provider-Agnostic

*Part 3 of 3 in the "Agents in Practice" series. Parts 1–2 covered the MCP server and the four-agent pipeline; this part covers the layer that lets the same pipeline run on Claude, OpenRouter, Groq, or a local Ollama model.*

---

Halfway through building **Sage** (my open-source research pipeline), I hit a practical problem: I wanted Claude's native tool-use for planning, but I also wanted to run the pipeline on open-weight models via OpenRouter — partly for cost, partly because "works only with one vendor" is a design smell.

The result is a small provider abstraction that I now reuse in other projects. The interesting part isn't the abstraction itself — it's *where the seam goes*.

**Repo:** https://github.com/kushagra-2240/sage

## The hard part: structured output, two dialects

Most of an agent pipeline is provider-trivial: "system prompt + user message → text" looks the same everywhere. The hard part is the **Orchestrator's plan** — it must be machine-readable JSON, and the two API families get you there differently.

### Anthropic: force the tool call

Claude's tool-use API lets you define a tool whose input schema *is* your output schema, then **force** the model to call it:

```python
PLAN_TOOL = {
    "name": "submit_research_plan",
    "description": "Submit a structured research plan with 3-5 steps...",
    "input_schema": {
        "type": "object",
        "properties": {
            "steps": {
                "type": "array",
                "minItems": 3, "maxItems": 5,
                "items": {
                    "type": "object",
                    "properties": {
                        "step": {"type": "integer"},
                        "search_query": {"type": "string"},
                        "goal": {"type": "string"},
                    },
                    "required": ["step", "search_query", "goal"],
                },
            }
        },
        "required": ["steps"],
    },
}

message = client.messages.create(
    model=model,
    system=ORCHESTRATOR_PROMPT,
    messages=[{"role": "user", "content": user}],
    tools=[PLAN_TOOL],
    tool_choice={"type": "tool", "name": "submit_research_plan"},  # ← forced
)
```

`tool_choice` with a specific tool name means the model *cannot* reply with prose. You read the plan straight out of the `tool_use` block — no regex, no "please respond with only JSON" begging. The tool is fictional; nothing executes it. **Forced tool use is just structured output wearing a different API.** That reframing is the most useful thing I learned building this.

### OpenAI-compatible: ask for JSON, trust nothing

OpenRouter, Together, Groq, and Ollama speak the OpenAI chat-completions dialect. There you request JSON mode if available, fall back if the endpoint doesn't support it, and parse defensively:

```python
try:
    response = client.chat.completions.create(
        **kwargs, response_format={"type": "json_object"},
    )
except Exception:
    response = client.chat.completions.create(**kwargs)  # endpoint lacks JSON mode

return parse_plan_from_json(response.choices[0].message.content)
```

And `parse_plan_from_json` assumes the model has bad habits, because it does:

```python
def parse_plan_from_json(text: str) -> list[dict[str, Any]]:
    cleaned = text.strip()
    if cleaned.startswith("```"):                      # models love code fences
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)

    data = json.loads(cleaned)
    steps = data if isinstance(data, list) else data.get("steps", [])
    return validate_plan(steps)                        # same validator as Anthropic path
```

Code-fence stripping looks hacky and is non-negotiable: even strong open-weight models wrap JSON in markdown fences under JSON-adjacent prompting. Empirically, consistent 3–5 step plans need roughly 70B-class capacity — `meta-llama/llama-3.3-70b-instruct` via OpenRouter runs the full Sage pipeline end-to-end; smaller models skip steps or emit invalid JSON often enough to annoy.

## The seam: one validator, two transports

Here's the design point that matters more than either code snippet. Both paths converge on the **same `validate_plan()` function** before anything downstream sees the plan:

```
Anthropic tool_use  ──► extract block.input ──┐
                                              ├──► validate_plan() ──► Researcher
OpenAI JSON mode    ──► parse + strip fences ─┘
```

The Researcher, Analyst, and Writer (and the MCP layer from Part 1) have no idea which provider produced their input. Provider differences are quarantined in `llm/`; correctness is enforced at one chokepoint. If a third dialect shows up next year, it's a new file in `llm/`, not a refactor.

Switching is entirely env-driven:

```env
# Claude
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=...

# or any OpenAI-compatible endpoint
LLM_PROVIDER=openai
OPENAI_BASE_URL=https://openrouter.ai/api/v1
OPENAI_MODEL=meta-llama/llama-3.3-70b-instruct
```

```bash
python main.py --query "How does RAG work?" --provider openai --model llama3.3 -o report.md
```

## What I'd tell you before you build this

**Put the seam at structured output, not at "LLM call."** A generic `complete()` method is easy; the planning path is where providers genuinely differ. Abstract exactly that, nothing more.

**Validate after every provider, identically.** The validator is your real schema. JSON mode and forced tools both reduce — not eliminate — malformed output.

**Don't abstract preemptively.** Sage's two provider classes are ~150 lines of code combined. No plugin registry, no adapter metaclasses. The third provider can pay for the generalization when it arrives.

**Budget capability, not just price.** The cheap model that fails plan validation 20% of the time isn't cheap — you pay in retries and in downstream garbage. Match the model to the stage: Sage happily uses a big model for planning and could use a smaller one for note-taking stages.

## Series wrap-up

Three posts, one small system:

1. **MCP server** — tools behind a standard protocol, spawning as API design.
2. **Four-agent pipeline** — one agent, one job; intelligence at the edges, boring plumbing in the middle.
3. **Provider abstraction** — quarantine vendor differences, converge on one validator.

None of this needed a framework. The total system is a few hundred lines of readable Python, and every pattern here — tool protocols, staged orchestration, structured-output seams — maps directly onto the larger systems I build in client work. Small, working, explainable examples teach more than slide decks.

*Which provider quirk has bitten you hardest? Tell me in the comments — and if you run Sage on a model I haven't tried, open an issue with the results.*

**Repo:** https://github.com/kushagra-2240/sage · **MCP spec:** https://modelcontextprotocol.io/
