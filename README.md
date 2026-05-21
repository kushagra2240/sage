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
│  Claude claude-sonnet-4-6 + tool_use        │
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
│   └── tools/
│       ├── web_search.py       # Tavily API wrapper
│       ├── content_extractor.py # URL → clean text
│       └── document_store.py   # In-memory note storage
├── agents/
│   ├── orchestrator.py    # Plans and delegates research steps
│   ├── researcher.py      # Uses MCP tools to gather information
│   ├── analyst.py         # Synthesizes findings across sources
│   └── writer.py          # Produces the final markdown report
├── skills/
│   └── prompts.py         # System prompt constants for each agent role
├── tests/
│   ├── test_mcp_server.py
│   ├── test_researcher.py
│   └── test_orchestrator.py
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
git clone https://github.com/YOUR_USERNAME/sage.git
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
# Edit .env and add your keys:
# ANTHROPIC_API_KEY=sk-ant-...
# TAVILY_API_KEY=tvly-...
```

Get a free Tavily API key at [tavily.com](https://tavily.com) — the free tier is enough for this project.

---

## Usage

```bash
# Basic research query
python main.py --query "What are the key design patterns for multi-agent AI systems?"

# Save report to a file
python main.py --query "How does RAG work?" --output report.md
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

**Tool use with the Anthropic SDK** — The researcher agent uses Claude's native tool_use feature to decide *when* and *how* to call MCP tools, rather than hardcoding a fixed search-then-summarize flow.

**Agent skills as prompt templates** — System prompts are treated as first-class code in `skills/prompts.py`, versioned alongside the logic they govern.

---

## Roadmap

- [ ] Streaming output support
- [ ] Persistent document store (SQLite)
- [ ] Web UI with Gradio
- [ ] Support for PDF sources
- [ ] Multi-model support (swap Claude for other providers)

---

## Tech Stack

| Tool | Purpose |
|------|---------|
| [Anthropic Python SDK](https://github.com/anthropic/anthropic-sdk-python) | Claude API + tool use |
| [FastMCP](https://github.com/jlowin/fastmcp) | MCP server framework |
| [Tavily](https://tavily.com) | Web search API |
| [pytest](https://pytest.org) | Testing |
| [python-dotenv](https://github.com/theskumar/python-dotenv) | Env variable management |

---

## License

MIT