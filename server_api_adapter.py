"""MCP adapter for the simulated Scheduling API."""

import json

from mcp.server.fastmcp import FastMCP

from scheduling_api import (
    RequestContext,
    SchedulingAPIError,
    get_schedule_conflicts as api_get_schedule_conflicts,
)

mcp = FastMCP("Schedule API Adapter")

# Simulated authenticated session for this local demonstration.
# In production, verified context would come from trusted
# authentication and authorization services.
DEMO_CONTEXT = RequestContext(
    user_id="biology-scheduler-001",
    tenant_id="university_a",
    permissions=frozenset({"schedule:read"}),
)


@mcp.tool()
def get_schedule_conflicts(term_id: str) -> str:
    """Retrieve authorized scheduling conflicts for an academic term."""
    try:
        result = api_get_schedule_conflicts(
            context=DEMO_CONTEXT,
            term_id=term_id,
        )
        return json.dumps(result)

    except SchedulingAPIError as error:
        raise ValueError(
            json.dumps({
                "status": "error",
                "code": error.code,
                "message": str(error),
            })
        ) from error


if __name__ == "__main__":
    mcp.run()
