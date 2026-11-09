"""Test-only MCP server with an unauthorized user context."""

import server_api_adapter as adapter

from scheduling_api import RequestContext

adapter.DEMO_CONTEXT = RequestContext(
    user_id="unauthorized-user",
    tenant_id="university_a",
    permissions=frozenset(),
)

if __name__ == "__main__":
    adapter.mcp.run()
