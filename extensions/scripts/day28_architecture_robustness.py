
#!/usr/bin/env python3
"""
Day 28 - Step 5
FSM Architecture Selection Robustness Analysis

Uses existing Day 28 Step 3 and Step 4 reports.
No RTL changes, simulation, synthesis, or new PPA measurements.
"""

import csv
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "extensions" / "results" / "day28"

SELECTION_FILE = RESULTS / "day28_architecture_selection.json"
SENSITIVITY_FILE = RESULTS / "day28_constraint_sensitivity.json"

OUTPUT_CSV = RESULTS / "day28_architecture_robustness.csv"
OUTPUT_JSON = RESULTS / "day28_architecture_robustness.json"
OUTPUT_TXT = RESULTS / "day28_architecture_robustness.txt"

SCENARIOS = (
    "area_priority",
    "power_priority",
    "timing_priority",
    "balanced",
)

EXPECTED_CASES = 8
EXPECTED_CONFIGURATIONS = 13


def load_json(path):
    if not path.is_file():
        raise ValueError(f"Missing required file: {path}")

    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object: {path}")

    if data.get("status") != "PASS":
        raise ValueError(f"Source status is not PASS: {path}")

    return data


def extract_winner(value):
    """Extract a configuration name from a supported result shape."""
    if isinstance(value, str):
        return value.strip() or None

    if isinstance(value, dict):
        for key in (
            "winner",
            "selected_configuration",
            "selected",
            "configuration",
            "configuration_name",
            "best_configuration",
            "best",
        ):
            if key in value:
                result = extract_winner(value[key])
                if result:
                    return result

    return None


def extract_scenario_winners(obj):
    """
    Read scenario winners without assuming one particular
    JSON nesting convention.
    """
    if isinstance(obj, dict):
        if all(scenario in obj for scenario in SCENARIOS):
            winners = {
                scenario: extract_winner(obj[scenario])
                for scenario in SCENARIOS
            }
            if all(winners.values()):
                return winners

        for key in (
            "winners",
            "global_winners",
            "scenario_winners",
            "selected_architectures",
            "selections",
            "results",
        ):
            if key in obj:
                found = extract_scenario_winners(obj[key])
                if found:
                    return found

    if isinstance(obj, list):
        winners = {}

        for item in obj:
            if not isinstance(item, dict):
                continue

            scenario = (
                item.get("scenario")
                or item.get("scenario_name")
                or item.get("objective")
            )

            if scenario in SCENARIOS:
                winner = extract_winner(item)
                if winner:
                    winners[scenario] = winner

        if all(scenario in winners for scenario in SCENARIOS):
            return winners

    return None


def find_case_results(obj):
    """Find the list of sensitivity cases containing winners."""
    if isinstance(obj, list):
        cases = []

        for item in obj:
            if not isinstance(item, dict):
                continue

            winners = extract_scenario_winners(item)

            if winners:
                cases.append((item, winners))

        if cases:
            return cases

        for item in obj:
            found = find_case_results(item)
            if found:
                return found

    elif isinstance(obj, dict):
        for key in (
            "results",
            "constraint_cases",
            "cases",
            "sensitivity_results",
        ):
            if key in obj:
                found = find_case_results(obj[key])
                if found:
                    return found

    return None


def case_name(item, index):
    for key in (
        "case",
        "case_name",
        "constraint_case",
        "constraint_name",
        "name",
        "id",
    ):
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    return f"case_{index:02d}"


def main():
    selection = load_json(SELECTION_FILE)
    sensitivity = load_json(SENSITIVITY_FILE)

    if selection.get("configuration_count") != EXPECTED_CONFIGURATIONS:
        raise ValueError("Step 3 configuration count is not 13")

    if sensitivity.get("configuration_count") != EXPECTED_CONFIGURATIONS:
        raise ValueError("Step 4 configuration count is not 13")

    if sensitivity.get("constraint_case_count") != EXPECTED_CASES:
        raise ValueError("Step 4 constraint case count is not 8")

    baseline = extract_scenario_winners(
        selection.get("global_winners")
    )

    if not baseline:
        raise ValueError(
            "Unable to identify Step 3 global winners. "
            "Inspect global_winners JSON structure before proceeding."
        )

    cases = find_case_results(sensitivity.get("results"))

    if not cases:
        raise ValueError(
            "Unable to identify scenario winners in Step 4 results. "
            "Inspect results JSON structure before proceeding."
        )

    if len(cases) != EXPECTED_CASES:
        raise ValueError(
            f"Expected 8 constraint cases, found {len(cases)}"
        )

    records = []
    seen_names = set()

    for index, (item, winners) in enumerate(cases, start=1):
        name = case_name(item, index)

        if name in seen_names:
            raise ValueError(f"Duplicate constraint case: {name}")

        seen_names.add(name)

        for scenario in SCENARIOS:
            original = baseline[scenario]
            selected = winners[scenario]

            records.append({
                "constraint_case": name,
                "scenario": scenario,
                "baseline_winner": original,
                "constraint_winner": selected,
                "stable": selected == original,
            })

    stable_count = sum(row["stable"] for row in records)
    changed_count = len(records) - stable_count

    scenario_summary = {}

    for scenario in SCENARIOS:
        subset = [
            row for row in records
            if row["scenario"] == scenario
        ]

        scenario_summary[scenario] = {
            "baseline_winner": baseline[scenario],
            "stable_cases": sum(row["stable"] for row in subset),
            "changed_cases": sum(
                not row["stable"] for row in subset
            ),
            "selected_architectures": dict(
                Counter(
                    row["constraint_winner"]
                    for row in subset
                )
            ),
        }

    result = {
        "day": 28,
        "step": 5,
        "analysis": "FSM architecture selection robustness",
        "status": "PASS",
        "source_files": [
            str(SELECTION_FILE.relative_to(ROOT)),
            str(SENSITIVITY_FILE.relative_to(ROOT)),
        ],
        "configuration_count": EXPECTED_CONFIGURATIONS,
        "constraint_case_count": len(cases),
        "scenario_count": len(SCENARIOS),
        "total_decisions": len(records),
        "stable_decisions": stable_count,
        "changed_decisions": changed_count,
        "stability_percentage": round(
            100 * stable_count / len(records), 2
        ),
        "baseline_winners": baseline,
        "scenario_summary": scenario_summary,
        "records": records,
        "limitations": [
            "Results reuse existing pre-layout PPA evidence.",
            "Power is based on assumed switching activity.",
            "Timing is based on reported arrival-time metrics.",
            "Different FSM variants are not proven equivalent.",
            "Robustness applies only to the tested constraints.",
            "No new RTL, simulation, synthesis, or STA was run.",
        ],
    }

    RESULTS.mkdir(parents=True, exist_ok=True)

    with OUTPUT_CSV.open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "constraint_case",
                "scenario",
                "baseline_winner",
                "constraint_winner",
                "stable",
            ],
        )
        writer.writeheader()
        writer.writerows(records)

    with OUTPUT_JSON.open("w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2)
        handle.write("\n")

    lines = [
        "=" * 72,
        "DAY 28 - STEP 5",
        "FSM ARCHITECTURE SELECTION ROBUSTNESS REPORT",
        "=" * 72,
        "",
        f"Configurations: {EXPECTED_CONFIGURATIONS}",
        f"Constraint cases: {len(cases)}",
        f"Selection scenarios: {len(SCENARIOS)}",
        f"Total decisions: {len(records)}",
        f"Stable decisions: {stable_count}",
        f"Changed decisions: {changed_count}",
        f"Selection stability: {result['stability_percentage']:.2f}%",
        "",
        "SCENARIO SUMMARY",
        "-" * 72,
    ]

    for scenario in SCENARIOS:
        summary = scenario_summary[scenario]
        lines.extend([
            f"Scenario: {scenario}",
            f"  Original winner: {summary['baseline_winner']}",
            f"  Stable cases: {summary['stable_cases']}",
            f"  Changed cases: {summary['changed_cases']}",
            "",
        ])

    lines.extend([
        "DETAILED CONSTRAINT RESULTS",
        "-" * 72,
    ])

    for row in records:
        state = "STABLE" if row["stable"] else "CHANGED"
        lines.append(
            f"{row['constraint_case']} | "
            f"{row['scenario']} | "
            f"{row['constraint_winner']} | {state}"
        )

    lines.extend([
        "",
        "METHODOLOGY AND LIMITATIONS",
        "-" * 72,
    ])

    for number, limitation in enumerate(
        result["limitations"], start=1
    ):
        lines.append(f"{number}. {limitation}")

    lines.extend([
        "",
        "DAY 28 STEP 5: PASS",
    ])

    OUTPUT_TXT.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )

    print("=" * 64)
    print("DAY 28 - STEP 5")
    print("FSM ARCHITECTURE SELECTION ROBUSTNESS")
    print("=" * 64)
    print(f"CONFIGURATIONS: {EXPECTED_CONFIGURATIONS}")
    print(f"CONSTRAINT CASES: {len(cases)}")
    print(f"SELECTION SCENARIOS: {len(SCENARIOS)}")
    print(f"TOTAL DECISIONS: {len(records)}")
    print(f"STABLE DECISIONS: {stable_count}")
    print(f"CHANGED DECISIONS: {changed_count}")
    print(
        f"SELECTION STABILITY: "
        f"{result['stability_percentage']:.2f}%"
    )

    print("\nGENERATED REPORTS:")
    for path in (OUTPUT_CSV, OUTPUT_JSON, OUTPUT_TXT):
        print(path.relative_to(ROOT))

    print("\nDAY 28 STEP 5: PASS")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(f"DAY 28 STEP 5: FAIL - {exc}", file=sys.stderr)
        sys.exit(1)
