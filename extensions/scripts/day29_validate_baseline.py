
#!/usr/bin/env python3
"""
Extension Day 5 / Execution Day 29
Step 1 - Baseline Evidence Validation

Read-only validation of Day 26, 27 and 28 source reports.
Writes new evidence only to extensions/results/day29.
"""

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "extensions" / "results"
OUT = RESULTS / "day29"

SOURCE_FILES = {
    "day26_ppa_csv":
        RESULTS / "day26" / "day26_fsm_ppa_summary.csv",
    "day27_efficiency_csv":
        RESULTS / "day27" / "day27_efficiency_metrics.csv",
    "day27_pareto_json":
        RESULTS / "day27" / "day27_pareto_analysis.json",
    "day28_selection_json":
        RESULTS / "day28" / "day28_architecture_selection.json",
    "day28_sensitivity_json":
        RESULTS / "day28" / "day28_constraint_sensitivity.json",
    "day28_robustness_json":
        RESULTS / "day28" / "day28_architecture_robustness.json",
}

OUTPUT_JSON = OUT / "day29_baseline_validation.json"
OUTPUT_TXT = OUT / "day29_baseline_validation.txt"

EXPECTED_CONFIGURATIONS = 13
EXPECTED_SCENARIOS = 4
EXPECTED_CONSTRAINT_CASES = 8
EXPECTED_DECISIONS = 32


def read_csv(path):
    with path.open(
        "r", newline="", encoding="utf-8"
    ) as handle:
        reader = csv.DictReader(handle)
        return list(reader), reader.fieldnames or []


def read_json(path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    checks = []
    failures = []

    def check(condition, description):
        checks.append({
            "description": description,
            "status": "PASS" if condition else "FAIL",
        })

        label = "PASS" if condition else "FAIL"
        print(f"[{label}] {description}")

        if not condition:
            failures.append(description)

    print("=" * 70)
    print("DAY 29 - STEP 1")
    print("BASELINE EVIDENCE VALIDATION")
    print("=" * 70)

    for name, path in SOURCE_FILES.items():
        check(
            path.is_file() and path.stat().st_size > 0,
            f"Source available: {name}"
        )

    loaded = {}

    for name, path in SOURCE_FILES.items():
        if not path.is_file():
            continue

        try:
            if path.suffix == ".json":
                loaded[name] = read_json(path)
                check(
                    isinstance(loaded[name], dict),
                    f"Valid JSON object: {name}"
                )
            else:
                rows, columns = read_csv(path)
                loaded[name] = {
                    "rows": rows,
                    "columns": columns,
                }
                check(
                    bool(rows) and bool(columns),
                    f"Readable nonempty CSV: {name}"
                )
        except (OSError, ValueError, csv.Error) as exc:
            check(False, f"Cannot read {name}: {exc}")

    day26 = loaded.get("day26_ppa_csv")
    day27 = loaded.get("day27_efficiency_csv")

    if day26:
        check(
            len(day26["rows"]) == EXPECTED_CONFIGURATIONS,
            "Day 26 PPA CSV contains 13 configurations"
        )
        check(
            "configuration" in day26["columns"],
            "Day 26 PPA CSV has configuration column"
        )

    if day27:
        check(
            len(day27["rows"]) == EXPECTED_CONFIGURATIONS,
            "Day 27 efficiency CSV contains 13 configurations"
        )
        check(
            "configuration" in day27["columns"],
            "Day 27 efficiency CSV has configuration column"
        )

    if day26 and day27:
        day26_names = {
            row["configuration"]
            for row in day26["rows"]
            if "configuration" in row
        }

        day27_names = {
            row["configuration"]
            for row in day27["rows"]
            if "configuration" in row
        }

        check(
            day26_names == day27_names
            and len(day26_names) == EXPECTED_CONFIGURATIONS,
            "Day 26 and Day 27 configuration sets match"
        )

    for name in (
        "day27_pareto_json",
        "day28_selection_json",
        "day28_sensitivity_json",
        "day28_robustness_json",
    ):
        data = loaded.get(name)

        if isinstance(data, dict):
            check(
                data.get("status") == "PASS",
                f"Source report status PASS: {name}"
            )

    selection = loaded.get("day28_selection_json")
    sensitivity = loaded.get("day28_sensitivity_json")
    robustness = loaded.get("day28_robustness_json")

    if isinstance(selection, dict):
        check(
            selection.get("configuration_count")
            == EXPECTED_CONFIGURATIONS,
            "Day 28 selection contains 13 configurations"
        )

        check(
            selection.get("scenario_count")
            == EXPECTED_SCENARIOS,
            "Day 28 selection contains four scenarios"
        )

    if isinstance(sensitivity, dict):
        check(
            sensitivity.get("constraint_case_count")
            == EXPECTED_CONSTRAINT_CASES,
            "Day 28 sensitivity contains eight cases"
        )

    if isinstance(robustness, dict):
        check(
            robustness.get("total_decisions")
            == EXPECTED_DECISIONS,
            "Day 28 robustness contains 32 decisions"
        )

        check(
            robustness.get("stable_decisions")
            == EXPECTED_DECISIONS,
            "Day 28 reports 32 stable decisions"
        )

        check(
            robustness.get("changed_decisions") == 0,
            "Day 28 reports zero changed decisions"
        )

    status = "PASS" if not failures else "FAIL"

    report = {
        "day": 29,
        "step": 1,
        "analysis": "baseline_evidence_validation",
        "status": status,
        "passed_checks": len(checks) - len(failures),
        "failed_checks": len(failures),
        "source_files": {
            name: str(path.relative_to(ROOT))
            for name, path in SOURCE_FILES.items()
        },
        "checks": checks,
        "limitations": [
            "Validates report presence and selected metadata.",
            "Does not independently recompute PPA values.",
            "Does not establish functional equivalence.",
            "Does not perform simulation or synthesis.",
        ],
    }

    OUTPUT_JSON.write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
    )

    lines = [
        "DAY 29 - STEP 1 BASELINE VALIDATION",
        "=" * 60,
    ]

    for item in checks:
        lines.append(
            f"[{item['status']}] {item['description']}"
        )

    lines.extend([
        "",
        f"PASSED CHECKS: {report['passed_checks']}",
        f"FAILED CHECKS: {report['failed_checks']}",
        f"FINAL STATUS: {status}",
    ])

    OUTPUT_TXT.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )

    print("\n" + "=" * 70)
    print("DAY 29 STEP 1 SUMMARY")
    print("=" * 70)
    print(f"PASSED CHECKS: {report['passed_checks']}")
    print(f"FAILED CHECKS: {report['failed_checks']}")
    print(f"FINAL STATUS: {status}")
    print(f"JSON REPORT: {OUTPUT_JSON.relative_to(ROOT)}")
    print(f"TEXT REPORT: {OUTPUT_TXT.relative_to(ROOT)}")

    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(
            f"DAY 29 STEP 1: FAIL - {exc}",
            file=sys.stderr,
        )
        sys.exit(1)
