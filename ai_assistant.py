import json
import time

from openai import OpenAI

from mcp_bridge import call_mcp_tool


TOOLS = [
    {
        "type": "function",
        "name": "get_schedule_conflicts",
        "description": (
            "Find room and instructor scheduling conflicts "
            "for an academic term."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "term_id": {"type": "string"}
            },
            "required": ["term_id"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "get_sections_by_term",
        "description": (
            "Retrieve academic course sections, including "
            "courses, instructors, rooms, days, times, and enrollment. "
            "Use this to answer questions about specific courses, "
            "instructors, schedules, or overlapping sections."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "term_id": {"type": "string"}
            },
            "required": ["term_id"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "find_available_rooms",
        "description": (
            "Find available classrooms for a specified academic term, "
            "day, time interval, and minimum seating capacity. "
            "Times must use 24-hour HH:MM format."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "term_id": {"type": "string"},
                "day": {
                    "type": "string",
                    "enum": [
                        "MON", "TUE", "WED", "THU",
                        "FRI", "SAT", "SUN"
                    ],
                },
                "start": {"type": "string"},
                "end": {"type": "string"},
                "minimum_capacity": {"type": "integer"},
            },
            "required": [
                "term_id",
                "day",
                "start",
                "end",
                "minimum_capacity",
            ],
            "additionalProperties": False,
        },
        "strict": True,
    },
]

ALLOWED_TOOLS = {
    "get_schedule_conflicts",
    "get_sections_by_term",
    "find_available_rooms",
}


def evaluate_scheduling_assistant(question: str) -> dict:
    started_at = time.perf_counter()
    selected_tools = []
    api_usage = []

    client = OpenAI()

    instructions = (
        "You are an academic scheduling assistant. "
        "Use tools whenever scheduling facts are needed. "
        "When a user asks for information available through a tool, "
        "call the appropriate tool immediately. "
        "Do not ask permission to retrieve information. "
        "For section counts, retrieve sections and use the returned count. "
        "Available capabilities include scheduling conflicts, "
        "course sections, and classroom availability. "
        "Use 2027-SPRING for Spring 2027. "
        "For room searches, use minimum_capacity=0 if the "
        "user does not specify a capacity. "
        "Do not invent scheduling data. "
        "Never claim to have checked information unless "
        "a tool actually returned it. "
        "For unsupported requests, explain the limitation. "
        "This assistant is strictly READ-ONLY. "
        "You cannot create, update, delete, cancel, or modify sections. "
        "Never claim an action was completed unless an authorized "
        "tool explicitly confirms that action. "
        "If asked to modify scheduling data, clearly state that "
        "you cannot perform that action. "
        "When listing matching sections or rooms, include ALL "
        "matching records returned by the tool, not just the first. "
        "Keep answers concise but complete."
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

    api_usage.append({
        "input_tokens": response.usage.input_tokens if response.usage else 0,
        "output_tokens": response.usage.output_tokens if response.usage else 0,
    })

    tool_outputs = []

    for item in response.output:
        if item.type != "function_call":
            continue

        if item.name not in ALLOWED_TOOLS:
            raise ValueError(f"Unsupported tool: {item.name}")

        arguments = json.loads(item.arguments)

        selected_tools.append({
            "name": item.name,
            "arguments": arguments,
        })

        # Tenant identity remains fixed inside the MCP adapter.
        result = call_mcp_tool(
            item.name,
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
        return {
            "answer": response.output_text,
            "selected_tools": selected_tools,
            "latency_seconds": round(time.perf_counter() - started_at, 3),
            "input_tokens": sum(u["input_tokens"] for u in api_usage),
            "output_tokens": sum(u["output_tokens"] for u in api_usage),
        }

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

    api_usage.append({
        "input_tokens": final_response.usage.input_tokens if final_response.usage else 0,
        "output_tokens": final_response.usage.output_tokens if final_response.usage else 0,
    })

    return {
        "answer": final_response.output_text,
        "selected_tools": selected_tools,
        "latency_seconds": round(time.perf_counter() - started_at, 3),
        "input_tokens": sum(u["input_tokens"] for u in api_usage),
        "output_tokens": sum(u["output_tokens"] for u in api_usage),
    }


def ask_scheduling_assistant(question: str) -> str:
    return evaluate_scheduling_assistant(question)["answer"]
