#!/usr/bin/env python3

import csv
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path.cwd()
PPA = ROOT / "extensions/results/day25/ppa"
OUT = ROOT / "extensions/results/day30/alu_final_report"
LIB = ROOT / (
    "extensions/technology/nangate45/"
    "NangateOpenCellLibrary_typical.lib"
)
SDC = ROOT / "extensions/scripts/alu_timing.sdc"
EQUIV = ROOT / "extensions/results/day25/alu_equivalence.log"

DESIGNS = {
    "original": "alu",
    "optimized": "alu_opt",
}


def fail(message):
    print("[FAIL]", message)
    sys.exit(1)


def read_required(path):
    if not path.is_file() or path.stat().st_size == 0:
        fail(f"Missing or empty file: {path}")

    return path.read_text(
        encoding="utf-8",
        errors="replace"
    )


def last_number(text, expression, label):
    matches = re.findall(
        expression,
        text,
        re.IGNORECASE | re.MULTILINE
    )

    if not matches:
        fail(f"Cannot extract {label}")

    return float(matches[-1])


def extract_slack(text, section_start, section_end=None):
    if section_start not in text:
        fail(f"Missing timing section: {section_start}")

    section = text.split(section_start, 1)[1]

    if section_end:
        section = section.split(section_end, 1)[0]

    matches = re.findall(
        r"([-+]?\d+(?:\.\d+)?)\s+slack\s+"
        r"\((MET|VIOLATED)\)",
        section,
        re.IGNORECASE
    )

    if not matches:
        fail(f"No slack values in {section_start}")

    values = [float(x[0]) for x in matches]
    states = [x[1].upper() for x in matches]

    if any(state != "MET" for state in states):
        fail(f"Timing violation in {section_start}")

    return min(values)


def parse_power(text, label):
    if "POWER ANALYSIS COMPLETED" not in text:
        fail(f"{label}: missing power completion marker")

    match = re.search(
        r"(?m)^\s*Total\s+"
        r"(\S+)\s+(\S+)\s+(\S+)\s+(\S+)",
        text
    )

    if not match:
        fail(f"{label}: cannot find total power row")

    try:
        values = [float(v) for v in match.groups()]
    except ValueError:
        fail(f"{label}: invalid power numbers")

    if any(v < 0 for v in values):
        fail(f"{label}: negative power result")

    internal, switching, leakage, total = [
        value * 1e6 for value in values
    ]

    if abs(
        internal + switching + leakage - total
    ) > 0.03:
        fail(f"{label}: inconsistent power totals")

    return {
        "internal_power_uw": internal,
        "switching_power_uw": switching,
        "leakage_power_uw": leakage,
        "total_power_uw": total,
    }


def parse_design(label, top):
    mapping = read_required(
        PPA / f"{label}_mapping.log"
    )
    timing = read_required(
        PPA / f"{label}_timing.log"
    )
    power = read_required(
        PPA / f"{label}_power.log"
    )
    netlist = read_required(
        PPA / f"{label}_mapped.v"
    )

    if not re.search(
        rf"\bmodule\s+{re.escape(top)}\b",
        netlist
    ):
        fail(f"{label}: mapped top module not found")

    for name, log in (
        ("mapping", mapping),
        ("timing", timing),
        ("power", power),
    ):
        if re.search(
            r"(?im)^\s*(?:Error:|STA Error:|ERROR:)",
            log
        ):
            fail(f"{label}: error found in {name} log")

    area = last_number(
        mapping,
        rf"Chip area for module\s+"
        rf"['\"]?\\?{re.escape(top)}['\"]?\s*:"
        rf"\s*([0-9]+(?:\.[0-9]+)?)",
        f"{label} mapped area"
    )

    cells = int(last_number(
        mapping,
        r"Number of cells:\s*(\d+)",
        f"{label} mapped cell count"
    ))

    if area <= 0 or cells <= 0:
        fail(f"{label}: invalid mapped area or cell count")

    if "TIMING CHECK COMPLETE" not in timing:
        fail(f"{label}: timing completion marker missing")

    setup_slack = extract_slack(
        timing,
        "========== MAXIMUM DELAY PATHS ==========",
        "========== MINIMUM DELAY PATHS =========="
    )

    minimum_slack = extract_slack(
        timing,
        "========== MINIMUM DELAY PATHS ==========",
        "========== TIMING CHECK COMPLETE =========="
    )

    if setup_slack < 0:
        fail(f"{label}: setup timing failed")

    result = {
        "design": label,
        "top_module": top,
        "area_um2": area,
        "mapped_cell_count": cells,
        "setup_slack_ns": setup_slack,
        "minimum_path_slack_ns": minimum_slack,
        "timing_status": "MET",
    }

    result.update(parse_power(power, label))
    return result


def percentage_reduction(original, optimized):
    if original <= 0:
        fail("Invalid baseline for percentage calculation")

    return (original - optimized) / original * 100.0


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("DAY 30 STEP 7A-4 — FINAL ALU PPA REPORT")
    print("=" * 70)

    read_required(LIB)
    sdc_text = read_required(SDC)
    equiv_text = read_required(EQUIV)

    print("\n========== EQUIVALENCE VALIDATION ==========")

    checks = {}

    for name, expression in [
        ("total", r"TOTAL CHECKS\s*:\s*(\d+)"),
        ("passed", r"PASSED CHECKS\s*:\s*(\d+)"),
        ("failed", r"FAILED CHECKS\s*:\s*(\d+)"),
    ]:
        checks[name] = int(last_number(
            equiv_text,
            expression,
            name
        ))

    if (
        checks["total"] != 2048
        or checks["passed"] != 2048
        or checks["failed"] != 0
        or "DAY 25 ALU EQUIVALENCE: PASS" not in equiv_text
    ):
        fail("ALU equivalence evidence is not 2048/2048 PASS")

    print("[PASS] 2048/2048 equivalent test cases")

    print("\n========== LIBRARY CAPACITANCE UNIT ==========")

    lib_text = read_required(LIB)

    unit_match = re.search(
        r"capacitive_load_unit\s*\(\s*"
        r"([0-9.]+)\s*,\s*([a-zA-Z]+)\s*\)",
        lib_text,
        re.IGNORECASE
    )

    library_cap_unit = (
        f"{unit_match.group(1)} {unit_match.group(2)}"
        if unit_match else "NOT IDENTIFIED"
    )

    print("Library capacitance unit:", library_cap_unit)

    load_match = re.search(
        r"set_load\s+([0-9.]+)\s+\[all_outputs\]",
        sdc_text
    )

    specified_load = (
        float(load_match.group(1))
        if load_match else None
    )

    print("SDC output load:", specified_load)

    if unit_match and specified_load is not None:
        multiplier = float(unit_match.group(1))
        unit_name = unit_match.group(2).lower()

        if unit_name == "pf":
            load_ff = specified_load * multiplier * 1000
            print(f"Equivalent output load: {load_ff:g} fF")
        elif unit_name == "ff":
            load_ff = specified_load * multiplier
            print(f"Equivalent output load: {load_ff:g} fF")
        else:
            print(
                "[REVIEW] Convert using library "
                "capacitance unit"
            )

    print("\n========== MAPPED PPA VALIDATION ==========")

    rows = []

    for label, top in DESIGNS.items():
        result = parse_design(label, top)
        rows.append(result)

        print(f"\n[PASS] {label.upper()} ALU")
        print(f"  Area: {result['area_um2']:.3f} um^2")
        print(f"  Cells: {result['mapped_cell_count']}")
        print(
            f"  Setup slack: "
            f"{result['setup_slack_ns']:.3f} ns"
        )
        print(
            f"  Minimum-path slack: "
            f"{result['minimum_path_slack_ns']:.3f} ns"
        )
        print(
            f"  Estimated power: "
            f"{result['total_power_uw']:.3f} uW"
        )

    original, optimized = rows

    area_reduction = percentage_reduction(
        original["area_um2"],
        optimized["area_um2"]
    )

    power_reduction = percentage_reduction(
        original["total_power_uw"],
        optimized["total_power_uw"]
    )

    slack_change = (
        optimized["setup_slack_ns"]
        - original["setup_slack_ns"]
    )

    comparison = {
        "area_reduction_percent": area_reduction,
        "estimated_power_reduction_percent": power_reduction,
        "setup_slack_improvement_ns": slack_change,
        "setup_slack_improvement_ps": slack_change * 1000,
        "cell_count_reduction": (
            original["mapped_cell_count"]
            - optimized["mapped_cell_count"]
        ),
    }

    csv_file = OUT / "day30_alu_ppa_comparison.csv"
    json_file = OUT / "day30_alu_final_report.json"
    md_file = OUT / "day30_alu_final_report.md"

    with csv_file.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(rows[0].keys())
        )
        writer.writeheader()
        writer.writerows(rows)

    report = {
        "title": "Day 30 Final ALU PPA Verification",
        "generated_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "status": "PASS",
        "equivalence_checks": checks,
        "technology": "Nangate45 typical",
        "method": "Pre-layout technology-mapped analysis",
        "clock": "10 ns virtual clock",
        "sd c_output_load".replace(" ", ""): specified_load,
        "liberty_capacitance_unit": library_cap_unit,
        "power_activity": (
            "0.1 transitions/ns input activity, "
            "duty cycle 0.5"
        ),
        "results": rows,
        "comparison": comparison,
        "limitations": [
            "Pre-layout cell area, not placed die area",
            "Timing depends on virtual-clock constraints",
            "Power uses assumed input activity",
            "No waveform-based power measurement",
            "No routed parasitics included",
        ],
    }

    json_file.write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8"
    )

    markdown = f"""# Day 30 — Final ALU PPA Report

## Functional verification

Original and optimized ALUs passed
**{checks['passed']}/{checks['total']} equivalence checks**.

## Technology-mapped PPA

| Metric | Original | Optimized |
|---|---:|---:|
| Cell area (µm²) | {original['area_um2']:.3f} | {optimized['area_um2']:.3f} |
| Cell count | {original['mapped_cell_count']} | {optimized['mapped_cell_count']} |
| Setup slack (ns) | {original['setup_slack_ns']:.3f} | {optimized['setup_slack_ns']:.3f} |
| Minimum-path slack (ns) | {original['minimum_path_slack_ns']:.3f} | {optimized['minimum_path_slack_ns']:.3f} |
| Estimated power (µW) | {original['total_power_uw']:.3f} | {optimized['total_power_uw']:.3f} |

## Optimization results

- Cell area reduction: **{area_reduction:.2f}%**
- Estimated power reduction: **{power_reduction:.2f}%**
- Setup slack improvement: **{slack_change * 1000:.0f} ps**
- Mapped cell count reduction: **{comparison['cell_count_reduction']}**

## Evaluation conditions

- Library: Nangate45 typical
- Analysis: technology-mapped, pre-layout
- Virtual clock: 10 ns
- Input/output delays: 0.2 ns
- SDC load: {specified_load}
- Library capacitance unit: {library_cap_unit}
- Assumed input activity: 0.1 transitions/ns
- Duty cycle: 0.5

## Conclusion

The optimized ALU maintains functional equivalence
while reducing mapped cell area and estimated power.
Both designs meet the evaluated setup constraints.

These are pre-layout estimates, not physical
implementation or measured silicon results.
"""

    md_file.write_text(
        markdown,
        encoding="utf-8"
    )

    print("\n========== FINAL ALU COMPARISON ==========")
    print(f"AREA REDUCTION: {area_reduction:.2f}%")
    print(f"POWER REDUCTION: {power_reduction:.2f}%")
    print(
        f"SETUP SLACK IMPROVEMENT: "
        f"{slack_change * 1000:.0f} ps"
    )
    print(
        "MAPPED CELL COUNT REDUCTION:",
        comparison["cell_count_reduction"]
    )

    print("\n========== GENERATED REPORTS ==========")
    print("CSV:", csv_file)
    print("JSON:", json_file)
    print("MARKDOWN:", md_file)

    print("\nDAY 30 FINAL ALU PPA REPORT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
