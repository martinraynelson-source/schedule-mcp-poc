import asyncio
import json

from openai import OpenAI
from mcp_bridge import call_mcp_tool


TOOLS = [
    {
        "type": "function",
        "name": "get_schedule_conflicts",
        "description": (
            "Retrieve academic scheduling conflicts "
            "for the authorized demo institution."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "term_id": {
                    "type": "string",
                    "description": "Academic term identifier.",
                }
            },
            "required": ["term_id"],
            "additionalProperties": False,
        },
        "strict": True,
    }
]


def ask_scheduling_assistant(question: str) -> str:
    client = OpenAI()

    instructions = (
        "You are an academic scheduling assistant. "
        "Use tools for scheduling facts. "
        "Only scheduling conflict information is available "
        "through the AI interface at this stage. "
        "Use 2027-SPRING for Spring 2027. "
        "Do not invent scheduling data. "
        "Never claim to have checked information unless "
        "a tool actually returned it. "
        "Keep answers concise."
    )

    response = client.responses.create(
        model="gpt-5-nano",
        instructions=instructions,
        input=question,
        tools=TOOLS,
        tool_choice="auto",
        reasoning={"effort": "minimal"},
        max_output_tokens=400,
    )

    tool_outputs = []

    for item in response.output:
        if item.type != "function_call":
            continue

        if item.name != "get_schedule_conflicts":
            raise ValueError(f"Unsupported tool: {item.name}")

        arguments = json.loads(item.arguments)

        # The tenant identity is fixed inside the MCP adapter.
        result = call_mcp_tool(
            "get_schedule_conflicts",
            arguments,
            server_name="server_api_adapter.py",
        )

        tool_outputs.append(
            {
                "type": "function_call_output",
                "call_id": item.call_id,
                "output": json.dumps(result),
            }
        )

    if not tool_outputs:
        return response.output_text

    final_response = client.responses.create(
        model="gpt-5-nano",
        instructions=(
            "Answer using only the scheduling tool results. "
            "Do not invent facts. Be concise."
        ),
        previous_response_id=response.id,
        input=tool_outputs,
        tool_choice="none",
        reasoning={"effort": "minimal"},
        max_output_tokens=500,
    )

    return final_response.output_text
