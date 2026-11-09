
import asyncio
import sys
import unittest
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


SERVER_PATH = Path(__file__).resolve().parent / "server.py"


class TestScheduleMCPIntegration(unittest.TestCase):

    def test_mcp_tools(self):
        asyncio.run(self._run_mcp_tests())

    async def _run_mcp_tests(self):
        params = StdioServerParameters(
            command=sys.executable,
            args=[str(SERVER_PATH)],
        )

        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                # Verify the server exposes the expected tools.
                response = await session.list_tools()
                tool_names = {tool.name for tool in response.tools}

                expected = {
                    "get_sections_by_term",
                    "get_schedule_conflicts",
                    "find_available_rooms",
                }
                self.assertTrue(expected.issubset(tool_names))

                # Verify conflict detection works over MCP.
                result = await session.call_tool(
                    "get_schedule_conflicts",
                    arguments={"term_id": "2027-SPRING"},
                )

                self.assertFalse(result.isError)

                # Verify the server returned two conflicts.
                import json

                text_blocks = [
                    block.text
                    for block in result.content
                    if block.type == "text"
                ]
                self.assertTrue(text_blocks)

                payload = json.loads(text_blocks[0])
                self.assertEqual(payload["count"], 2)


if __name__ == "__main__":
    unittest.main()

