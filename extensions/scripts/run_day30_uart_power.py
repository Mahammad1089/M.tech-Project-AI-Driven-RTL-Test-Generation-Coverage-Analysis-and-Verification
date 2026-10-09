#!/usr/bin/env python3

import csv
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path.home() / "Mtech_project" / "AI_RTL_Verification"
PPA = ROOT / "extensions/results/day30/uart/ppa"
LIB = (
    ROOT
    / "extensions/technology/nangate45"
    / "NangateOpenCellLibrary_typical.lib"
)

DESIGNS = [
    ("baseline_tx", "uart_tx"),
    ("optimized_tx", "uart_tx_opt"),
    ("baseline_rx", "uart_rx"),
    ("optimized_rx", "uart_rx_opt"),
]

CLOCK_PERIOD_NS = 10.0
INPUT_ACTIVITY_PER_CYCLE = 1.0
INPUT_ACTIVITY_PER_NS = (
    INPUT_ACTIVITY_PER_CYCLE / CLOCK_PERIOD_NS
)
INPUT_DUTY = 0.5
OUTPUT_LOAD_FF = 5.0

NUMBER = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?"

TOTAL_PATTERN = re.compile(
    rf"(?m)^\s*Total\s+"
    rf"({NUMBER})\s+"
    rf"({NUMBER})\s+"
    rf"({NUMBER})\s+"
    rf"({NUMBER})(?:\s|$)"
)

ERROR_PATTERN = re.compile(
    r"(?im)^\s*(?:Error:|STA Error:)"
)


def build_tcl(top, netlist):
    return f"""
read_liberty {LIB}
read_verilog {netlist}
link_design {top}

create_clock -name uart_clk -period {CLOCK_PERIOD_NS} [get_ports clk]

set_load {OUTPUT_LOAD_FF} [all_outputs]

# One assumed transition per 10 ns clock cycle.
# This is 0.1 transitions/ns for the input signals.
set_power_activity -input -activity {INPUT_ACTIVITY_PER_CYCLE} -duty {INPUT_DUTY}

# Treat synchronous reset as inactive in steady-state operation.
set_power_activity -input_ports [get_ports rst] -activity 0.0 -duty 0.0

puts "UART_POWER_REPORT_BEGIN"
report_power -digits 6
puts "UART_POWER_REPORT_END"
puts "UART_POWER_ANALYSIS_COMPLETE"
"""


def measure(name, top):
    print(
        f"\n========== UART POWER: {name.upper()} ==========",
        flush=True,
    )

    netlist = PPA / f"{name}_mapped.v"
    tcl_file = PPA / f"{name}_power.tcl"
    log_file = PPA / f"{name}_power.log"

    if not netlist.is_file():
        print("[FAIL] Missing mapped netlist:", netlist)
        return None

    tcl_file.write_text(
        build_tcl(top, netlist),
        encoding="utf-8",
    )

    try:
        result = subprocess.run(
            ["sta", "-exit", str(tcl_file)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        print("[FAIL] OpenSTA execution:", exc)
        return None

    output = result.stdout + "\n" + result.stderr

    log_file.write_text(
        output,
        encoding="utf-8",
    )

    if result.returncode != 0 or ERROR_PATTERN.search(output):
        print("[FAIL] OpenSTA reported errors")

        for line in output.splitlines():
            if ERROR_PATTERN.search(line):
                print(line)

        print("Full log:", log_file)
        return None

    for line in output.splitlines():
        if re.match(r"^\s*Warning:", line):
            print("[WARNING]", line.strip())

    markers = [
        "UART_POWER_REPORT_BEGIN",
        "UART_POWER_REPORT_END",
        "UART_POWER_ANALYSIS_COMPLETE",
    ]

    if any(marker not in output for marker in markers):
        print("[FAIL] Power report markers missing")
        print("Full log:", log_file)
        return None

    section = output.split(
        "UART_POWER_REPORT_BEGIN", 1
    )[1].split(
        "UART_POWER_REPORT_END", 1
    )[0]

    matches = TOTAL_PATTERN.findall(section)

    if len(matches) != 1:
        print("[FAIL] Expected exactly one total-power row")
        print(section[-3000:])
        print("Full log:", log_file)
        return None

    internal, switching, leakage, total = [
        float(value) for value in matches[0]
    ]

    if min(internal, switching, leakage, total) < 0:
        print("[FAIL] Negative power value detected")
        return None

    if total <= 0:
        print("[FAIL] Nonpositive total power")
        return None

    component_sum = internal + switching + leakage

    # Allow small differences from OpenSTA report rounding.
    tolerance = max(total * 0.01, 1e-12)

    if abs(component_sum - total) > tolerance:
        print("[FAIL] Inconsistent power components")
        print("Sum:", component_sum)
        print("Reported total:", total)
        return None

    record = {
        "design": name,
        "top_module": top,
        "technology": "Nangate45 typical",
        "clks_per_bit": 16,
        "clock_period_ns": CLOCK_PERIOD_NS,
        "assumed_input_transitions_per_cycle": INPUT_ACTIVITY_PER_CYCLE,
        "assumed_input_transitions_per_ns": INPUT_ACTIVITY_PER_NS,
        "output_load_ff": OUTPUT_LOAD_FF,
        "internal_power_uw": internal * 1e6,
        "switching_power_uw": switching * 1e6,
        "leakage_power_uw": leakage * 1e6,
        "total_power_uw": total * 1e6,
        "power_log": str(log_file.relative_to(ROOT)),
    }

    print("[PASS] Power estimation completed")
    print(f"Internal power:  {record['internal_power_uw']:.6f} uW")
    print(f"Switching power: {record['switching_power_uw']:.6f} uW")
    print(f"Leakage power:   {record['leakage_power_uw']:.6f} uW")
    print(f"Total power:     {record['total_power_uw']:.6f} uW")
    print("Log:", log_file)

    return record


def main():
    PPA.mkdir(parents=True, exist_ok=True)

    if not LIB.is_file():
        print("[FAIL] Missing Nangate45 Liberty library")
        return 1

    print("=" * 65)
    print("DAY 30 STEP 4E-5 - UART POWER ESTIMATION")
    print("=" * 65)

    records = []
    failures = []

    for name, top in DESIGNS:
        record = measure(name, top)

        if record is None:
            failures.append(name)
        else:
            records.append(record)

    if failures or len(records) != 4:
        print("\n========== FINAL RESULT ==========")
        print("[FAIL] UART power analysis incomplete")
        print("Failed designs:", ", ".join(failures))
        return 1

    csv_path = PPA / "day30_uart_power_comparison.csv"
    json_path = PPA / "day30_uart_power_comparison.json"

    with csv_path.open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(records[0].keys()),
        )
        writer.writeheader()
        writer.writerows(records)

    by_name = {
        record["design"]: record
        for record in records
    }

    comparisons = []

    print("\n========== UART POWER COMPARISON ==========")

    for block in ("tx", "rx"):
        baseline = by_name[f"baseline_{block}"]
        optimized = by_name[f"optimized_{block}"]

        baseline_power = baseline["total_power_uw"]
        optimized_power = optimized["total_power_uw"]

        reduction = (
            (baseline_power - optimized_power)
            / baseline_power * 100
        )

        print(f"\nUART {block.upper()}")
        print(f"Baseline power:  {baseline_power:.6f} uW")
        print(f"Optimized power: {optimized_power:.6f} uW")
        print(f"Power reduction: {reduction:+.2f}%")

        if reduction > 0:
            print("[RESULT] Estimated power decreased")
        elif reduction < 0:
            print("[RESULT] Estimated power increased")
        else:
            print("[RESULT] Estimated power unchanged")

        comparisons.append({
            "block": block.upper(),
            "baseline_power_uw": baseline_power,
            "optimized_power_uw": optimized_power,
            "power_reduction_percent": reduction,
        })

    baseline_combined = sum(
        by_name[f"baseline_{block}"]["total_power_uw"]
        for block in ("tx", "rx")
    )

    optimized_combined = sum(
        by_name[f"optimized_{block}"]["total_power_uw"]
        for block in ("tx", "rx")
    )

    combined_reduction = (
        (baseline_combined - optimized_combined)
        / baseline_combined * 100
    )

    print("\nUART TX + RX COMBINED")
    print(f"Baseline:  {baseline_combined:.6f} uW")
    print(f"Optimized: {optimized_combined:.6f} uW")
    print(f"Reduction: {combined_reduction:+.2f}%")

    report = {
        "status": "ANALYSIS_COMPLETED",
        "scope": "Pre-layout, assumed-activity power estimation",
        "technology": "Nangate45 typical",
        "clock_period_ns": CLOCK_PERIOD_NS,
        "assumed_input_activity_transitions_per_ns": INPUT_ACTIVITY_PER_NS,
        "reset_activity": 0.0,
        "output_load_ff": OUTPUT_LOAD_FF,
        "records": records,
        "comparisons": comparisons,
        "combined": {
            "baseline_power_uw": baseline_combined,
            "optimized_power_uw": optimized_combined,
            "power_reduction_percent": combined_reduction,
        },
        "limitations": [
            "Switching activity is assumed, not measured from VCD or SAIF",
            "Actual UART traffic and idle intervals are not modeled",
            "No routed interconnect parasitics",
            "No physical clock tree",
            "Values depend on assumed activity and output load",
            "Mapped design uses default CLKS_PER_BIT=16",
        ],
    }

    json_path.write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
    )

    print("\n========== FINAL POWER VALIDATION ==========")
    print("[PASS] Power reports generated for four designs")
    print("CSV:", csv_path)
    print("JSON:", json_path)
    print("DAY 30 UART POWER ESTIMATION: COMPLETED")

    return 0


if __name__ == "__main__":
    sys.exit(main())
