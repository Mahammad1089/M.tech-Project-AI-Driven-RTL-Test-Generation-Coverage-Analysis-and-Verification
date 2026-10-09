#!/usr/bin/env python3

"""
DAY 27 - STEP 4
Pareto-optimal FSM architecture analysis.

Input:
    extensions/results/day27/day27_efficiency_metrics.csv

Outputs:
    extensions/results/day27/day27_pareto_analysis.csv
    extensions/results/day27/day27_pareto_analysis.json
    extensions/results/day27/day27_pareto_report.txt

Objectives to minimize:
    1. Technology-mapped area (um2)
    2. Estimated total power (uW)
    3. Reported data arrival time (ns)

Important:
    Global Pareto comparison is numerical only.
    Controlled comparison is within the same pattern
    and overlap setting.
"""

import csv
import json
import math
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path.home() / "Mtech_project" / "AI_RTL_Verification"

INPUT_FILE = (
    ROOT
    / "extensions/results/day27"
    / "day27_efficiency_metrics.csv"
)

OUTPUT_DIR = ROOT / "extensions/results/day27"

CSV_OUTPUT = OUTPUT_DIR / "day27_pareto_analysis.csv"
JSON_OUTPUT = OUTPUT_DIR / "day27_pareto_analysis.json"
TEXT_OUTPUT = OUTPUT_DIR / "day27_pareto_report.txt"

REQUIRED_COLUMNS = (
    "configuration",
    "area_um2",
    "total_power_uw",
    "data_arrival_ns",
    "setup_slack_ns",
)

OBJECTIVES = (
    "area_um2",
    "total_power_uw",
    "data_arrival_ns",
)

PATTERNS = ("1011", "10101", "1101")

EXPECTED_NAMES = {
    "fsm_original_1011",
    *{
        f"{arch}_{pattern}_overlap_{overlap}"
        for arch in ("mealy", "moore")
        for pattern in PATTERNS
        for overlap in (0, 1)
    },
}


def parse_configuration(name):
    if name == "fsm_original_1011":
        return {
            "architecture": "baseline",
            "pattern": "1011",
            "overlap": "baseline",
            "comparison_group": "baseline_only",
        }

    match = re.fullmatch(
        r"(mealy|moore)_(1011|10101|1101)_overlap_([01])",
        name,
    )

    if match is None:
        raise ValueError(
            f"Unexpected configuration name: {name}"
        )

    architecture, pattern, overlap = match.groups()

    return {
        "architecture": architecture,
        "pattern": pattern,
        "overlap": overlap,
        "comparison_group": (
            f"pattern_{pattern}_overlap_{overlap}"
        ),
    }


def load_data():
    if not INPUT_FILE.is_file():
        raise FileNotFoundError(
            f"Missing Step 3 CSV: {INPUT_FILE}"
        )

    with INPUT_FILE.open(
        newline="",
        encoding="utf-8",
    ) as handle:
        reader = csv.DictReader(handle)

        if reader.fieldnames is None:
            raise ValueError("CSV header is missing")

        missing = [
            field
            for field in REQUIRED_COLUMNS
            if field not in reader.fieldnames
        ]

        if missing:
            raise ValueError(
                f"Missing required CSV columns: {missing}"
            )

        raw_rows = list(reader)

    if len(raw_rows) != 13:
        raise ValueError(
            f"Expected 13 rows; found {len(raw_rows)}"
        )

    records = []

    for raw in raw_rows:
        name = raw["configuration"].strip()

        metadata = parse_configuration(name)

        record = {
            "configuration": name,
            **metadata,
        }

        for field in (
            "area_um2",
            "total_power_uw",
            "data_arrival_ns",
            "setup_slack_ns",
        ):
            try:
                value = float(raw[field])
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    f"{name}: invalid {field}"
                ) from exc

            if not math.isfinite(value):
                raise ValueError(
                    f"{name}: nonfinite {field}"
                )

            record[field] = value

        for field in OBJECTIVES:
            if record[field] <= 0:
                raise ValueError(
                    f"{name}: {field} must be positive"
                )

        records.append(record)

    names = [r["configuration"] for r in records]

    if len(set(names)) != 13:
        raise ValueError(
            "Duplicate configurations found"
        )

    if set(names) != EXPECTED_NAMES:
        missing = sorted(EXPECTED_NAMES - set(names))
        extra = sorted(set(names) - EXPECTED_NAMES)

        raise ValueError(
            f"Configuration mismatch: "
            f"missing={missing}; extra={extra}"
        )

    return sorted(
        records,
        key=lambda r: r["configuration"],
    )


def dominates(candidate, target):
    """
    Candidate dominates target when:
      - candidate is <= target in every objective
      - candidate is < target in at least one objective

    Values are taken from the rounded source CSV.
    No artificial tolerance is introduced.
    """

    no_worse = all(
        candidate[key] <= target[key]
        for key in OBJECTIVES
    )

    strictly_better = any(
        candidate[key] < target[key]
        for key in OBJECTIVES
    )

    return no_worse and strictly_better


def pareto_members(records):
    return {
        record["configuration"]
        for record in records
        if not any(
            dominates(other, record)
            for other in records
            if other["configuration"]
            != record["configuration"]
        )
    }


def analyze(records):
    global_front = pareto_members(records)

    grouped = defaultdict(list)

    for record in records:
        if record["architecture"] != "baseline":
            grouped[record["comparison_group"]].append(
                record
            )

    if len(grouped) != 6:
        raise ValueError(
            f"Expected six comparison groups; "
            f"found {len(grouped)}"
        )

    controlled_fronts = {}

    for group, members in grouped.items():
        architectures = {
            item["architecture"]
            for item in members
        }

        if (
            len(members) != 2
            or architectures != {"mealy", "moore"}
        ):
            raise ValueError(
                f"Invalid group: {group}"
            )

        controlled_fronts[group] = pareto_members(
            members
        )

    results = []

    for record in records:
        name = record["configuration"]
        group = record["comparison_group"]

        global_dominators = sorted(
            other["configuration"]
            for other in records
            if other["configuration"] != name
            and dominates(other, record)
        )

        if record["architecture"] == "baseline":
            controlled_status = "NOT_APPLICABLE"
            controlled_dominators = []
        else:
            members = grouped[group]

            controlled_dominators = sorted(
                other["configuration"]
                for other in members
                if other["configuration"] != name
                and dominates(other, record)
            )

            controlled_status = (
                "PARETO"
                if name in controlled_fronts[group]
                else "DOMINATED"
            )

        results.append({
            **record,
            "global_pareto_status": (
                "PARETO"
                if name in global_front
                else "DOMINATED"
            ),
            "global_dominated_by": global_dominators,
            "controlled_pareto_status": (
                controlled_status
            ),
            "controlled_dominated_by": (
                controlled_dominators
            ),
        })

    return results, grouped


def save_csv(results):
    columns = [
        "configuration",
        "architecture",
        "pattern",
        "overlap",
        "comparison_group",
        "area_um2",
        "total_power_uw",
        "data_arrival_ns",
        "setup_slack_ns",
        "global_pareto_status",
        "global_dominated_by",
        "controlled_pareto_status",
        "controlled_dominated_by",
    ]

    with CSV_OUTPUT.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=columns,
        )

        writer.writeheader()

        for record in results:
            output = dict(record)

            output["global_dominated_by"] = ";".join(
                record["global_dominated_by"]
            )

            output["controlled_dominated_by"] = ";".join(
                record["controlled_dominated_by"]
            )

            writer.writerow(output)


def save_json(results):
    global_front = sorted(
        r["configuration"]
        for r in results
        if r["global_pareto_status"] == "PARETO"
    )

    controlled_fronts = defaultdict(list)

    for record in results:
        if record["controlled_pareto_status"] == "PARETO":
            controlled_fronts[
                record["comparison_group"]
            ].append(record["configuration"])

    document = {
        "day": 27,
        "step": 4,
        "status": "PASS",
        "generated_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "source": str(
            INPUT_FILE.relative_to(ROOT)
        ),
        "configuration_count": len(results),
        "comparison_group_count": 6,
        "objectives_minimized": list(OBJECTIVES),
        "global_pareto_front": global_front,
        "controlled_pareto_fronts": {
            key: sorted(value)
            for key, value in sorted(
                controlled_fronts.items()
            )
        },
        "limitations": [
            "Global comparison includes functionally "
            "different FSM variants",
            "Controlled comparisons match pattern and "
            "overlap but do not establish cycle-level "
            "Mealy/Moore equivalence",
            "Data arrival time is a timing proxy",
            "Power is based on assumed activity",
            "Area and timing are pre-layout estimates",
            "No post-route or VCD/SAIF-based results",
        ],
        "records": results,
    }

    JSON_OUTPUT.write_text(
        json.dumps(document, indent=2) + "\n",
        encoding="utf-8",
    )


def save_text(results, grouped):
    lines = [
        "=" * 90,
        "DAY 27 - STEP 4 - FSM PARETO ANALYSIS",
        "=" * 90,
        "",
        "OBJECTIVES: MINIMIZE AREA, POWER, ARRIVAL TIME",
        "SOURCE: DAY 27 STEP 3 EFFICIENCY METRICS",
        "CONFIGURATIONS: 13",
        "",
        "1. GLOBAL NUMERICAL PARETO ANALYSIS",
        "-" * 90,
    ]

    for record in results:
        lines.append(
            f"{record['configuration']:30s} "
            f"{record['global_pareto_status']}"
        )

        if record["global_dominated_by"]:
            lines.append(
                "    Dominated by: "
                + ", ".join(
                    record["global_dominated_by"]
                )
            )

    lines.extend([
        "",
        "2. CONTROLLED MEALY VS MOORE COMPARISONS",
        "-" * 90,
    ])

    for group in sorted(grouped):
        lines.append("")
        lines.append(f"GROUP: {group}")

        members = [
            record
            for record in results
            if record["comparison_group"] == group
        ]

        for record in members:
            lines.append(
                f"  {record['architecture']:6s} "
                f"area={record['area_um2']:.3f} um2 "
                f"power={record['total_power_uw']:.3f} uW "
                f"arrival={record['data_arrival_ns']:.3f} ns "
                f"status={record['controlled_pareto_status']}"
            )

    lines.extend([
        "",
        "3. METHODOLOGY AND LIMITATIONS",
        "-" * 90,
        "Pareto dominance uses three minimized metrics.",
        "A dominated design is no better in any metric",
        "and strictly worse in at least one metric.",
        "",
        "The baseline is included in global numerical",
        "analysis only, not the controlled comparisons.",
        "",
        "Mealy and Moore designs can have different",
        "output timing and cycle-level semantics.",
        "A numerical Pareto result does not prove",
        "functional interchangeability.",
        "",
        "Timing uses reported data arrival time,",
        "which may include external input delay.",
        "",
        "Power uses assumed switching activity.",
        "These are pre-layout technology-mapped results.",
        "",
        "DAY 27 STEP 4: PASS",
        "",
    ])

    TEXT_OUTPUT.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


def validate_outputs():
    with CSV_OUTPUT.open(
        newline="",
        encoding="utf-8",
    ) as handle:
        csv_records = list(csv.DictReader(handle))

    json_data = json.loads(
        JSON_OUTPUT.read_text(encoding="utf-8")
    )

    text_report = TEXT_OUTPUT.read_text(
        encoding="utf-8"
    )

    if len(csv_records) != 13:
        raise ValueError(
            "Output CSV does not contain 13 records"
        )

    if json_data["configuration_count"] != 13:
        raise ValueError(
            "JSON configuration count mismatch"
        )

    if json_data["comparison_group_count"] != 6:
        raise ValueError(
            "JSON group count mismatch"
        )

    if len(json_data["controlled_pareto_fronts"]) != 6:
        raise ValueError(
            "Missing controlled Pareto group"
        )

    if "DAY 27 STEP 4: PASS" not in text_report:
        raise ValueError(
            "Text report completion marker missing"
        )


def main():
    print("=" * 70)
    print("DAY 27 - STEP 4")
    print("PARETO-OPTIMAL FSM ARCHITECTURE ANALYSIS")
    print("=" * 70)

    records = load_data()

    results, grouped = analyze(records)

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    save_csv(results)
    save_json(results)
    save_text(results, grouped)

    validate_outputs()

    global_front = [
        r["configuration"]
        for r in results
        if r["global_pareto_status"] == "PARETO"
    ]

    print()
    print("GLOBAL NUMERICAL PARETO FRONT:")

    for name in global_front:
        print("  ", name)

    print()
    print("CONTROLLED COMPARISONS:")

    for group in sorted(grouped):
        members = [
            r
            for r in results
            if r["comparison_group"] == group
        ]

        winners = [
            r["configuration"]
            for r in members
            if r["controlled_pareto_status"] == "PARETO"
        ]

        print(
            f"  {group}: "
            + ", ".join(winners)
        )

    print()
    print("========== GENERATED REPORTS ==========")

    for path in (
        CSV_OUTPUT,
        JSON_OUTPUT,
        TEXT_OUTPUT,
    ):
        print(path.relative_to(ROOT))

    print()
    print("CONFIGURATIONS ANALYZED: 13")
    print("CONTROLLED COMPARISON GROUPS: 6")
    print("CSV VALIDATION: PASS")
    print("JSON VALIDATION: PASS")
    print("TEXT REPORT VALIDATION: PASS")
    print("DAY 27 STEP 4: PASS")


if __name__ == "__main__":
    try:
        main()
    except (
        OSError,
        ValueError,
        KeyError,
    ) as error:
        print(
            "DAY 27 STEP 4: FAIL -",
            error,
            file=sys.stderr,
        )
        sys.exit(1)
