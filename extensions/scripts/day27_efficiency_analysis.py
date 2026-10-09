#!/usr/bin/env python3

"""
Extension Day 3 / Day 27 - Step 3

Calculate pre-layout FSM PPA efficiency metrics.

Input:
  extensions/results/day26/day26_fsm_ppa_summary.csv

Outputs:
  extensions/results/day27/day27_efficiency_metrics.csv
  extensions/results/day27/day27_efficiency_metrics.json
  extensions/results/day27/day27_efficiency_report.txt

No RTL modification or resynthesis is performed.
"""

import csv
import json
import math
import sys
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path.home() / "Mtech_project" / "AI_RTL_Verification"

SOURCE = (
    ROOT / "extensions/results/day26"
    / "day26_fsm_ppa_summary.csv"
)

OUTPUT = ROOT / "extensions/results/day27"

REQUIRED = (
    "configuration",
    "area_um2",
    "setup_slack_ns",
    "data_arrival_ns",
    "total_power_uw",
)

EXPECTED_CASES = {
    "fsm_original_1011",
    *{
        f"{architecture}_{pattern}_overlap_{overlap}"
        for architecture in ("mealy", "moore")
        for pattern in ("1011", "10101", "1101")
        for overlap in (0, 1)
    },
}


def load_source():
    if not SOURCE.is_file():
        raise FileNotFoundError(
            f"Source file missing: {SOURCE}"
        )

    with SOURCE.open(
        newline="",
        encoding="utf-8"
    ) as file:
        reader = csv.DictReader(file)

        if reader.fieldnames is None:
            raise ValueError("Missing CSV header")

        missing = [
            name for name in REQUIRED
            if name not in reader.fieldnames
        ]

        if missing:
            raise ValueError(
                "Missing columns: " + ", ".join(missing)
            )

        rows = list(reader)

    if len(rows) != 13:
        raise ValueError(
            f"Expected 13 configurations, got {len(rows)}"
        )

    names = [
        row["configuration"].strip()
        for row in rows
    ]

    if len(set(names)) != 13:
        raise ValueError(
            "Duplicate configuration names detected"
        )

    if set(names) != EXPECTED_CASES:
        missing = sorted(EXPECTED_CASES - set(names))
        extra = sorted(set(names) - EXPECTED_CASES)

        raise ValueError(
            f"Configuration mismatch. "
            f"Missing={missing}; Extra={extra}"
        )

    return rows


def parse_number(row, key):
    name = row["configuration"]

    try:
        value = float(row[key])
    except (TypeError, ValueError) as error:
        raise ValueError(
            f"{name}: invalid {key}"
        ) from error

    if not math.isfinite(value):
        raise ValueError(
            f"{name}: nonfinite {key}"
        )

    return value


def calculate(rows):
    results = []

    for row in rows:
        name = row["configuration"].strip()

        area = parse_number(row, "area_um2")
        arrival = parse_number(
            row, "data_arrival_ns"
        )
        slack = parse_number(
            row, "setup_slack_ns"
        )
        power = parse_number(
            row, "total_power_uw"
        )

        if area <= 0:
            raise ValueError(
                f"{name}: invalid area"
            )

        if arrival <= 0:
            raise ValueError(
                f"{name}: invalid arrival time"
            )

        if power <= 0:
            raise ValueError(
                f"{name}: invalid power"
            )

        if slack < 0:
            raise ValueError(
                f"{name}: negative setup slack"
            )

        # Unit conversion:
        # 1 uW * 1 ns = 1e-15 J = 1 fJ.
        adp = area * arrival
        pdp = power * arrival
        app = area * power

        result = {
            "configuration": name,
            "area_um2": round(area, 6),
            "data_arrival_ns": round(arrival, 6),
            "setup_slack_ns": round(slack, 6),
            "total_power_uw": round(power, 6),
            "arrival_based_adp_um2_ns": round(
                adp, 6
            ),
            "arrival_based_pdp_fj": round(
                pdp, 6
            ),
            "area_power_product_um2_uw": round(
                app, 6
            ),
            "setup_timing_met": True,
        }

        results.append(result)

    return sorted(
        results,
        key=lambda item: item["configuration"]
    )


def save_csv(results):
    path = OUTPUT / "day27_efficiency_metrics.csv"

    with path.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(results[0].keys())
        )
        writer.writeheader()
        writer.writerows(results)

    return path


def save_json(results):
    path = OUTPUT / "day27_efficiency_metrics.json"

    document = {
        "day": 27,
        "step": 3,
        "status": "PASS",
        "generated_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "technology": "Nangate45 typical",
        "source": str(SOURCE.relative_to(ROOT)),
        "configuration_count": len(results),
        "methodology": {
            "adp": (
                "mapped cell area multiplied by "
                "reported data arrival time"
            ),
            "pdp": (
                "estimated total power multiplied by "
                "reported data arrival time"
            ),
            "app": (
                "mapped cell area multiplied by "
                "estimated total power"
            ),
            "pdp_units": "fJ",
            "timing_basis": (
                "reported OpenSTA data arrival time"
            ),
        },
        "limitations": [
            "Pre-layout mapped standard-cell area",
            "Power uses assumed switching activity",
            "Arrival-based ADP/PDP are proxy metrics",
            "Data arrival can include input delay",
            "Different critical-path classes may "
            "not be directly comparable",
            "No measured maximum clock frequency",
            "No post-route parasitics",
            "Cross-variant cycle-level equivalence "
            "has not been established",
        ],
        "records": results,
    }

    path.write_text(
        json.dumps(document, indent=2) + "\n",
        encoding="utf-8"
    )

    return path


def save_text(results):
    path = OUTPUT / "day27_efficiency_report.txt"

    lines = [
        "=" * 110,
        "DAY 27 - FSM ARCHITECTURAL EFFICIENCY REPORT",
        "=" * 110,
        "",
        "Technology: Nangate45 typical",
        "Source: Day 26 PPA measurements",
        "Configurations: 13",
        "",
        (
            f"{'Configuration':29s}"
            f"{'Area':>10s}"
            f"{'Arrival':>11s}"
            f"{'Slack':>10s}"
            f"{'Power':>10s}"
            f"{'ADP':>13s}"
            f"{'PDP':>12s}"
        ),
        "-" * 110,
    ]

    for row in results:
        lines.append(
            f"{row['configuration']:29s}"
            f"{row['area_um2']:10.3f}"
            f"{row['data_arrival_ns']:11.3f}"
            f"{row['setup_slack_ns']:10.3f}"
            f"{row['total_power_uw']:10.3f}"
            f"{row['arrival_based_adp_um2_ns']:13.4f}"
            f"{row['arrival_based_pdp_fj']:12.4f}"
        )

    lowest_area = min(
        results,
        key=lambda r: r["area_um2"]
    )

    lowest_power = min(
        results,
        key=lambda r: r["total_power_uw"]
    )

    lowest_adp = min(
        results,
        key=lambda r: r["arrival_based_adp_um2_ns"]
    )

    lowest_pdp = min(
        results,
        key=lambda r: r["arrival_based_pdp_fj"]
    )

    highest_slack = max(
        results,
        key=lambda r: r["setup_slack_ns"]
    )

    lines.extend([
        "",
        "=" * 110,
        "SUMMARY",
        "=" * 110,
        (
            "Lowest mapped area: "
            + lowest_area["configuration"]
        ),
        (
            "Lowest estimated power: "
            + lowest_power["configuration"]
        ),
        (
            "Lowest arrival-based ADP: "
            + lowest_adp["configuration"]
        ),
        (
            "Lowest arrival-based PDP: "
            + lowest_pdp["configuration"]
        ),
        (
            "Highest setup slack: "
            + highest_slack["configuration"]
        ),
        "",
        "IMPORTANT INTERPRETATION",
        (
            "ADP/PDP use reported arrival time "
            "rather than intrinsic path delay."
        ),
        (
            "Results are exploratory pre-layout "
            "comparison metrics."
        ),
        (
            "Different path types and output "
            "latencies limit direct comparisons."
        ),
        (
            "Power values use assumed switching "
            "activity, not measured VCD/SAIF activity."
        ),
        "",
        "DAY 27 STEP 3: PASS",
        "",
    ])

    path.write_text(
        "\n".join(lines),
        encoding="utf-8"
    )

    return path


def main():
    print("=" * 72)
    print("DAY 27 - STEP 3")
    print("FSM AREA, TIMING AND POWER EFFICIENCY")
    print("=" * 72)

    rows = load_source()
    results = calculate(rows)

    OUTPUT.mkdir(
        parents=True,
        exist_ok=True
    )

    paths = [
        save_csv(results),
        save_json(results),
        save_text(results),
    ]

    print()
    print(
        f"{'Configuration':29s}"
        f"{'ADP (um2*ns)':>16s}"
        f"{'PDP (fJ)':>13s}"
    )
    print("-" * 58)

    for row in results:
        print(
            f"{row['configuration']:29s}"
            f"{row['arrival_based_adp_um2_ns']:16.4f}"
            f"{row['arrival_based_pdp_fj']:13.4f}"
        )

    print()
    print("========== GENERATED REPORTS ==========")

    for path in paths:
        print(path.relative_to(ROOT))

    # Independent checks of generated outputs.
    with paths[0].open(
        newline="",
        encoding="utf-8"
    ) as file:
        csv_rows = list(csv.DictReader(file))

    json_data = json.loads(
        paths[1].read_text(encoding="utf-8")
    )

    assert len(csv_rows) == 13
    assert json_data["configuration_count"] == 13
    assert len(json_data["records"]) == 13
    assert "DAY 27 STEP 3: PASS" in (
        paths[2].read_text(encoding="utf-8")
    )

    print()
    print("CONFIGURATIONS ANALYZED: 13")
    print("CSV VALIDATION: PASS")
    print("JSON VALIDATION: PASS")
    print("TEXT REPORT VALIDATION: PASS")
    print("DAY 27 STEP 3: PASS")


if __name__ == "__main__":
    try:
        main()
    except (
        OSError,
        ValueError,
        KeyError,
        AssertionError
    ) as error:
        print(
            "DAY 27 STEP 3: FAIL -",
            error,
            file=sys.stderr
        )
        sys.exit(1)
