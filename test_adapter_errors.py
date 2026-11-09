import asyncio
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER_PATH = (
    Path(__file__).resolve().parent
    / "server_api_adapter_unauthorized.py"
)


async def main():
    params = StdioServerParameters(
        command=sys.executable,
        args=[str(SERVER_PATH)],
    )

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            result = await session.call_tool(
                "get_schedule_conflicts",
                arguments={"term_id": "2027-SPRING"},
            )

            assert result.isError, (
                "Expected MCP to report a tool error."
            )
            print("PASS: MCP reports failed tool execution")

            error_text = "\n".join(
                block.text
                for block in result.content
                if block.type == "text"
            )

            assert "PERMISSION_DENIED" in error_text, (
                f"Expected permission error, got: {error_text}"
            )
            print("PASS: Permission-denied error propagated")

            assert "conflict-001" not in error_text
            assert "conflict-002" not in error_text
            print("PASS: No unauthorized conflict data returned")


if __name__ == "__main__":
    asyncio.run(main())
