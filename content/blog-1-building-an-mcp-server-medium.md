# Most People Use MCP Servers. I Built One — Here's What the Tutorials Skip

*Part 1 of 3 in the "Agents in Practice" series, based on Sage, my open-source multi-agent research assistant.*

---

The Model Context Protocol (MCP) has become the standard way to connect AI models to external tools — Anthropic introduced it, and OpenAI, Google, and most major IDEs have since adopted it. The mental model that finally made it click for me: **MCP is a USB port for AI.** Any compatible model can plug into any compatible tool through one standardized interface.

Most tutorials show you how to *consume* existing MCP servers — point Claude Desktop at a config file, done. You learn far more by *authoring* one. This post walks through the MCP server I built for **Sage**, a multi-agent research pipeline that takes a question and returns a cited markdown report — including the part where everything broke with a cryptic `Connection closed` error.

**Repo:** https://github.com/kushagra-2240/sage

---

## The shape of an MCP server

An MCP setup has two sides:

- **Host/client** — the application running the agent loop (Claude Desktop, an IDE, or your own Python script).
- **Server** — a process exposing **tools** the model can invoke.

They talk JSON-RPC, typically over **stdio** for local development: your client spawns the server as a subprocess, exchanges messages, and tears it down when done. No ports, no auth, no deployment — which is exactly why it's the right transport for learning.

Sage's server, `sage-tools`, exposes three tools the research agent needs:

| Tool | Backed by | Purpose |
|------|-----------|---------|
| `web_search` | Tavily API | Search results tuned for LLM consumption |
| `extract_content` | httpx + BeautifulSoup | URL → clean main text |
| `save_note` | in-memory dict | Paper trail for each research step |

## Registering tools with FastMCP

[FastMCP](https://gofastmcp.com/) turns a typed Python function into a protocol-compliant tool. The decorator reads your type hints and docstring and generates the JSON schema the model sees:

```python
from fastmcp import FastMCP

mcp = FastMCP("sage-tools")

@mcp.tool
def web_search(query: str, max_results: int = 5) -> list[dict[str, Any]]:
    """
    Search the web using the Tavily API.

    Args:
        query: Search terms to look up.
        max_results: Maximum number of results to return (default 5).

    Returns:
        A list of dicts, each with keys: title, url, snippet.
    """
    if not query or not query.strip():
        raise ValueError("query must be a non-empty string")

    try:
        return _search_web(query.strip(), max_results=max_results)
    except ValueError:
        raise
    except Exception as exc:
        raise RuntimeError(f"Tavily search failed: {exc}") from exc

if __name__ == "__main__":
    mcp.run()
```

Three deliberate choices here, because **your docstring is your API documentation for the model**:

1. **The docstring is a prompt.** The model decides whether and how to call your tool based on this text. Vague docstrings produce vague tool calls.
2. **Validate inputs at the boundary.** The model *will* eventually send an empty query. Fail fast with `ValueError` rather than letting a confusing error surface three layers deep.
3. **Normalize errors.** Wrapping provider exceptions in `RuntimeError` with context means the client sees "Tavily search failed: …" instead of a raw stack trace from a library it doesn't know exists.

The tool implementations live in separate modules (`mcp_server/tools/`), keeping the server file a thin protocol layer. That separation pays off in tests: you unit-test the logic without spinning up an MCP session at all.

## The client side: spawning is part of your API

Sage's research agent connects to the server using the official `mcp` Python SDK:

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

def get_server_params(env: dict[str, str] | None = None) -> StdioServerParameters:
    server_env = {**os.environ}
    if env:
        server_env.update(env)

    return StdioServerParameters(
        command=sys.executable,
        args=["-m", "mcp_server"],   # ← module form, not a script path
        env=server_env,
        cwd=str(PROJECT_ROOT),
    )

async def run_with_session(server_params, callback):
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            return await callback(session)
```

Every detail in `get_server_params` exists because something broke without it.

### War story: `McpError: Connection closed`

My first integration test died at the MCP handshake. The error told me nothing — just that the subprocess had exited.

Root cause: I was launching the server as `python mcp_server/server.py`. Run that way, Python doesn't treat `mcp_server` as a package, so the server's own imports (`from mcp_server.tools.search import ...`) raised `ModuleNotFoundError` — and the client saw only a dead process.

The fix is to run the server **as a module from the project root**:

```bash
python -m mcp_server
```

…and to pass `cwd` and the parent's environment explicitly, so `TAVILY_API_KEY` actually reaches the child process. The lesson generalizes: **when you build MCP clients, how you spawn the server is part of your API design.** Subprocess + stdio means classic subprocess failure modes — working directory, environment inheritance, import paths — now sit in your AI system's critical path.

## Parsing tool results defensively

MCP tool results arrive as content blocks, not Python objects. Sage normalizes them in one place:

```python
def parse_tool_result(result: CallToolResult) -> Any:
    if result.isError:
        raise RuntimeError(_content_to_text(result.content) or "Unknown MCP tool error")

    text = _content_to_text(result.content).strip()
    try:
        return json.loads(text)        # structured outputs (search results)
    except json.JSONDecodeError:
        return text                    # plain text (extracted content)
```

One chokepoint for error handling and deserialization means agents never touch raw protocol types. When the protocol evolves — and it is evolving fast — there's exactly one function to update.

## What I'd tell you before you build one

**Start with stdio, not HTTP.** You can move to remote transports later; stdio removes deployment from the learning loop.

**Keep tools coarse.** Three focused tools beat ten granular ones. Every tool adds schema tokens to each model call and another branch the model can take wrongly.

**Write the failure path first.** What happens when the URL 404s, when the API key is missing, when the page is 500KB of JavaScript? In Sage, `extract_content` distinguishes timeouts, HTTP errors, and unparseable pages — and the research agent degrades gracefully to the search snippet when extraction fails.

**Test without tokens.** Sage's pytest suite mocks the Tavily and HTTP layers, so CI verifies tool logic and protocol plumbing without burning API credits.

---

In **Part 2**, I cover the consumer of this server: a four-agent pipeline (Orchestrator → Researcher → Analyst → Writer) and why strict role boundaries beat one mega-prompt. **Part 3** covers making the whole thing provider-agnostic — the same pipeline runs on Claude or any OpenAI-compatible model, switched by one env var.

*Clone the repo, run a query, and tell me one tool you'd add to `sage-tools`. The protocol gets better when we share boring, working examples.*

**Repo:** https://github.com/kushagra-2240/sage · **MCP spec:** https://modelcontextprotocol.io/ · **FastMCP:** https://gofastmcp.com/
