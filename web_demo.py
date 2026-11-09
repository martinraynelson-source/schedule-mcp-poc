from ai_assistant import ask_scheduling_assistant
import streamlit as st
from scheduling_api import RequestContext, get_schedule_conflicts
from mcp_bridge import call_mcp_tool
from server import (
    get_sections_by_term,
    find_available_rooms,
)

DEMO_CONTEXT = RequestContext(
    user_id="biology-scheduler-001",
    tenant_id="university_a",
    permissions=frozenset({"schedule:read"}),
)


st.set_page_config(
    page_title="Schedule AI Assistant",
    page_icon="📅",
    layout="wide",
)

st.title("📅 Schedule AI Assistant")
st.caption("Enterprise AI Integration Demo | Schedule MCP Proof of Concept")

with st.sidebar:
    st.header("Demo Environment")
    st.info("Institution: University A")
    st.write("Academic Term: Spring 2027")
    st.write("Access Level: Read-only")
    st.divider()
    st.caption("Simulated scheduling data. Not connected to a production SaaS system.")

st.subheader("Ask about your academic schedule")

st.write(
    "Explore scheduling conflicts, academic sections, and room availability "
    "using a conversational interface."
)

st.markdown("**Suggested questions**")

col1, col2, col3 = st.columns(3)

with col1:
    conflicts = st.button("⚠️ Show scheduling conflicts", use_container_width=True)

with col2:
    sections = st.button("📚 List academic sections", use_container_width=True)

with col3:
    rooms = st.button("🏫 Find available rooms", use_container_width=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

if conflicts:
    st.session_state.messages.append({
        "role": "user",
        "content": "Show me scheduling conflicts for Spring 2027.",
    })

    result = call_mcp_tool(
        "get_schedule_conflicts",
        {"term_id": "2027-SPRING"},
        server_name="server_api_adapter.py",
    )
    conflict_lines = []

    for conflict in result["conflicts"]:
        conflict_lines.append(
            f"- **{conflict['type']}**: "
            f"{', '.join(conflict['section_ids'])} "
            f"on {conflict['day']}"
        )

    answer = (
        f"Found **{result['total_count']} scheduling conflicts** "
        f"for Spring 2027.\n\n"
        + "\n".join(conflict_lines)
    )

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
    })

if sections:
    st.session_state.messages.append({
        "role": "user",
        "content": "List academic sections for Spring 2027.",
    })

    result = call_mcp_tool(
        "get_sections_by_term",
        {"term_id": "2027-SPRING"},
    )
    st.session_state.messages.append({
        "role": "assistant",
        "content": "### Academic Sections",
        "data": result,
        "display": "sections",
    })

if rooms:
    st.session_state.messages.append({
        "role": "user",
        "content": "Find available rooms on Monday from 9:30 to 10:30 for 30 students.",
    })

    result = call_mcp_tool(
        "find_available_rooms",
        {
            "term_id": "2027-SPRING",
            "day": "MON",
            "start": "09:30",
            "end": "10:30",
            "minimum_capacity": 30,
        },
    )

    st.session_state.messages.append({
        "role": "assistant",
        "content": "### Available Rooms",
        "data": result,
        "display": "rooms",
    })

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message.get("display") in ("sections", "rooms"):
            st.markdown(message["content"])
            data = message["data"]

            if isinstance(data, dict):
                collection = (
                    data.get("sections")
                    if message["display"] == "sections"
                    else data.get("available_rooms", data.get("rooms"))
                )
                if isinstance(collection, list):
                    if collection:
                        st.dataframe(
                            collection,
                            use_container_width=True,
                            hide_index=True,
                        )
                    else:
                        st.info("No matching records found.")
                else:
                    st.json(data)
            else:
                st.json(data)
        else:
            st.markdown(message["content"])


prompt = st.chat_input("Ask a scheduling question...")

if prompt:
    st.session_state.messages.append({
        "role": "user",
        "content": prompt,
    })

    try:
        with st.spinner("Checking scheduling data..."):
            answer = ask_scheduling_assistant(prompt)
    except Exception as exc:
        answer = f"Unable to process the question: {exc}"

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
    })

    st.rerun()

st.divider()
st.caption("Prototype interface | OpenAI + MCP scheduling assistant")
