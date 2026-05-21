"""Run the sage-tools MCP server: python -m mcp_server"""

from mcp_server.server import mcp

if __name__ == "__main__":
    mcp.run()
