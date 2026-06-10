# Sage 🌿
### A Multi-Agent Research Assistant powered by Claude + MCP

Sage is an agentic research pipeline that takes a question and returns a structured, cited report. It demonstrates multi-agent orchestration, custom MCP (Model Context Protocol) server authorship, and tool-use patterns with the Anthropic Python SDK.

> Built as a learning project to explore MCP, agent design, and the Claude API.

---

## What is MCP?

MCP (Model Context Protocol) is an open standard by Anthropic — like a USB port for AI. It lets any compatible model connect to external tools (web search, file systems, APIs) through a standardized interface. In this project, we build our own MCP server from scratch that exposes tools Claude can call.

---

## Architecture

```
User query
    │
    ▼
┌─────────────────────────────────────┐
│         Orchestrator Agent          │
│  Plans research strategy using      │
│  Claude (tool_use) or JSON planning │
└──────┬──────────────┬───────────────┘
       │              │              │
       ▼              ▼              ▼
┌──────────┐  ┌──────────────┐  ┌──────────┐
│Researcher│  │   Analyst    │  │  Writer  │
│ Searches │  │ Synthesizes  │  │ Formats  │
│& extracts│  │  findings &  │  │  report  │
│ content  │  │key takeaways │  │    📄    │
└────┬─────┘  └──────────────┘  └──────────┘
     │
     ▼
┌─────────────────────────────────────┐
│         Custom MCP Server           │
│  ┌────────────┐  ┌───────────────┐  │
│  │ web_search │  │extract_content│  │
│  └────────────┘  └───────────────┘  │
│  ┌────────────┐                     │
│  │ save_note  │                     │
│  └────────────┘                     │
└─────────────────────────────────────┘
```

---

## Project Structure

```
sage/
├── mcp_server/
│   ├── server.py          # FastMCP server — exposes tools to Claude
│   ├── __main__.py        # Enables `python -m mcp_server`
│   └── tools/
│       ├── search.py      # Tavily API wrapper
│       ├── content.py     # URL → clean text (httpx + BeautifulSoup)
│       └── notes.py       # In-memory note storage
├── agents/
│   ├── orchestrator.py    # Plans and delegates research steps
│   ├── researcher.py      # Uses MCP tools to gather information
│   ├── analyst.py         # Synthesizes findings across sources
│   ├── writer.py          # Produces the final markdown report
│   └── mcp_client.py      # stdio client helpers for sage-tools
├── llm/                   # Provider abstraction (anthropic / openai-compatible)
│   ├── anthropic_provider.py
│   ├── openai_provider.py
│   ├── factory.py
│   └── planning.py        # Plan tool schema + JSON parsing
├── skills/
│   └── prompts.py         # System prompt constants for each agent role
├── plan_schema.py         # Shared plan validation (no agents↔llm dependency)
├── tests/                 # pytest suite (APIs mocked — no tokens burned)
├── main.py                # CLI entry point
├── config.py              # Environment variable loading
├── .env.example
├── requirements.txt
└── README.md
```

---

## Setup

**1. Clone the repo**
```bash
git clone https://github.com/kushagra-2240/sage.git
cd sage
```

**2. Create a virtual environment**
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Set up environment variables**
```bash
cp .env.example .env
```

**Anthropic (default)** — set `LLM_PROVIDER=anthropic`, `ANTHROPIC_API_KEY`, and `TAVILY_API_KEY`.

**Open-source / OpenAI-compatible** — set `LLM_PROVIDER=openai`, `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `OPENAI_MODEL`, and `TAVILY_API_KEY`. Works with [OpenRouter](https://openrouter.ai), Together, Groq, or local [Ollama](https://ollama.com).

Get a free Tavily API key at [tavily.com](https://tavily.com) — the free tier is enough for this project.

See [WORKFLOW_README.md](WORKFLOW_README.md) for OpenRouter and Ollama example `.env` blocks.

---

## Usage

```bash
# Anthropic (default from .env)
python main.py --query "What are the key design patterns for multi-agent AI systems?"

# Save report to a file
python main.py --query "How does RAG work?" --output report.md

# OpenRouter or Ollama (open-weight models)
python main.py --query "How does RAG work?" --provider openai --model meta-llama/llama-3.3-70b-instruct --output report.md
```

---

## Running Tests

```bash
pytest tests/ -v
```

---

## Key Concepts Demonstrated

**MCP Server authorship** — Most tutorials only show how to *use* existing MCP servers. This project builds one from scratch using FastMCP, exposing three tools with proper error handling and type annotations.

**Multi-agent orchestration** — The orchestrator delegates to specialized agents rather than one monolithic prompt. Each agent has a focused role and system prompt, which improves output quality and makes the system easier to debug.

**Modular LLM providers** — Swap Anthropic (native `tool_use` for planning) or any OpenAI-compatible API (JSON planning) via `LLM_PROVIDER` without changing the Researcher/MCP layer.

**Tool use with the Anthropic SDK** — The orchestrator uses Claude's native `tool_use` to emit a structured research plan when `LLM_PROVIDER=anthropic`.

**Agent skills as prompt templates** — System prompts are treated as first-class code in `skills/prompts.py`, versioned alongside the logic they govern.

---

## Roadmap

- [ ] Streaming output support
- [ ] Persistent document store (SQLite)
- [ ] Web UI with Gradio
- [ ] Support for PDF sources
- [x] Multi-model support (Anthropic + OpenAI-compatible providers)

---

## Tech Stack

| Tool | Purpose |
|------|---------|
| [Anthropic Python SDK](https://github.com/anthropics/anthropic-sdk-python) | Claude API + tool use (default) |
| [OpenAI Python SDK](https://github.com/openai/openai-python) | OpenRouter, Together, Groq, Ollama |
| [FastMCP](https://github.com/jlowin/fastmcp) | MCP server framework |
| [Tavily](https://tavily.com) | Web search API |
| [pytest](https://pytest.org) | Testing |
| [python-dotenv](https://github.com/theskumar/python-dotenv) | Env variable management |

---

## Blog — "Agents in Practice" series

Write-ups on how Sage works, with code. Links added as each part is published:

1. **Building an MCP server from scratch** — FastMCP, stdio transport, and the `Connection closed` war story *(coming soon)*

---

## License

MIT