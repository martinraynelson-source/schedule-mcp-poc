import asyncio
import json
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import OpenAI

SERVER_PATH = Path(__file__).resolve().parent / "server.py"


async def main():
    params = StdioServerParameters(
        command=sys.executable,
        args=[str(SERVER_PATH)],
    )

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            mcp_tools = await session.list_tools()

            openai_tools = [
                {
                    "type": "function",
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": tool.inputSchema,
                }
                for tool in mcp_tools.tools
            ]

            client = OpenAI()

            response = client.responses.create(
                model="gpt-5-nano",
                instructions=(
                    "You are an academic scheduling assistant. "
                    "Use tools for scheduling information."
                ),
                input=(
                    "Find scheduling conflicts for Spring 2027 "
                    "(term 2027-SPRING)."
                ),
                tools=openai_tools,
                tool_choice="required",
                reasoning={"effort": "minimal"},
                max_output_tokens=250,
            )

            valid_tools = {tool.name for tool in mcp_tools.tools}
            calls_executed = 0

            for item in response.output:
                if item.type != "function_call":
                    continue

                if item.name not in valid_tools:
                    raise ValueError(f"Unknown tool: {item.name}")

                arguments = json.loads(item.arguments)

                print("\nAI selected:", item.name)
                print("Arguments:", arguments)

                result = await session.call_tool(
                    item.name,
                    arguments=arguments,
                )

                if result.isError:
                    raise RuntimeError(
                        f"MCP tool {item.name} returned an error: "
                        f"{result.content}"
                    )

                print("\nMCP tool result:")
                for block in result.content:
                    if block.type == "text":
                        print(block.text)

                calls_executed += 1

            if calls_executed == 0:
                raise RuntimeError("AI did not request any tool calls.")

            print(f"\nSuccessfully executed {calls_executed} MCP tool call(s).")


if __name__ == "__main__":
    asyncio.run(main())
