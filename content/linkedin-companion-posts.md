# LinkedIn Companion Posts (one per Medium article)

Post these natively on LinkedIn 1–2 days after each Medium article goes live, with the Medium link in the **first comment** (links in the post body get downranked). Best posting windows for EU reach: Tue–Thu, 8:00–10:00 CET.

---

## Post 1 — MCP server (week 1)

Most engineers I talk to have *used* an MCP server. Very few have *built* one.

I built one from scratch for Sage, my open-source research agent, and the lessons were not where I expected:

→ Your tool's docstring is a prompt. The model decides how to call your tool based on it — vague docstring, vague tool calls.

→ How you spawn the server is part of your API. My first integration test died with a cryptic "Connection closed." Root cause: launching with `python server.py` instead of `python -m mcp_server` broke package imports, and the client only saw a dead subprocess.

→ Write the failure path first. Real web pages 404, time out, and hide behind paywalls. My pipeline degrades to search snippets instead of dying.

MCP is becoming the standard interface between models and tools — like a USB port for AI. Building a small server taught me more than consuming a dozen big ones.

Full write-up with code (link in comments). The repo is open source — clone it and tell me what tool you'd add.

#MCP #AIEngineering #LLM #Python #AIAgents

---

## Post 2 — Multi-agent pipeline (week 2)

Unpopular opinion: most "multi-agent systems" should be pipelines, not swarms.

My open-source research assistant Sage uses 4 agents — Orchestrator, Researcher, Analyst, Writer. One agent, one job, strict boundaries:

→ The Orchestrator plans but never searches.
→ The Researcher executes the plan via MCP tools — and contains *zero* LLM calls. Once the plan exists, execution is deterministic plumbing.
→ The Analyst synthesizes but can't search.
→ The Writer formats but can't invent sources.

Why it matters: when a report comes out bad, I can read the plan, the notes, and the analysis independently. The failing stage identifies itself. Try doing that with one mega-prompt.

The trade-off is honest too: a strict pipeline can't re-plan mid-run. Predictability vs adaptivity is a *choice*, not a default you inherit from a framework.

Architecture deep-dive with code in the comments.

What's the fifth agent you'd add? My vote: a critic that verifies citations.

#AIAgents #LLM #SystemDesign #MCP #GenAI

---

## Post 3 — Provider-agnostic agents (week 3)

The most useful thing I learned building my agent pipeline:

**Forced tool use is just structured output wearing a different API.**

I needed my Orchestrator to emit a machine-readable research plan. Two providers, two dialects:

→ Claude: define a fictional tool whose input schema IS your output schema, then force the call with tool_choice. The model literally cannot reply with prose.

→ OpenAI-compatible (OpenRouter, Groq, Ollama): request JSON mode, fall back when the endpoint doesn't support it, and always strip markdown code fences — even strong models wrap JSON in ``` under pressure.

Both paths converge on ONE validator before anything downstream runs. The rest of the pipeline has no idea which vendor produced its input.

Result: I switch between Claude and Llama 3.3 70B with one env var. Same pipeline, same report format.

If you're building agents in 2026, vendor-quarantine is cheap insurance. Full post with code in comments.

Which provider quirk has bitten you hardest?

#LLM #AIEngineering #Claude #OpenSource #GenAI

---

## Bonus: series announcement post (optional, day 0)

I'm starting a 3-part series on building production-style AI agents — based on Sage, an open-source multi-agent research assistant I built with Python, MCP, and Claude.

Part 1: Building an MCP server from scratch (most tutorials only show you how to consume one)
Part 2: Why 4 specialized agents beat 1 mega-prompt
Part 3: Running the same pipeline on Claude OR open-weight models with one env var

Everything is open source and runnable. No frameworks, no hand-waving — a few hundred lines of readable Python.

Follow along if you're building with LLMs. Part 1 drops this week.

#AIAgents #MCP #BuildInPublic #Python #GenAI
