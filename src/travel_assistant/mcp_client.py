import asyncio
import json
import shlex
import sys

from mcp.client.stdio import stdio_client

from mcp import ClientSession, StdioServerParameters


async def call_local_mcp(command: str, args: str, tool_name: str, arguments: dict) -> dict:
    if command.lower() in {"python", "python3", "py"}:
        command = sys.executable
    server = StdioServerParameters(command=command, args=shlex.split(args))
    async with stdio_client(server) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments)
            if getattr(result, "isError", False):
                raise RuntimeError(f"MCP tool {tool_name} returned an error")
            content = getattr(result, "content", [])
            text = next((item.text for item in content if hasattr(item, "text")), "{}")
            return json.loads(text) if isinstance(text, str) else text


def call_local_mcp_sync(command: str, args: str, tool_name: str, arguments: dict) -> dict:
    return asyncio.run(call_local_mcp(command, args, tool_name, arguments))