# MCP + Multi-Agent Pipelines: A Small Python Project That Ties Them Together

I spent the last few weeks going deep on two topics everyone talks about but few people ship together: **the Model Context Protocol (MCP)** and **multi-agent LLM systems**.

Not slides. Not a ChatGPT wrapper. A real Python repo called **Sage** that takes a research question and outputs a structured markdown report—using a custom MCP server and four agents with strict roles.

Here is what I built, what broke, and why I think this combination is worth your time if you care about agent engineering.

---

## Why I built this

Most MCP content I found was "how to connect Claude Desktop to an existing server." That is useful, but I wanted to understand the **server side**: schemas, stdio transport, subprocess lifecycle, error handling when the child process dies.

At the same time, "multi-agent" posts often describe autonomous swarms that sound impressive and fail mysteriously. I wanted a **pipeline I could debug**:

1. Plan the research (3–5 search steps).
2. Gather evidence via tools (search, extract, notes).
3. Analyze across sources.
4. Write the report.

If step 2 fails, I know the Researcher or MCP layer failed—not "the model felt creative today."

---

## Three ideas in one repo

### 1. Author an MCP server, do not only consume one

Sage exposes a FastMCP server named `sage-tools` with three tools:

- **web_search** — Tavily-backed search returning title, URL, snippet.
- **extract_content** — Fetch and parse page text (httpx + BeautifulSoup).
- **save_note** — Store per-step research notes in memory.

The Researcher agent is an MCP **client** (Python `mcp` SDK). It spawns the server with `python -m mcp_server` from the project root—lesson learned after `Connection closed` errors from bad import paths.

MCP spec: https://modelcontextprotocol.io/

### 2. Multi-agent means boundaries, not more chatbots

| Role | Responsibility |
|------|----------------|
| Orchestrator | Research plan only |
| Researcher | Tool execution only |
| Analyst | Synthesis only |
| Writer | Final report only |

Each role has a dedicated system prompt (~150 words) with explicit "do not" rules. The Orchestrator never hits the web. The Researcher never writes the final report.

That separation is the whole point. It is how you get explainable systems.

### 3. Provider abstraction (closed and open models)

Sage supports:

- **Anthropic** — planning via forced tool use (`submit_research_plan`).
- **OpenAI-compatible APIs** — OpenRouter, Ollama, etc., with JSON planning.

I ran a full successful pipeline on **OpenRouter + Llama 3.3 70B**—proof the architecture is not locked to one vendor.

---

## The pipeline in 60 seconds

```
Query → Orchestrator (plan)
      → Researcher (MCP: search, extract, note) × N steps
      → Analyst (synthesize)
      → Writer (markdown report)
```

You run:

```bash
python main.py --query "Your topic" --output report.md
```

Config via `.env` — see `.env.example` in the repo. Tavily is always required for search; LLM keys depend on your provider.

---

## What I would tell a hiring manager or teammate

I can now explain, without hand-waving:

- How an MCP server registers tools and speaks stdio.
- Why the Researcher—not the Orchestrator—calls Tavily.
- When to use tool-use vs JSON for structured planning.
- What fails when the MCP subprocess exits early (and how I fixed it).

That is different from "I built a chatbot." It is **systems thinking** around LLMs.

---

## Honest limitations

- Citations are not verified automatically.
- No adaptive re-plan if early searches are weak.
- Notes are in-memory (restart clears them).
- End-to-end runs take minutes and real API spend.

It is a learning project—but a credible one.

---

## Go deeper

I wrote a longer technical walkthrough on **Medium** with architecture detail, code snippets, and failure stories.

**Full article:** [ADD YOUR MEDIUM URL AFTER PUBLISHING]  
**Source code:** https://github.com/kushagra-2240/sage

Clone it, break it, open an issue with the tool you would add next (`pdf_extract`, `arxiv_search`, whatever).

---

## Let's connect

If you are building with MCP or agent pipelines, I want to hear what you are shipping—especially the boring parts that actually run.

Comment, connect, or share your repo. The best way to learn this space is to compare working systems, not buzzwords.

#MCP #AIAgents #LLM #Python #MachineLearning #OpenSource #GenerativeAI
