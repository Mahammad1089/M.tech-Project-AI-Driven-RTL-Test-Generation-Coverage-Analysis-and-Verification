
#!/usr/bin/env python3
"""Day 29 Step 5: consolidate and validate saved audit evidence.

Reads existing Day 29 JSON reports without rerunning RTL or EDA tools.
Writes final JSON, CSV, and text summaries.
"""

import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("extensions/results/day29")
ROOT.mkdir(parents=True, exist_ok=True)

STEPS = [
    (1, "Baseline evidence validation",
     "day29_baseline_validation.json", 27),
    (2, "Independent architecture ranking audit",
     "day29_independent_ranking_audit.json", 45),
    (3, "Independent constraint sensitivity audit",
     "day29_independent_sensitivity_audit.json", 216),
    (4, "Cross-report consistency verification",
     "day29_cross_report_verification.json", 63),
]

OUTPUT_JSON = ROOT / "day29_final_summary.json"
OUTPUT_CSV = ROOT / "day29_final_summary.csv"
OUTPUT_TXT = ROOT / "day29_final_summary.txt"


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            h.update(block)
    return h.hexdigest()


def integer_field(data, field):
    value = data.get(field)
    if type(value) is not int or value < 0:
        raise ValueError(
            f"{field} must be a nonnegative integer; received {value!r}"
        )
    return value


def validate_step(step, label, filename, expected_checks):
    path = ROOT / filename
    result = {
        "step": step,
        "description": label,
        "source_file": str(path),
        "status": "FAIL",
        "passed_checks": 0,
        "failed_checks": 0,
        "expected_passed_checks": expected_checks,
        "sha256": None,
        "errors": [],
    }

    if not path.is_file():
        result["errors"].append("Source JSON file is missing")
        return result

    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)

        if not isinstance(data, dict):
            raise ValueError("JSON root must be an object")

        result["sha256"] = digest(path)
        result["passed_checks"] = integer_field(
            data, "passed_checks"
        )
        result["failed_checks"] = integer_field(
            data, "failed_checks"
        )

        if data.get("day") != 29:
            result["errors"].append("Incorrect day value")

        if data.get("step") != step:
            result["errors"].append("Incorrect step value")

        if data.get("status") != "PASS":
            result["errors"].append("Source status is not PASS")

        if result["failed_checks"] != 0:
            result["errors"].append(
                "Source contains failed checks"
            )

        if result["passed_checks"] != expected_checks:
            result["errors"].append(
                f"Expected {expected_checks} passed checks; "
                f"found {result['passed_checks']}"
            )

        if not result["errors"]:
            result["status"] = "PASS"

    except (OSError, ValueError, json.JSONDecodeError) as exc:
        result["errors"].append(str(exc))

    return result


def main():
    print("=" * 70)
    print("DAY 29 STEP 5 - FINAL AUDIT CONSOLIDATION")
    print("=" * 70)

    records = [
        validate_step(step, label, filename, expected)
        for step, label, filename, expected in STEPS
    ]

    all_pass = all(row["status"] == "PASS" for row in records)
    total_passed = sum(row["passed_checks"] for row in records)
    total_failed = sum(row["failed_checks"] for row in records)

    status = "PASS" if all_pass else "FAIL"

    for row in records:
        print(
            f"[{row['status']}] Step {row['step']}: "
            f"{row['description']} | "
            f"passed={row['passed_checks']} "
            f"failed={row['failed_checks']}"
        )
        for error in row["errors"]:
            print(f"       ERROR: {error}")

    summary = {
        "day": 29,
        "step": 5,
        "analysis": "Final saved-evidence consolidation",
        "status": status,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "step_count": len(records),
        "successful_steps": sum(
            row["status"] == "PASS" for row in records
        ),
        "total_reported_passed_checks": total_passed,
        "total_reported_failed_checks": total_failed,
        "checks_are_independent": False,
        "steps": records,
        "methodology": {
            "source": "Existing Day 29 saved audit reports",
            "rtl_modified": False,
            "simulation_rerun": False,
            "synthesis_rerun": False,
            "eda_rerun": False,
            "functional_equivalence_established": False,
            "post_layout_signoff_established": False,
        },
        "limitations": [
            "Validates consistency and declared counts of saved evidence.",
            "Does not independently recompute Step 2 or Step 3 audits.",
            "Check totals may include overlapping verification conditions.",
            "Power estimates assume switching activity.",
            "Reported arrival time is not post-layout signoff timing.",
        ],
    }

    with OUTPUT_JSON.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)
        handle.write("\n")

    with OUTPUT_CSV.open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "step", "description", "status",
                "passed_checks", "failed_checks",
                "expected_passed_checks",
                "source_file", "sha256", "errors",
            ],
        )
        writer.writeheader()
        for row in records:
            writer.writerow({
                **row,
                "errors": "; ".join(row["errors"]),
            })

    lines = [
        "=" * 70,
        "DAY 29 STEP 5 - FINAL AUDIT CONSOLIDATION",
        "=" * 70,
        "",
    ]

    for row in records:
        lines.append(
            f"Step {row['step']}: {row['description']}"
        )
        lines.append(
            f"  Status: {row['status']}"
        )
        lines.append(
            f"  Passed checks: {row['passed_checks']}"
        )
        lines.append(
            f"  Failed checks: {row['failed_checks']}"
        )
        lines.append(
            f"  Source: {row['source_file']}"
        )
        for error in row["errors"]:
            lines.append(f"  ERROR: {error}")
        lines.append("")

    lines.extend([
        f"TOTAL REPORTED PASSED CHECKS: {total_passed}",
        f"TOTAL REPORTED FAILED CHECKS: {total_failed}",
        f"SUCCESSFUL STEPS: {summary['successful_steps']}/4",
        f"FINAL RESULT: {status}",
        "",
        "LIMITATIONS",
        "These checks summarize saved audit evidence.",
        "They are not necessarily independent verification properties.",
        "No RTL, synthesis, simulation, or EDA rerun was performed.",
        "Functional equivalence and physical signoff are not established.",
        "",
        f"DAY 29 STEP 5: {status}",
    ])

    OUTPUT_TXT.write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )

    print()
    print("=" * 70)
    print("DAY 29 STEP 5 SUMMARY")
    print("=" * 70)
    print(f"SUCCESSFUL STEPS: {summary['successful_steps']}/4")
    print(f"REPORTED PASSED CHECKS: {total_passed}")
    print(f"REPORTED FAILED CHECKS: {total_failed}")
    print(f"FINAL RESULT: {status}")
    print()
    print("GENERATED REPORTS:")
    print(OUTPUT_JSON)
    print(OUTPUT_CSV)
    print(OUTPUT_TXT)

    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
