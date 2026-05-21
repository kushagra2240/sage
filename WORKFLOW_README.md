# Sage Workflow Guide

This document explains how the Sage multi-agent research assistant fits together end to end—from your CLI command through MCP tools to the final markdown report.

---

## Architecture

Sage uses a **sequential multi-agent pipeline**. Each agent has a narrow job; the Orchestrator coordinates handoffs so no single prompt tries to do everything at once.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              YOU (CLI)                                  │
│                    python main.py --query "..." -o report.md            │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         main.py (entry point)                           │
│              validate config → Orchestrator → save report               │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
          ┌───────────────────────┼───────────────────────┐
          │                       │                       │
          ▼                       ▼                       ▼
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│  [1] ORCHESTRATOR│   │  skills/prompts  │   │     config.py    │
│  Claude + tool   │   │  system prompts  │   │  API keys (.env) │
│  use → 3–5 steps │   │  per agent role  │   │                  │
└────────┬─────────┘   └──────────────────┘   └──────────────────┘
         │ plan (search queries + goals)
         ▼
┌──────────────────┐         stdio (mcp Python SDK)
│  [2] RESEARCHER  │──────────────────────────────────────────────┐
│  For each step:  │                                              │
│  web_search      │                                              ▼
│  extract_content │                              ┌───────────────────────────┐
│  save_note       │                              │   MCP Server (sage-tools)   │
└────────┬─────────┘                              │   mcp_server/server.py    │
         │ raw notes + context                    │  ┌─────────┐ ┌───────────┐ │
         ▼                                        │  │web_search│ │extract_   │ │
┌──────────────────┐                              │  │ (Tavily) │ │content    │ │
│  [3] ANALYST     │                              │  └─────────┘ └───────────┘ │
│  Claude synthesize│                             │  ┌─────────┐               │
│  themes, gaps    │                              │  │save_note│               │
└────────┬─────────┘                              │  └─────────┘               │
         │ structured analysis                    └───────────────────────────┘
         ▼
┌──────────────────┐
│  [4] WRITER      │
│  Claude → markdown report (sections, citations, summary)
└────────┬─────────┘
         │
         ▼
    report.md  (or stdout)
```

**Data flow:** The Orchestrator never touches the web directly. The Researcher is the only agent that calls MCP tools. The Analyst and Writer only see text produced by earlier stages.

---

## What is MCP?

The **Model Context Protocol (MCP)** is an open standard for connecting AI applications to external tools and data through a consistent interface. In Sage, we run a local MCP server (`sage-tools`) that exposes web search, page extraction, and note storage so the Researcher agent can call them like structured functions instead of ad hoc API code.

---

## Multi-agent pattern

Sage follows a **specialist pipeline** rather than one monolithic assistant:

| Agent | Responsibility | Does *not* do |
|-------|----------------|---------------|
| **Orchestrator** | Break the question into 3–5 searchable steps | Search, analyze, or write |
| **Researcher** | Execute the plan via MCP (search → extract → note) | Thematic synthesis or final prose |
| **Analyst** | Compare sources, find themes and gaps | New searches or polished report |
| **Writer** | Markdown report with summary, sections, citations | New research or changing facts |

**Why this pattern?** Smaller prompts with clear boundaries reduce hallucination, make failures easier to localize (e.g. a bad search vs. a weak conclusion), and let you swap or upgrade one stage—such as the MCP tools—without rewriting the whole system.

The Orchestrator uses Claude **`tool_use`** to emit a structured plan (`submit_research_plan`). Downstream agents use plain text prompts with role-specific system strings from `skills/prompts.py`.

---

## Installation

**1. Clone and enter the project**

```bash
git clone https://github.com/YOUR_USERNAME/sage.git
cd sage
```

**2. Create a virtual environment**

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Configure API keys**

```bash
cp .env.example .env
```

Edit `.env` and set:

- `ANTHROPIC_API_KEY` — from [console.anthropic.com](https://console.anthropic.com)
- `TAVILY_API_KEY` — from [tavily.com](https://tavily.com) (free tier is sufficient)

---

## Usage example

Run a full research pipeline and save the report:

```bash
python main.py --query "What are the main tradeoffs in multi-agent AI system design?" --output reports/multi-agent-tradeoffs.md
```

**Progress output** (stderr) looks like:

```
Starting Sage research pipeline for: 'What are the main tradeoffs...'

[1/4] Planning research strategy with Claude...
      Created 4-step plan.
      • Step 1: multi-agent AI architecture patterns
      ...
[2/4] Gathering information via MCP tools (search, extract, notes)...
      Completed 4 research steps.
[3/4] Analyzing findings across sources...
      Analysis complete (842 output tokens).
[4/4] Writing final report...
      Report complete (1203 output tokens).

Report saved to D:\projects\sage\reports\multi-agent-tradeoffs.md

Done.
```

Print the report to stdout instead of a file:

```bash
python main.py --query "How does retrieval-augmented generation work?"
```

Optional audience hint for the Writer:

```bash
python main.py --query "Explain MCP servers" --audience technical --output mcp-report.md
```

**Run tests:**

```bash
pytest tests/ -v
```

**Run the MCP server standalone** (for debugging tools):

```bash
python mcp_server/server.py
```

---

## Project layout (workflow-relevant)

```
sage/
├── main.py                 # CLI: --query, --output, staged progress
├── config.py               # Loads ANTHROPIC_API_KEY, TAVILY_API_KEY
├── agents/
│   ├── orchestrator.py     # Plans with Claude tool_use
│   ├── researcher.py       # MCP client → search / extract / notes
│   ├── analyst.py          # Synthesizes research context
│   └── writer.py           # Produces markdown report
├── mcp_server/
│   └── server.py           # FastMCP "sage-tools" server
├── skills/
│   └── prompts.py          # ~150-word system prompts per role
└── tests/                  # pytest + mocked APIs
```

---

## What I learned

- **Separate planning from execution.** Forcing the Orchestrator to output only a structured plan via `tool_use` keeps search queries focused and prevents the model from “answering” the user question before any evidence is collected.

- **MCP as a tool boundary.** Wrapping Tavily, HTTP fetch, and note storage behind MCP tools means the Researcher talks to one interface; you can change backends or add tools without touching agent logic.

- **Specialist agents beat one mega-prompt.** Research, analysis, and writing use different cognitive tasks; giving each its own system prompt and constraints improved debuggability and made it obvious which stage failed when something went wrong.

- **stdio MCP fits local workflows.** Spawning the `sage-tools` server as a subprocess per research run is simple and testable; the tradeoff is no shared long-lived server, which is acceptable for a CLI research tool.

---

## See also

- [README.md](README.md) — project overview and tech stack
- [.env.example](.env.example) — required environment variables
