import asyncio
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER_PATH = Path(__file__).resolve().parent / "server.py"


async def main():
    params = StdioServerParameters(
        command=sys.executable,
        args=[str(SERVER_PATH)],
    )

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()

            print("\nMCP tools available to the AI assistant:\n")

            for tool in tools.tools:
                print(f"Name: {tool.name}")
                print(f"Description: {tool.description}")
                print(f"Input schema: {tool.inputSchema}")
                print("-" * 50)


if __name__ == "__main__":
    asyncio.run(main())
