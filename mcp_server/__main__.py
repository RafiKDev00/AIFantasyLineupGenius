# B''SD
# entry point — run with: python -m mcp_server
# or for testing: mcp dev mcp_server/__main__.py
# or for chatGPT via ngrok: MCP_TRANSPORT=sse python -m mcp_server

import os

# gotta import tools so the decorators register everything
from mcp_server.server import mcp
import mcp_server.tools  # noqa: F401, triggers all the @mcp.tool() registrations

if __name__ == "__main__":
    transport = os.getenv("MCP_TRANSPORT", "stdio")
    mcp.run(transport=transport)
