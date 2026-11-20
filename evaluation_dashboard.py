import json
from pathlib import Path

import streamlit as st


def render_evaluation_dashboard():
    st.subheader("AI Evaluation Dashboard")
    st.caption(
        "Evaluation of MCP tool selection, answer quality, "
        "read-only behavior, and performance."
    )

    path = Path(__file__).with_name("evaluation_results.json")

    if not path.exists():
        st.warning("No evaluation results found.")
        return

    report = json.loads(path.read_text())
    results = report.get("results", [])
    completed = [r for r in results if r.get("error") is None]

    st.info(
        "Metrics reflect a small, simulated test suite. "
        "They are not production reliability estimates."
    )

    col1, col2, col3, col4 = st.columns(4)

    def percentage(value):
        return f"{value:.0%}" if value is not None else "N/A"

    with col1:
        st.metric(
            "Tool Selection",
            percentage(report.get("tool_selection_accuracy")),
        )

    with col2:
        st.metric(
            "Fact Coverage",
            percentage(report.get("average_fact_coverage")),
        )

    with col3:
        st.metric(
            "Action Integrity",
            percentage(report.get("action_integrity_rate")),
        )

    with col4:
        st.metric(
            "Incorrect-Fact Checks",
            percentage(report.get("incorrect_fact_pass_rate")),
        )

    st.divider()
    st.subheader("Performance")

    latencies = [
        r["latency_seconds"]
        for r in completed
        if isinstance(r.get("latency_seconds"), (int, float))
    ]

    avg_latency = (
        sum(latencies) / len(latencies)
        if latencies else None
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Average Latency",
            f"{avg_latency:.2f}s" if avg_latency is not None else "N/A",
        )

    with col2:
        st.metric(
            "Input Tokens",
            f"{report.get('total_input_tokens', 0):,}",
        )

    with col3:
        st.metric(
            "Output Tokens",
            f"{report.get('total_output_tokens', 0):,}",
        )

    st.divider()
    st.subheader("Individual Test Results")

    for result in results:
        test_id = result.get("id", "Unknown")
        error = result.get("error")

        with st.expander(
            f"{'❌' if error else '📋'} {test_id}"
        ):
            if error:
                st.error(str(error))
                continue

            st.write("**Question:**", result.get("question", ""))
            st.write("**AI Answer:**")
            st.write(result.get("answer", ""))

            st.write(
                "**Tool Selection:**",
                "PASS" if result.get("tool_correct") else "FAIL",
            )

            coverage = result.get("fact_coverage")
            if coverage is not None:
                st.write("**Fact Coverage:**", percentage(coverage))

            integrity = result.get("action_integrity")
            if integrity is not None:
                st.write(
                    "**Action Integrity:**",
                    "PASS" if integrity else "FAIL",
                )

            incorrect = result.get("incorrect_fact_check")
            if incorrect is not None:
                st.write(
                    "**Incorrect-Fact Check:**",
                    "PASS" if incorrect else "FLAGGED",
                )

            st.write(
                "**Latency:**",
                f"{result.get('latency_seconds', 0):.2f}s",
            )

    st.caption(
        "Fact coverage measures expected-term inclusion. "
        "Incorrect-fact checks use predefined forbidden terms. "
        "Neither metric independently establishes factual accuracy."
    )
