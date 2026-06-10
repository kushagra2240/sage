# I Built a Research Agent Pipeline with MCP and Four Specialized Agents (Here's What Actually Worked)

*Why separating plan → gather → analyze → write beats one mega-prompt—and how a custom MCP server fits in.*

---

If you ask a single LLM to "research this topic on the web and write me a cited report," you usually get one of two outcomes: a fluent essay with shaky citations, or a tool-calling loop that is hard to debug when step three fails. I wanted something more boring—in a good way. A pipeline where each stage has one job, tools live behind a standard protocol, and I can tell you exactly which agent broke when something goes wrong.

That experiment became **Sage**, an open-source Python project: a multi-agent research assistant that takes a question and returns a structured markdown report. It combines a **custom MCP (Model Context Protocol) server**, a **four-agent sequential pipeline**, and **swappable LLM providers** (Anthropic or OpenAI-compatible APIs such as OpenRouter and Ollama).

**GitHub:** https://github.com/kushagra-2240/sage  
*(Replace with your public repo URL before publishing.)*

---

## The problem with one mega-prompt

Research is not one cognitive task. It is:

1. **Planning** — What should we search for, in what order?
2. **Gathering** — Hit the web, pull real pages, store raw notes.
3. **Synthesizing** — Compare sources, find themes and contradictions.
4. **Writing** — Format for a reader, with sections and a summary.

When you collapse all of that into a single system prompt, failures become opaque. Did the model hallucinate a source? Skip a search? Confuse analysis with prose? You cannot tell.

Sage's design rule is simple: **one agent, one responsibility, one handoff.**

---

## What is MCP, and why should you care?

The **Model Context Protocol (MCP)** is an open standard for connecting AI applications to external capabilities—tools, data sources, and prompts—through a consistent interface. Anthropic introduced it; the ecosystem has since grown to include many hosts and servers.

The useful mental model is not "yet another API wrapper." It is **separation of concerns**:

- **Host** — The application that runs the agent loop (Claude Desktop, an IDE, or your own Python script).
- **Server** — A process that exposes **tools** the model can invoke (`web_search`, `read_file`, `query_database`, etc.).

Communication often happens over **stdio** (subprocess with JSON-RPC messages) or HTTP. For local development, stdio is common: your agent spawns a server, talks to it, and tears it down when done.

Official spec and docs: [modelcontextprotocol.io](https://modelcontextprotocol.io/)

Most tutorials show you how to *consume* existing MCP servers. I learned more by **authoring** one—a FastMCP server called `sage-tools` with three tools I actually needed.

---

## Multi-agent systems: pipeline, not swarm

"Multi-agent" is overloaded. It can mean:

- **Autonomous agents** negotiating in a loop until done (exciting, hard to debug).
- **Orchestrated pipelines** where a coordinator runs stages in order (less glamorous, predictable).

Sage is explicitly the second. Four roles:

| Agent | Job | Does *not* do |
|-------|-----|----------------|
| **Orchestrator** | Produce a 3–5 step research plan | Web search, final report |
| **Researcher** | Execute plan via MCP tools | Thematic analysis, polished writing |
| **Analyst** | Synthesize findings across sources | New searches |
| **Writer** | Markdown report with summary and sections | New research |

The Orchestrator never calls Tavily. The Researcher never writes the final report. Boundaries are enforced in code *and* in system prompts stored as versioned constants in `skills/prompts.py`.

This is the same pattern discussed in production-oriented agent guides—specialists with narrow prompts outperform generalists on complex workflows. See Anthropic's [Building effective agents](https://www.anthropic.com/research/building-effective-agents) for a pragmatic take.

---

## Architecture: from CLI to report

```
You: python main.py --query "..." --output report.md
         │
         ▼
   Orchestrator ──► LLM plans 3-5 search steps
         │
         ▼
   Researcher ──stdio MCP──► sage-tools server
         │                    ├── web_search (Tavily)
         │                    ├── extract_content (HTTP + BeautifulSoup)
         │                    └── save_note (in-memory store)
         ▼
   Analyst ──► LLM synthesizes themes and gaps
         ▼
   Writer ──► LLM produces markdown report
         ▼
   report.md
```

**Data flow matters:** Only the Researcher touches MCP. The Analyst and Writer see text produced upstream—classic **retrieval-augmented** behavior without a vector database: search and extract at runtime, then reason over compiled context.

---

## Building the MCP server with FastMCP

The server lives in `mcp_server/server.py` and registers three tools with FastMCP:

```python
from fastmcp import FastMCP

mcp = FastMCP("sage-tools")

@mcp.tool
def web_search(query: str, max_results: int = 5) -> list[dict[str, Any]]:
    # Returns [{"title", "url", "snippet"}, ...] via Tavily
    ...
```

**`web_search`** wraps the Tavily API—search results tuned for LLM consumption. **`extract_content`** fetches a URL with httpx and pulls main text with BeautifulSoup (preferring `<article>` or `<main>`). **`save_note`** stores step summaries in an in-memory dict so each research step leaves a paper trail.

FastMCP handles schema generation and protocol plumbing so you focus on tool logic. Docs: [gofastmcp.com](https://gofastmcp.com/)

### War story: `Connection closed` on Windows

My first integration test failed at MCP handshake with `McpError: Connection closed`. The subprocess was exiting immediately.

Root cause: launching the server as `python mcp_server/server.py` broke package imports (`ModuleNotFoundError: No module named 'mcp_server'`). Worse, a bad `__main__` guard once called `SystemExit` instead of starting the server—so the client saw a dead process.

**Fix:** Run the server as a module from the project root:

```bash
python -m mcp_server
```

The Researcher client spawns exactly that, with `cwd` set to the repo root and environment variables passed through so `TAVILY_API_KEY` reaches the child process:

```python
return StdioServerParameters(
    command=sys.executable,
    args=["-m", "mcp_server"],
    env=server_env,
    cwd=str(PROJECT_ROOT),
)
```

If you build MCP clients, treat **how you spawn the server** as part of your API design—not an afterthought.

---

## Planning: tool use vs JSON

The Orchestrator must return a **machine-readable plan** before any web access.

**Anthropic path:** Force a tool call to `submit_research_plan` with JSON Schema describing 3–5 steps (`step`, `search_query`, `goal`). Claude's tool-use API makes this reliable.

**OpenAI-compatible path** (OpenRouter, Together, Groq, Ollama): Ask for JSON only and parse `{"steps": [...]}`, with strict validation afterward. Open-weight models may need 70B-class capacity for consistent plans; smaller models sometimes skip steps or emit invalid JSON.

I run OpenRouter with `meta-llama/llama-3.3-70b-instruct` in production experiments; the full pipeline completed and wrote a real `report.md`. Provider switching is env-driven:

```env
LLM_PROVIDER=openai
OPENAI_BASE_URL=https://openrouter.ai/api/v1
OPENAI_MODEL=meta-llama/llama-3.3-70b-instruct
```

The `llm/` package abstracts both paths behind `get_provider()` so agent code stays provider-agnostic.

---

## Prompts as "skills"

Each agent gets a ~150-word system prompt defining role and **hard constraints**. For example, the Researcher is told to gather evidence, not analyze themes or write the final report. The Writer must use provided material and not invent new searches.

Treating prompts as first-class files (`skills/prompts.py`)—not string literals scattered across modules—made iteration safer. When the Writer started sounding like the Analyst, I knew which file to edit.

---

## Running it yourself

```bash
git clone https://github.com/kushagra-2240/sage.git
cd sage
python -m venv .venv
# activate venv
pip install -r requirements.txt
cp .env.example .env
# Add TAVILY_API_KEY + your LLM provider keys
python main.py --query "What are the tradeoffs in multi-agent AI design?" --output report.md
```

Progress prints to stderr in four stages. The first successful run takes a few minutes—multiple searches, extractions, and two long LLM calls add up.

Tests use `pytest` with mocked APIs so CI does not burn tokens.

---

## What worked, what didn't, what's next

**Worked:**

- Clear stage boundaries made debugging possible (planning vs MCP vs analysis).
- MCP let me add tools without rewriting agent logic.
- Provider abstraction let me ship with OpenRouter when I did not have an Anthropic key handy.

**Didn't (yet):**

- Citation quality still depends on search/extraction luck; no verification pass.
- No **re-planning** after research—if step 2 finds nothing useful, the pipeline does not adapt.
- Notes are in-memory only; restart loses state.
- Five-step plans on smaller open models can be flaky.

**Next steps I'd consider:** persistent note store (SQLite), a critic agent for citation checking, streaming output, and optional human approval between stages.

---

## Why this matters for your work

If you are exploring MCP or agent design for real systems—not slide decks—building a small server plus a strict pipeline teaches more than importing a dozen tools you never read.

You learn:

- How subprocess stdio MCP actually behaves.
- Where to draw agent boundaries so teams can own stages.
- When to use tool-use vs structured JSON for planning.

Sage is a learning project, not a production platform. But the patterns map to larger systems: specialized workers, tool protocols, and orchestration you can explain in an interview or a design review without hand-waving.

---

## Try it and tell me what you'd add

Clone the repo, run a query that matters to you, and open an issue or comment with one tool you would add to `sage-tools`—`arxiv_search`, `pdf_extract`, `slack_post`, anything.

If you publish your own MCP server or pipeline, link it. The protocol gets better when we share boring, working examples—not just announcements.

**Repo:** https://github.com/kushagra-2240/sage  
**MCP spec:** https://modelcontextprotocol.io/  
**FastMCP:** https://gofastmcp.com/

---

*If this helped, follow for more hands-on agent engineering posts—or connect on LinkedIn and tell me what you're building with MCP.*
