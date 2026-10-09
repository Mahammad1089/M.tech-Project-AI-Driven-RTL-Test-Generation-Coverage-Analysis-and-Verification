#!/usr/bin/env python3

import csv
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd()

LIB = ROOT / (
    "extensions/technology/nangate45/"
    "NangateOpenCellLibrary_typical.lib"
)

PPA = ROOT / "extensions/results/day25/ppa"

OUT = ROOT / (
    "extensions/results/day30/alu_5ff_sensitivity"
)

DESIGNS = {
    "original": "alu",
    "optimized": "alu_opt",
}

OUTPUT_LOAD_FF = 5.0


def fail(message):
    print("[FAIL]", message)
    sys.exit(1)


def read_file(path):
    if not path.is_file() or path.stat().st_size == 0:
        fail(f"Missing or empty file: {path}")

    return path.read_text(
        encoding="utf-8",
        errors="replace"
    )


def extract_slack(text, header, next_header):
    if header not in text:
        fail(f"Missing timing section: {header}")

    section = text.split(header, 1)[1]

    if next_header in section:
        section = section.split(next_header, 1)[0]

    matches = re.findall(
        r"([-+]?\d+(?:\.\d+)?)\s+slack\s+"
        r"\((MET|VIOLATED)\)",
        section,
        re.IGNORECASE
    )

    if not matches:
        fail(f"No timing slack found: {header}")

    if any(status.upper() != "MET"
           for _, status in matches):
        fail(f"Timing violation: {header}")

    return min(float(value) for value, _ in matches)


def extract_power(text):
    match = re.search(
        r"(?m)^\s*Total\s+"
        r"(\S+)\s+(\S+)\s+(\S+)\s+(\S+)",
        text
    )

    if not match:
        fail("OpenSTA total power row missing")

    values = [float(value) * 1e6
              for value in match.groups()]

    if any(value < 0 for value in values):
        fail("Negative power result")

    internal, switching, leakage, total = values

    if abs(
        internal + switching + leakage - total
    ) > 0.03:
        fail("Inconsistent power components")

    return internal, switching, leakage, total


def extract_area(label, top):
    log = read_file(PPA / f"{label}_mapping.log")

    match = re.search(
        rf"Chip area for module\s+"
        rf"['\"]?\\?{re.escape(top)}['\"]?\s*:"
        rf"\s*([0-9.]+)",
        log
    )

    if not match:
        fail(f"Mapped area unavailable: {label}")

    return float(match.group(1))


def analyze(label, top):
    netlist = PPA / f"{label}_mapped.v"

    read_file(netlist)

    tcl_file = OUT / f"{label}_5ff.tcl"
    log_file = OUT / f"{label}_5ff_sta.log"

    # Nangate45 typical Liberty declares capacitance in fF.
    # All timing and power settings match the existing ALU
    # methodology except the explicitly increased output load.

    tcl = f"""
read_liberty {LIB}
read_verilog {netlist}
link_design {top}

create_clock -name virtual_clk -period 10.0

set_input_delay 0.2 -clock virtual_clk [all_inputs]
set_output_delay 0.2 -clock virtual_clk [all_outputs]

set_load {OUTPUT_LOAD_FF} [all_outputs]

puts "========== MAXIMUM DELAY PATHS =========="
report_checks -path_delay max

puts "========== MINIMUM DELAY PATHS =========="
report_checks -path_delay min

set_power_activity -input -activity 0.1 -duty 0.5

puts "========== POWER REPORT =========="
report_power

puts "========== 5FF ANALYSIS COMPLETED =========="
"""

    tcl_file.write_text(tcl, encoding="utf-8")

    print(f"\n========== ANALYZING {label.upper()} ==========")
    print("Top module:", top)
    print("Output load:", OUTPUT_LOAD_FF, "fF")

    try:
        process = subprocess.run(
            ["sta", "-no_init", "-exit", str(tcl_file)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=120
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        fail(f"OpenSTA execution exception: {exc}")

    log = process.stdout + "\n" + process.stderr

    log_file.write_text(log, encoding="utf-8")

    if process.returncode != 0:
        print(log[-2500:])
        fail(f"OpenSTA failed for {label}")

    if re.search(
        r"(?im)^\s*(?:Error:|STA Error:)",
        log
    ):
        print(log[-2500:])
        fail(f"OpenSTA reported errors for {label}")

    if "5FF ANALYSIS COMPLETED" not in log:
        fail(f"Incomplete analysis for {label}")

    setup = extract_slack(
        log,
        "========== MAXIMUM DELAY PATHS ==========",
        "========== MINIMUM DELAY PATHS =========="
    )

    minimum = extract_slack(
        log,
        "========== MINIMUM DELAY PATHS ==========",
        "========== POWER REPORT =========="
    )

    internal, switching, leakage, total = extract_power(log)

    area = extract_area(label, top)

    result = {
        "design": label,
        "top_module": top,
        "output_load_ff": OUTPUT_LOAD_FF,
        "mapped_area_um2": area,
        "setup_slack_ns": setup,
        "minimum_path_slack_ns": minimum,
        "internal_power_uw": internal,
        "switching_power_uw": switching,
        "leakage_power_uw": leakage,
        "total_power_uw": total,
        "timing_status": "MET",
    }

    print("[PASS] OpenSTA execution")
    print("[PASS] Setup timing")
    print(f"Mapped area: {area:.3f} um^2")
    print(f"Setup slack: {setup:.3f} ns")
    print(f"Minimum-path slack: {minimum:.3f} ns")
    print(f"Estimated power: {total:.3f} uW")

    return result


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    print("=" * 68)
    print("DAY 30 STEP 7A-5 - ALU 5 fF LOAD SENSITIVITY")
    print("=" * 68)

    if not shutil.which("sta"):
        fail("OpenSTA command 'sta' unavailable")

    liberty = read_file(LIB)

    match = re.search(
        r"capacitive_load_unit\s*\(\s*"
        r"([0-9.]+)\s*,\s*([a-zA-Z]+)\s*\)",
        liberty,
        re.IGNORECASE
    )

    if not match:
        fail("Liberty capacitance unit unavailable")

    unit_value = float(match.group(1))
    unit_name = match.group(2).lower()

    print("Liberty capacitance unit:",
          unit_value, unit_name)

    if unit_value != 1.0 or unit_name != "ff":
        fail("Expected Nangate45 capacitance unit of 1 fF")

    rows = [
        analyze(label, top)
        for label, top in DESIGNS.items()
    ]

    original, optimized = rows

    area_reduction = (
        (original["mapped_area_um2"]
         - optimized["mapped_area_um2"])
        / original["mapped_area_um2"]
        * 100.0
    )

    power_reduction = (
        (original["total_power_uw"]
         - optimized["total_power_uw"])
        / original["total_power_uw"]
        * 100.0
    )

    slack_change_ps = (
        optimized["setup_slack_ns"]
        - original["setup_slack_ns"]
    ) * 1000.0

    csv_path = OUT / "day30_alu_5ff_comparison.csv"
    json_path = OUT / "day30_alu_5ff_comparison.json"
    md_path = OUT / "day30_alu_5ff_report.md"

    with csv_path.open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(rows[0].keys())
        )
        writer.writeheader()
        writer.writerows(rows)

    report = {
        "status": "PASS",
        "technology": "Nangate45 typical",
        "output_load_ff": OUTPUT_LOAD_FF,
        "clock_period_ns": 10.0,
        "input_delay_ns": 0.2,
        "output_delay_ns": 0.2,
        "power_activity_transitions_per_ns": 0.1,
        "power_duty_cycle": 0.5,
        "results": rows,
        "comparison": {
            "area_reduction_percent": area_reduction,
            "estimated_power_reduction_percent": power_reduction,
            "setup_slack_change_ps": slack_change_ps,
        },
        "limitations": [
            "Pre-layout timing and area",
            "Assumed switching activity",
            "No parasitic extraction",
            "No silicon power measurement",
        ],
    }

    json_path.write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8"
    )

    markdown = f"""# ALU 5 fF Sensitivity Report

## Evaluation

Nangate45 typical, technology-mapped pre-layout.

Output load: **5 fF** per output.

Virtual clock: 10 ns.

Input and output delays: 0.2 ns.

Input activity: 0.1 transitions/ns, duty cycle 0.5.

## Results

| Metric | Original | Optimized |
|---|---:|---:|
| Area (um^2) | {original['mapped_area_um2']:.3f} | {optimized['mapped_area_um2']:.3f} |
| Setup slack (ns) | {original['setup_slack_ns']:.3f} | {optimized['setup_slack_ns']:.3f} |
| Estimated power (uW) | {original['total_power_uw']:.3f} | {optimized['total_power_uw']:.3f} |

## Comparison

Area reduction: {area_reduction:.2f}%

Estimated power reduction: {power_reduction:.2f}%

Setup slack change: {slack_change_ps:.1f} ps

These are pre-layout estimates under specified
constraints, not measurements from silicon.
"""

    md_path.write_text(markdown, encoding="utf-8")

    print("\n========== FINAL 5 fF COMPARISON ==========")
    print(f"AREA REDUCTION: {area_reduction:.2f}%")
    print(f"POWER REDUCTION: {power_reduction:.2f}%")
    print(f"SETUP SLACK CHANGE: {slack_change_ps:.1f} ps")

    print("\nCSV:", csv_path)
    print("JSON:", json_path)
    print("REPORT:", md_path)

    print("\nDAY 30 ALU 5FF SENSITIVITY: PASS")


if __name__ == "__main__":
    main()
