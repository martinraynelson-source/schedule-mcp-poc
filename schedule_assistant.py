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
            valid_tools = {tool.name for tool in mcp_tools.tools}

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

            question = (
                "What scheduling conflicts exist in Spring 2027 "
                "(term 2027-SPRING)?"
            )

            print("\nQuestion:", question)

            response = client.responses.create(
                model="gpt-5-nano",
                instructions=(
                    "You are an academic scheduling assistant. "
                    "Use MCP tools for scheduling facts. "
                    "Base answers only on returned tool data. "
                    "Never invent scheduling information."
                ),
                input=question,
                tools=openai_tools,
                tool_choice="required",
                reasoning={"effort": "minimal"},
                max_output_tokens=300,
            )

            # Preserve the model's tool-call messages.
            conversation = [response.output]

            tool_outputs = []

            for item in response.output:
                if item.type != "function_call":
                    continue

                if item.name not in valid_tools:
                    raise ValueError(f"Unknown tool: {item.name}")

                arguments = json.loads(item.arguments)

                print("\nAI selected tool:", item.name)
                print("Arguments:", arguments)

                result = await session.call_tool(
                    item.name,
                    arguments=arguments,
                )

                if result.isError:
                    raise RuntimeError(
                        f"MCP tool error: {result.content}"
                    )

                result_text = "\n".join(
                    block.text
                    for block in result.content
                    if block.type == "text"
                )

                tool_outputs.append({
                    "type": "function_call_output",
                    "call_id": item.call_id,
                    "output": result_text,
                })

            if not tool_outputs:
                raise RuntimeError("AI requested no tools.")

            # Return tool results to the model for interpretation.
            final_response = client.responses.create(
                model="gpt-5-nano",
                instructions=(
                    "Summarize the scheduling tool results clearly. "
                    "Do not invent details beyond the data."
                ),
                previous_response_id=response.id,
                input=tool_outputs,
                tool_choice="none",
                reasoning={"effort": "minimal"},
                max_output_tokens=500,
            )

            print("\nAI Answer:\n")
            print(final_response.output_text)

            print("\nToken usage:")
            print(
                "First request:",
                response.usage.input_tokens,
                "input,",
                response.usage.output_tokens,
                "output",
            )
            print(
                "Second request:",
                final_response.usage.input_tokens,
                "input,",
                final_response.usage.output_tokens,
                "output",
            )


if __name__ == "__main__":
    asyncio.run(main())
