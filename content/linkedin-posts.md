# LinkedIn posts — Sage launch campaign

Replace `YOUR_USERNAME`, Medium URL, and LinkedIn article URL before posting.

---

## Post 1 — Launch day (Day 0)

**Format:** Text post + link preview (Medium) + comment with GitHub link

---

I kept seeing "multi-agent" demos that were one prompt wearing four hats.

So I built something more debuggable: **Sage** — a Python research pipeline with:

→ An **Orchestrator** that plans 3–5 web search steps  
→ A **Researcher** that calls tools through a **custom MCP server** (search, extract, notes)  
→ An **Analyst** + **Writer** that never touch the web directly  

The Model Context Protocol (MCP) finally clicked when I **authored** the server, not only plugged into someone else's.

War story: my MCP client kept failing with "Connection closed." The fix was spawning the server as `python -m mcp_server` from the project root — not `python mcp_server/server.py`. Subprocess details matter.

I wrote up the full architecture, code, and failures on Medium (link in comments).

**Try the repo:** https://github.com/kushagra-2240/sage

If you are building agents: what is the first tool you would add to an MCP server?

#MCP #AIAgents #LLM #Python #OpenSource #GenerativeAI

**First comment (post immediately):**  
Medium article: [PASTE MEDIUM URL]  
`.env.example` in the repo — works with OpenRouter/Ollama or Anthropic.

---

## Post 2 — Insight post (Day 2–3)

**Format:** Text only (no link required — drives profile visits)

---

Best debugging win on my agent project was not a smarter model.

It was a boundary:

**The Orchestrator never calls Tavily.**

Only the **Researcher** does — through an MCP server (`web_search`, `extract_content`, `save_note`).

When search failed, I knew exactly which layer to inspect. No more "the pipeline feels wrong."

That is the difference between a demo and a system you can explain in a design review.

Multi-agent hype vs multi-agent **pipelines** — I am firmly on the pipeline side for v1.

Building in public: https://github.com/kushagra-2240/sage

#MCP #AIAgents #SoftwareEngineering #LLM

---

## Post 3 — Results post (Day 7)

**Format:** Text + optional screenshot of report.md excerpt (blur any sensitive paths)

---

Ran my MCP + multi-agent pipeline on a real question:

*"What are the tradeoffs in multi-agent AI design?"*

Four stages, ~few minutes, output: a structured markdown report with sections and citations.

Stack:
- **MCP** (custom FastMCP server)
- **4 agents** (plan → research → analyze → write)
- **OpenRouter + Llama 3.3** for LLM calls (Anthropic path also supported)

Not production-ready — but **runnable and open source**.

Clone: https://github.com/kushagra-2240/sage  
Deep dive: [PASTE MEDIUM URL]

What research question would you throw at it?

#MCP #AIAgents #LLM #Python #BuildInPublic

---

## Optional short post — LinkedIn article promo

Published a shorter version on LinkedIn Articles too — same repo, less code, more "what I learned."

Link: [PASTE LINKEDIN ARTICLE URL]
