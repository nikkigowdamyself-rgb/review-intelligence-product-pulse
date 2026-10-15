"""Minimal stdio MCP client used by the Streamlit approval button."""
import asyncio, sys
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).parent

async def _call(tool_name, arguments):
    server = StdioServerParameters(
        command=sys.executable,
        args=[str(ROOT / "mcp_server.py")],
        cwd=str(ROOT),
        env=None
    )
    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments)
            if result.isError:
                raise RuntimeError(f"MCP tool {tool_name} failed: {result.content}")
            texts = [part.text for part in result.content if getattr(part, "text", None)]
            import json
            for item in texts:
                try:
                    return json.loads(item)
                except Exception:
                    continue
            return {"result": texts}

def call_mcp_tool(tool_name, arguments):
    return asyncio.run(_call(tool_name, arguments))
