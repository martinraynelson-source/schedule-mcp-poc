import asyncio
import json
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import OpenAI

SERVER_PATH = Path(__file__).resolve().parent / "server_api_adapter.py"


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

            print("\nSchedule MCP Assistant")
            print("Ask questions about academic scheduling.")
            print("Type 'exit' to quit.\n")

            while True:
                question = input("You: ").strip()

                if question.lower() in {"exit", "quit"}:
                    print("Goodbye!")
                    break

                if not question:
                    continue

                response = client.responses.create(
                    model="gpt-5-nano",
                    instructions=(
                        "You are an academic scheduling assistant. "
                        "Use MCP tools for scheduling facts. "
                        "Base answers only on tool results. "
                        "Use term 2027-SPRING if the user says Spring 2027. "
                        "Use MON, TUE, WED, THU, FRI, SAT, SUN for days. "
                        "Do not invent scheduling information."
                    ),
                    input=question,
                    tools=openai_tools,
                    tool_choice="auto",
                    reasoning={"effort": "minimal"},
                    max_output_tokens=400,
                )

                tool_outputs = []

                for item in response.output:
                    if item.type != "function_call":
                        continue

                    if item.name not in valid_tools:
                        raise ValueError(f"Unknown tool: {item.name}")

                    arguments = json.loads(item.arguments)

                    print(f"\n[MCP tool: {item.name}]")
                    print(f"[Arguments: {arguments}]")

                    result = await session.call_tool(
                        item.name,
                        arguments=arguments,
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

                if tool_outputs:
                    final_response = client.responses.create(
                        model="gpt-5-nano",
                        instructions=(
                            "Answer using only the MCP tool results. "
                            "Be concise and accurate. "
                            "Do not invent information."
                        ),
                        previous_response_id=response.id,
                        input=tool_outputs,
                        tool_choice="none",
                        reasoning={"effort": "minimal"},
                        max_output_tokens=500,
                    )
                    answer = final_response.output_text
                else:
                    answer = response.output_text

                print("\nAssistant:", answer, "\n")


if __name__ == "__main__":
    asyncio.run(main())
