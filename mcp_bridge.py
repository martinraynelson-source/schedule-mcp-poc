import asyncio
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER_PATH = Path(__file__).resolve().parent / "server.py"


async def call_mcp_tool_async(
    tool_name: str,
    arguments: dict,
    server_name: str = "server.py",
):
    """Call a scheduling tool through the MCP protocol."""

    allowed_servers = {
        "server.py",
        "server_api_adapter.py",
    }

    if server_name not in allowed_servers:
        raise ValueError("Unsupported MCP server")

    server_path = Path(__file__).resolve().parent / server_name

    server_params = StdioServerParameters(
        command=sys.executable,
        args=[str(server_path)],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            result = await session.call_tool(
                tool_name,
                arguments=arguments,
            )

            if result.isError:
                error_text = "\n".join(
                    block.text
                    for block in result.content
                    if block.type == "text"
                )
                raise RuntimeError(error_text or "MCP tool execution failed")

            if result.structuredContent is not None:
                data = result.structuredContent
                if (
                    isinstance(data, dict)
                    and isinstance(data.get("result"), str)
                ):
                    import json
                    return json.loads(data["result"])
                return data

            import json

            for block in result.content:
                if block.type == "text":
                    return json.loads(block.text)

            raise RuntimeError("MCP tool returned no usable data")


def call_mcp_tool(
    tool_name: str,
    arguments: dict,
    server_name: str = "server.py",
):
    """Synchronous wrapper for Streamlit."""

    return asyncio.run(
        call_mcp_tool_async(tool_name, arguments, server_name)
    )
