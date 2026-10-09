#!/usr/bin/env python3

"""
Extension Day 3 / Day 27
Step 2: Matched Mealy versus Moore FSM comparison.

Reads existing Day 26 PPA CSV.
Does not modify RTL, synthesis results, or Day 26 reports.
"""

import csv
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path.home() / "Mtech_project" / "AI_RTL_Verification"

INPUT = (
    ROOT
    / "extensions/results/day26/day26_fsm_ppa_summary.csv"
)

OUTPUT = ROOT / "extensions/results/day27"

PATTERNS = ("1011", "10101", "1101")
OVERLAPS = (0, 1)

REQUIRED_COLUMNS = (
    "configuration",
    "area_um2",
    "setup_slack_ns",
    "data_arrival_ns",
    "internal_power_uw",
    "switching_power_uw",
    "leakage_power_uw",
    "total_power_uw",
)

NUMERIC_COLUMNS = REQUIRED_COLUMNS[1:]


def load_data():
    if not INPUT.is_file():
        raise FileNotFoundError(
            f"Day 26 CSV not found: {INPUT}"
        )

    with INPUT.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        if not reader.fieldnames:
            raise ValueError("CSV header is missing")

        missing = [
            name
            for name in REQUIRED_COLUMNS
            if name not in reader.fieldnames
        ]

        if missing:
            raise ValueError(
                "Missing required columns: "
                + ", ".join(missing)
            )

        rows = list(reader)

    if len(rows) != 13:
        raise ValueError(
            f"Expected 13 configurations; found {len(rows)}"
        )

    records = {}

    for row in rows:
        name = row["configuration"].strip()

        if not name:
            raise ValueError("Empty configuration name")

        if name in records:
            raise ValueError(
                f"Duplicate configuration: {name}"
            )

        values = {"configuration": name}

        for column in NUMERIC_COLUMNS:
            try:
                number = float(row[column])
            except (ValueError, TypeError) as exc:
                raise ValueError(
                    f"{name}: invalid {column}"
                ) from exc

            if not math.isfinite(number):
                raise ValueError(
                    f"{name}: nonfinite {column}"
                )

            if column != "setup_slack_ns" and number < 0:
                raise ValueError(
                    f"{name}: negative {column}"
                )

            values[column] = number

        if values["area_um2"] <= 0:
            raise ValueError(
                f"{name}: area must be positive"
            )

        if values["total_power_uw"] <= 0:
            raise ValueError(
                f"{name}: total power must be positive"
            )

        records[name] = values

    return records


def percentage_change(mealy, moore):
    """
    Positive: Moore value is larger.
    Negative: Moore value is smaller.
    """
    if mealy == 0:
        raise ValueError(
            "Cannot calculate change from zero baseline"
        )

    return 100.0 * (moore - mealy) / mealy


def compare_pair(mealy, moore, pattern, overlap):
    result = {
        "pattern": pattern,
        "overlap": overlap,
        "mealy_configuration": mealy["configuration"],
        "moore_configuration": moore["configuration"],
    }

    fields = (
        "area_um2",
        "setup_slack_ns",
        "data_arrival_ns",
        "internal_power_uw",
        "switching_power_uw",
        "leakage_power_uw",
        "total_power_uw",
    )

    for field in fields:
        a = mealy[field]
        b = moore[field]

        result["mealy_" + field] = round(a, 6)
        result["moore_" + field] = round(b, 6)
        result[field + "_difference"] = round(b - a, 6)

        result[field + "_change_pct"] = round(
            percentage_change(a, b), 4
        ) if a != 0 else None

    result["lower_area"] = (
        "Mealy"
        if mealy["area_um2"] < moore["area_um2"]
        else "Moore"
        if moore["area_um2"] < mealy["area_um2"]
        else "Tie"
    )

    result["lower_power"] = (
        "Mealy"
        if mealy["total_power_uw"]
        < moore["total_power_uw"]
        else "Moore"
        if moore["total_power_uw"]
        < mealy["total_power_uw"]
        else "Tie"
    )

    result["higher_setup_slack"] = (
        "Mealy"
        if mealy["setup_slack_ns"]
        > moore["setup_slack_ns"]
        else "Moore"
        if moore["setup_slack_ns"]
        > mealy["setup_slack_ns"]
        else "Tie"
    )

    return result


def save_csv(comparisons):
    path = OUTPUT / "day27_mealy_moore_comparison.csv"

    with path.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=list(comparisons[0].keys())
        )

        writer.writeheader()
        writer.writerows(comparisons)

    return path


def save_json(comparisons):
    path = OUTPUT / "day27_mealy_moore_comparison.json"

    document = {
        "day": 27,
        "step": 2,
        "analysis": "matched_mealy_moore_comparison",
        "technology": "Nangate45 typical",
        "source": str(INPUT.relative_to(ROOT)),
        "generated_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "pair_count": len(comparisons),
        "status": "PASS",
        "limitations": [
            "Pre-layout technology-mapped estimates",
            "Power based on assumed switching activity",
            "Setup slack is not the same as path delay",
            "Data arrival includes external input delay "
            "for input-origin paths",
            "Mealy and Moore detection timing can differ",
            "Cross-variant cycle-level equivalence "
            "has not been established",
        ],
        "comparisons": comparisons,
    }

    path.write_text(
        json.dumps(document, indent=2) + "\n",
        encoding="utf-8"
    )

    return path


def save_text(comparisons):
    path = OUTPUT / "day27_mealy_moore_comparison.txt"

    lines = [
        "=" * 76,
        "DAY 27 - STEP 2",
        "MATCHED MEALY VERSUS MOORE FSM COMPARISON",
        "=" * 76,
        "",
        "Technology: Nangate45 typical",
        "Source: Day 26 consolidated PPA CSV",
        "Matched pairs: 6",
        "",
    ]

    for item in comparisons:
        lines.extend([
            "-" * 76,
            (
                f"PATTERN: {item['pattern']} | "
                f"OVERLAP: {item['overlap']}"
            ),
            "-" * 76,
            (
                "Mealy: "
                + item["mealy_configuration"]
            ),
            (
                "Moore: "
                + item["moore_configuration"]
            ),
            "",
            (
                "Area (um^2): "
                f"Mealy={item['mealy_area_um2']:.3f}, "
                f"Moore={item['moore_area_um2']:.3f}"
            ),
            (
                "Total power (uW): "
                f"Mealy={item['mealy_total_power_uw']:.3f}, "
                f"Moore={item['moore_total_power_uw']:.3f}"
            ),
            (
                "Setup slack (ns): "
                f"Mealy={item['mealy_setup_slack_ns']:.3f}, "
                f"Moore={item['moore_setup_slack_ns']:.3f}"
            ),
            "",
            (
                "Area change (Moore vs Mealy): "
                f"{item['area_um2_change_pct']:+.2f}%"
            ),
            (
                "Power change (Moore vs Mealy): "
                f"{item['total_power_uw_change_pct']:+.2f}%"
            ),
            "",
            "Lower area: " + item["lower_area"],
            "Lower power: " + item["lower_power"],
            (
                "Higher setup slack: "
                + item["higher_setup_slack"]
            ),
            "",
        ])

    lines.extend([
        "=" * 76,
        "INTERPRETATION",
        "=" * 76,
        "Negative area/power change means Moore uses less.",
        "Positive area/power change means Moore uses more.",
        "Higher setup slack indicates greater margin "
        "under the applied timing constraints.",
        "",
        "IMPORTANT LIMITATIONS",
        "- Pre-layout standard-cell measurements.",
        "- Assumed switching activity for power.",
        "- Setup slack must not be called path delay.",
        "- Mealy/Moore output timing may differ.",
        "- Functional equivalence across variants "
        "is not established by PPA comparison.",
        "",
        "DAY 27 STEP 2: PASS",
        "",
    ])

    path.write_text(
        "\n".join(lines),
        encoding="utf-8"
    )

    return path


def main():
    print("=" * 68)
    print("DAY 27 - STEP 2")
    print("MEALY VERSUS MOORE ARCHITECTURAL COMPARISON")
    print("=" * 68)

    records = load_data()
    comparisons = []

    for pattern in PATTERNS:
        for overlap in OVERLAPS:
            mealy_name = (
                f"mealy_{pattern}_overlap_{overlap}"
            )
            moore_name = (
                f"moore_{pattern}_overlap_{overlap}"
            )

            if mealy_name not in records:
                raise ValueError(
                    f"Missing Mealy case: {mealy_name}"
                )

            if moore_name not in records:
                raise ValueError(
                    f"Missing Moore case: {moore_name}"
                )

            item = compare_pair(
                records[mealy_name],
                records[moore_name],
                pattern,
                overlap
            )

            comparisons.append(item)

            print()
            print(
                f"PATTERN={pattern} OVERLAP={overlap}"
            )
            print(
                "Area: "
                f"Mealy={item['mealy_area_um2']:.3f}, "
                f"Moore={item['moore_area_um2']:.3f}"
            )
            print(
                "Power: "
                f"Mealy={item['mealy_total_power_uw']:.3f}, "
                f"Moore={item['moore_total_power_uw']:.3f}"
            )
            print(
                "Slack: "
                f"Mealy={item['mealy_setup_slack_ns']:.3f}, "
                f"Moore={item['moore_setup_slack_ns']:.3f}"
            )

    assert len(comparisons) == 6

    OUTPUT.mkdir(
        parents=True,
        exist_ok=True
    )

    paths = [
        save_csv(comparisons),
        save_json(comparisons),
        save_text(comparisons),
    ]

    print()
    print("=" * 68)
    print("GENERATED REPORTS")
    print("=" * 68)

    for path in paths:
        print(path.relative_to(ROOT))

    print()
    print("MATCHED COMPARISONS: 6")
    print("DAY 27 STEP 2: PASS")


if __name__ == "__main__":
    try:
        main()
    except (
        OSError,
        ValueError,
        AssertionError,
        KeyError
    ) as exc:
        print(
            "DAY 27 STEP 2: FAIL -",
            exc,
            file=sys.stderr
        )
        sys.exit(1)
