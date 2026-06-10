# Publishing checklist — Sage blog campaign

Use this before and after you publish on Medium and LinkedIn.

---

## Pre-flight (do once)

- [ ] Replace `YOUR_USERNAME` in all `content/` files with your GitHub org/username
- [ ] Confirm repo is **public** on GitHub
- [ ] Confirm `.env` is **not** committed (only `.env.example`)
- [ ] Run pipeline once more for a fresh screenshot: `python main.py --query "..." -o report.md`
- [ ] Rotate any keys that ever appeared in screenshots or old `.env.example` commits

---

## Medium article

**File:** `content/medium-mcp-multi-agent-sage.md`

**Title:** I Built a Research Agent Pipeline with MCP and Four Specialized Agents (Here's What Actually Worked)

**Subtitle:** Why separating plan → gather → analyze → write beats one mega-prompt—and how a custom MCP server fits in.

**Suggested tags (5):** Artificial Intelligence, Machine Learning, Programming, Software Engineering, Technology

**Topics / SEO keywords:** MCP, Model Context Protocol, multi-agent systems, AI agents, LLM, Python, FastMCP, tool use

**Cover image ideas:**
- Architecture diagram (export from README or WORKFLOW_README)
- Terminal screenshot of 4-stage progress output
- Simple flowchart: Query → 4 agents → report.md

**Publishing steps:**
1. New story on Medium → paste markdown (or use Medium import)
2. Add code blocks with syntax highlighting where needed
3. Set canonical link if you cross-post elsewhere later
4. Publish → copy live URL

**After publish:**
- [ ] Save URL: _______________________________

---

## LinkedIn native article

**File:** `content/linkedin-article-mcp-multi-agent.md`

**Title:** MCP + Multi-Agent Pipelines: A Small Python Project That Ties Them Together

**Publishing steps:**
1. LinkedIn → Write article → paste adapted content
2. Add headline image (same as Medium or cropped terminal shot)
3. In body, set Medium link to your live Medium URL
4. Publish → copy live URL

**After publish:**
- [ ] Save URL: _______________________________
- [ ] Update `content/linkedin-posts.md` Post 1 comment and Post 3 with both URLs
- [ ] Optional: pin article to profile (Featured section)

---

## LinkedIn posts schedule

**File:** `content/linkedin-posts.md`

| Day | Post | Action |
|-----|------|--------|
| 0 | Post 1 — Launch | Paste text, add Medium link in first comment, GitHub in post |
| 2–3 | Post 2 — Boundary insight | Text only |
| 7 | Post 3 — Results | Add report excerpt image if possible |

**Engagement (same week):**
- [ ] Comment thoughtfully on 5–10 posts about MCP, agents, or Anthropic tool use (2–3 sentences each, no spam)
- [ ] Reply to every comment on your posts within 24h

**Hashtags (use 3–5 max per post):** #MCP #AIAgents #LLM #Python #OpenSource #GenerativeAI #BuildInPublic

---

## README update

After URLs exist, update README **Blog** section (see repo README) with:
- Medium article link
- LinkedIn article link

---

## Optional: commit `content/` to git

Safe to commit — no secrets. Helps you version drafts.

```bash
git add content/
git commit -m "Add Medium and LinkedIn blog drafts for Sage"
```

---

## Post-publish metrics (track informally)

| Metric | Medium | LinkedIn |
|--------|--------|----------|
| Views | | |
| Reads / read ratio | | |
| Claps / likes | | |
| Comments | | |
| GitHub stars (week of publish) | | |

Review after 2 weeks: which hook worked? Double down on that angle for post #2.
