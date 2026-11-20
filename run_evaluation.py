import json
import time
from datetime import datetime, timezone
from pathlib import Path

from ai_assistant import evaluate_scheduling_assistant


def run_evaluation():
    cases = json.loads(Path("evaluation_cases.json").read_text())
    results = []

    print(f"\nRunning {len(cases)} AI evaluation cases...\n")

    for index, case in enumerate(cases, start=1):
        print(f"[{index}/{len(cases)}] {case['id']}", flush=True)

        try:
            result = evaluate_scheduling_assistant(case["question"])

            selected = [
                tool["name"]
                for tool in result["selected_tools"]
            ]

            expected_tool = case["expected_tool"]

            tool_correct = (
                selected == [expected_tool]
                if expected_tool is not None
                else len(selected) == 0
            )

            answer = result["answer"]
            expected_terms = case["expected_terms"]

            facts_found = [
                term for term in expected_terms
                if term.lower() in answer.lower()
            ]

            fact_coverage = (
                len(facts_found) / len(expected_terms)
                if expected_terms else None
            )

            forbidden_terms = case.get("forbidden_terms", [])

            incorrect_facts_found = [
                term for term in forbidden_terms
                if term.lower() in answer.lower()
            ]

            incorrect_fact_check = (
                len(incorrect_facts_found) == 0
                if forbidden_terms else None
            )

            action_integrity = None

            if case["id"] == "unsupported_action":
                normalized = (
                    answer.lower()
                    .replace("\u2019", "'")
                    .replace("\u2018", "'")
                )

                refusal_phrases = (
                    "can't",
                    "cannot",
                    "unable to",
                    "not able to",
                    "do not have permission",
                )

                completion_phrases = (
                    "has been canceled",
                    "has been cancelled",
                    "successfully canceled",
                    "successfully cancelled",
                    "cancellation request processed",
                )

                action_integrity = (
                    any(phrase in normalized for phrase in refusal_phrases)
                    and not any(
                        phrase in normalized
                        for phrase in completion_phrases
                    )
                )

            record = {
                "id": case["id"],
                "action_integrity": action_integrity,
                "forbidden_terms": forbidden_terms,
                "incorrect_facts_found": incorrect_facts_found,
                "incorrect_fact_check": incorrect_fact_check,
                "question": case["question"],
                "answer": answer,
                "expected_tool": expected_tool,
                "selected_tools": selected,
                "tool_correct": tool_correct,
                "expected_terms": expected_terms,
                "facts_found": facts_found,
                "fact_coverage": fact_coverage,
                "latency_seconds": result["latency_seconds"],
                "input_tokens": result["input_tokens"],
                "output_tokens": result["output_tokens"],
                "error": None,
            }

            print(
                f"  Tool: {'PASS' if tool_correct else 'FAIL'}"
                f" | Facts: "
                f"{f'{fact_coverage:.0%}' if fact_coverage is not None else 'N/A'}"
                f" | Latency: {result['latency_seconds']}s"
            )

        except Exception as exc:
            record = {
                "id": case["id"],
                "question": case["question"],
                "error": str(exc),
                "tool_correct": False,
                "fact_coverage": None,
            }

            print(f"  ERROR: {exc}")

        results.append(record)

    completed = [
        r for r in results if r["error"] is None
    ]

    tool_accuracy = (
        sum(r["tool_correct"] for r in results) / len(results)
        if results else 0
    )

    scored_facts = [
        r["fact_coverage"]
        for r in completed
        if r["fact_coverage"] is not None
    ]

    average_fact_coverage = (
        sum(scored_facts) / len(scored_facts)
        if scored_facts else None
    )

    incorrect_fact_tests = [
        r["incorrect_fact_check"]
        for r in completed
        if r.get("incorrect_fact_check") is not None
    ]

    incorrect_fact_pass_rate = (
        sum(incorrect_fact_tests) / len(incorrect_fact_tests)
        if incorrect_fact_tests else None
    )

    action_tests = [
        r["action_integrity"]
        for r in completed
        if r.get("action_integrity") is not None
    ]

    action_integrity_rate = (
        sum(action_tests) / len(action_tests)
        if action_tests else None
    )

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action_integrity_rate": action_integrity_rate,
        "incorrect_fact_pass_rate": incorrect_fact_pass_rate,
        "total_cases": len(results),
        "completed_cases": len(completed),
        "tool_selection_accuracy": tool_accuracy,
        "average_fact_coverage": average_fact_coverage,
        "total_input_tokens": sum(
            r.get("input_tokens", 0) for r in results
        ),
        "total_output_tokens": sum(
            r.get("output_tokens", 0) for r in results
        ),
        "results": results,
    }

    output_path = Path("evaluation_results.json")
    output_path.write_text(json.dumps(report, indent=2))

    print("\n=== Evaluation Summary ===")
    print(f"Completed: {len(completed)}/{len(results)}")
    print(f"Tool selection accuracy: {tool_accuracy:.1%}")

    if average_fact_coverage is not None:
        print(f"Average fact coverage: {average_fact_coverage:.1%}")

    if action_integrity_rate is not None:
        print(f"Action integrity: {action_integrity_rate:.1%}")

    if incorrect_fact_pass_rate is not None:
        print(f"Incorrect-fact checks passed: {incorrect_fact_pass_rate:.1%}")

    print(f"Input tokens: {report['total_input_tokens']}")
    print(f"Output tokens: {report['total_output_tokens']}")
    print(f"Report saved: {output_path}")


if __name__ == "__main__":
    run_evaluation()
