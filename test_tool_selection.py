import asyncio
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

            # Convert MCP tool definitions to OpenAI function tools.
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
                    "Use the available tools to answer scheduling questions. "
                    "For weekdays, use MON, TUE, WED, THU, FRI, SAT, SUN."
                ),
                input="Find scheduling conflicts for Spring 2027 (term 2027-SPRING).",
                tools=openai_tools,
                tool_choice="required",
                reasoning={"effort": "minimal"},
                max_output_tokens=250,
            )

            print("\nAI tool selection:")
            for item in response.output:
                if item.type == "function_call":
                    print("Tool:", item.name)
                    print("Arguments:", item.arguments)

            print("\nToken usage:")
            print("Input:", response.usage.input_tokens)
            print("Output:", response.usage.output_tokens)


if __name__ == "__main__":
    asyncio.run(main())
