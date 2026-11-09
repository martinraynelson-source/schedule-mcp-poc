import asyncio
import json
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER_PATH = Path(__file__).resolve().parent / "server_api_adapter.py"


async def main():
    params = StdioServerParameters(
        command=sys.executable,
        args=[str(SERVER_PATH)],
    )

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            tool_names = [tool.name for tool in tools.tools]

            assert "get_schedule_conflicts" in tool_names
            print("PASS: MCP tool discovered")

            result = await session.call_tool(
                "get_schedule_conflicts",
                arguments={"term_id": "2027-SPRING"},
            )

            assert not result.isError, "MCP tool execution failed"

            response = json.loads(
                next(
                    block.text
                    for block in result.content
                    if block.type == "text"
                )
            )

            assert response["status"] == "success"
            assert response["total_count"] == 2

            conflict_ids = {
                conflict["conflict_id"]
                for conflict in response["conflicts"]
            }

            assert conflict_ids == {
                "conflict-001",
                "conflict-002",
            }

            print("PASS: MCP adapter returned University A conflicts")
            print("PASS: University B conflicts excluded")
            print()
            print(json.dumps(response, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
