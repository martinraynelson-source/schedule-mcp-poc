
import asyncio
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Locate the server in the same folder as this client.
SERVER_PATH = Path(__file__).resolve().parent / "server.py"


async def main():
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[str(SERVER_PATH)],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("Connected to Schedule MCP server!\n")

            # Discover the server's available tools.
            tools = await session.list_tools()

            print("Available tools:")
            for tool in tools.tools:
                print(f"  - {tool.name}")

            # Execute a scheduling tool through MCP.
            print("\nChecking Spring 2027 conflicts...")

            result = await session.call_tool(
                "get_schedule_conflicts",
                arguments={"term_id": "2027-SPRING"},
            )

            if result.isError:
                print("Tool returned an error:")
            else:
                print("Tool response:")

            for block in result.content:
                if block.type == "text":
                    print(block.text)
            # Retrieve course sections.
            print("\nRetrieving Spring 2027 sections...")

            sections = await session.call_tool(
                "get_sections_by_term",
                arguments={"term_id": "2027-SPRING"},
            )

            for block in sections.content:
                if block.type == "text":
                    print(block.text)

            # Find available rooms.
            print("\nFinding available rooms...")

            rooms = await session.call_tool(
                "find_available_rooms",
                arguments={
                    "term_id": "2027-SPRING",
                    "day": "MON",
                    "start": "09:30",
                    "end": "10:30",
                    "min_capacity": 30,
                },
            )

            for block in rooms.content:
                if block.type == "text":
                    print(block.text)

if __name__ == "__main__":
    asyncio.run(main())
