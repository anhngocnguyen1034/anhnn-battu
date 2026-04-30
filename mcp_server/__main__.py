# -*- coding: utf-8 -*-
"""
Entry point for running the MCP server as a module:
    python -m mcp_server.server
"""
import asyncio
from mcp_server.server import main

asyncio.run(main())
