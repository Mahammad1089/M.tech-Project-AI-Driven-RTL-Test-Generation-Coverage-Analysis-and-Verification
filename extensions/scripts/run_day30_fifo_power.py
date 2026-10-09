#!/usr/bin/env python3

import csv
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path.home() / "Mtech_project" / "AI_RTL_Verification"

OUT = ROOT / "extensions/results/day30/fifo_ppa"

LIB = (
    ROOT / "extensions/technology/nangate45"
    / "NangateOpenCellLibrary_typical.lib"
)

CONFIGURATIONS = [
    ("w8_d4", 8, 4, 2),
    ("w8_d8", 8, 8, 3),
    ("w16_d4", 16, 4, 2),
    ("w8_d16", 8, 16, 4),
]

DESIGNS = [
    ("baseline", "fifo"),
    ("optimized", "fifo_opt"),
]

CLOCK_PERIOD_NS = 10.0
INPUT_ACTIVITY_PER_CYCLE = 1.0
INPUT_DUTY = 0.5
OUTPUT_LOAD_FF = 5.0

NUMBER = (
    r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)"
    r"(?:[eE][+-]?\d+)?"
)

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

create_clock -name fifo_clk -period {CLOCK_PERIOD_NS} [get_ports clk]

set_load {OUTPUT_LOAD_FF} [all_outputs]

# Assumed input activity:
# 1 transition/clock cycle = 0.1 transitions/ns.
set_power_activity -input -activity {INPUT_ACTIVITY_PER_CYCLE} -duty {INPUT_DUTY}

# Reset is considered inactive during steady-state operation.
set_power_activity -input_ports [get_ports rst] -activity 0.0 -duty 0.0

puts "FIFO_POWER_REPORT_BEGIN"
report_power -digits 6
puts "FIFO_POWER_REPORT_END"
puts "FIFO_POWER_ANALYSIS_COMPLETE"
"""


def analyze(name, top, config):
    label, width, depth, addr_width = config
    design_id = f"{name}_{label}"

    print(
        f"\n========== FIFO POWER: {design_id.upper()} ==========",
        flush=True
    )

    netlist = OUT / f"{design_id}_mapped.v"
    tcl_file = OUT / f"{design_id}_power.tcl"
    log_file = OUT / f"{design_id}_power.log"

    if not netlist.is_file():
        print("[FAIL] Missing mapped netlist:", netlist)
        return None

    tcl_file.write_text(
        build_tcl(top, netlist),
        encoding="utf-8"
    )

    try:
        result = subprocess.run(
            ["sta", "-exit", str(tcl_file)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=120
        )
    except subprocess.TimeoutExpired:
        print("[FAIL] OpenSTA timeout")
        return None
    except OSError as exc:
        print("[FAIL] Unable to execute OpenSTA:", exc)
        return None

    output = result.stdout + "\n" + result.stderr

    log_file.write_text(
        output,
        encoding="utf-8"
    )

    if result.returncode != 0 or ERROR_PATTERN.search(output):
        print("[FAIL] OpenSTA reported an error")

        for line in output.splitlines():
            if ERROR_PATTERN.search(line):
                print(line)

        print("Full log:", log_file)
        return None

    warnings = [
        line.strip()
        for line in output.splitlines()
        if re.match(r"^\s*Warning:", line)
    ]

    for warning in warnings:
        print("[WARNING]", warning)

    for marker in [
        "FIFO_POWER_REPORT_BEGIN",
        "FIFO_POWER_REPORT_END",
        "FIFO_POWER_ANALYSIS_COMPLETE",
    ]:
        if marker not in output:
            print("[FAIL] Missing report marker:", marker)
            return None

    section = output.split(
        "FIFO_POWER_REPORT_BEGIN", 1
    )[1].split(
        "FIFO_POWER_REPORT_END", 1
    )[0]

    matches = TOTAL_PATTERN.findall(section)

    if len(matches) != 1:
        print("[FAIL] Expected exactly one total-power row")
        print(section[-2500:])
        print("Full log:", log_file)
        return None

    internal, switching, leakage, total = [
        float(value)
        for value in matches[0]
    ]

    if min(internal, switching, leakage, total) < 0:
        print("[FAIL] Negative power value")
        return None

    if total <= 0:
        print("[FAIL] Total power must be positive")
        return None

    component_sum = internal + switching + leakage
    tolerance = max(total * 0.01, 1e-12)

    if abs(component_sum - total) > tolerance:
        print("[FAIL] Inconsistent power components")
        print("Component sum:", component_sum)
        print("Reported total:", total)
        return None

    record = {
        "design": name,
        "configuration": label,
        "data_width": width,
        "depth": depth,
        "addr_width": addr_width,
        "technology": "Nangate45 typical",
        "clock_period_ns": CLOCK_PERIOD_NS,
        "assumed_input_transitions_per_cycle":
            INPUT_ACTIVITY_PER_CYCLE,
        "assumed_input_transitions_per_ns":
            INPUT_ACTIVITY_PER_CYCLE / CLOCK_PERIOD_NS,
        "output_load_ff": OUTPUT_LOAD_FF,
        "internal_power_uw": internal * 1e6,
        "switching_power_uw": switching * 1e6,
        "leakage_power_uw": leakage * 1e6,
        "total_power_uw": total * 1e6,
        "warning_count": len(warnings),
        "power_log": str(log_file.relative_to(ROOT)),
    }

    print("[PASS] Power report generated")
    print(f"Internal power:  {record['internal_power_uw']:.6f} uW")
    print(f"Switching power: {record['switching_power_uw']:.6f} uW")
    print(f"Leakage power:   {record['leakage_power_uw']:.6f} uW")
    print(f"Total power:     {record['total_power_uw']:.6f} uW")
    print("Log:", log_file)

    return record


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    if not LIB.is_file():
        print("[FAIL] Nangate45 Liberty file missing")
        return 1

    print("=" * 70)
    print("DAY 30 STEP 5E - FIFO POWER ESTIMATION")
    print("=" * 70)

    records = []
    failures = []

    for config in CONFIGURATIONS:
        for name, top in DESIGNS:
            record = analyze(name, top, config)

            if record is None:
                failures.append(f"{name}_{config[0]}")
            else:
                records.append(record)

    if failures or len(records) != 8:
        print("\n========== FINAL RESULT ==========")
        print("[FAIL] FIFO power analysis incomplete")
        print("Failed designs:", ", ".join(failures))
        return 1

    lookup = {
        (row["design"], row["configuration"]): row
        for row in records
    }

    comparisons = []

    print("\n========== FIFO POWER COMPARISON ==========")

    for label, width, depth, addr_width in CONFIGURATIONS:
        baseline = lookup[("baseline", label)]
        optimized = lookup[("optimized", label)]

        baseline_power = baseline["total_power_uw"]
        optimized_power = optimized["total_power_uw"]

        reduction = (
            (baseline_power - optimized_power)
            / baseline_power * 100
        )

        comparison = {
            "configuration": label,
            "data_width": width,
            "depth": depth,
            "addr_width": addr_width,
            "baseline_power_uw": baseline_power,
            "optimized_power_uw": optimized_power,
            "power_reduction_percent": reduction,
            "baseline_internal_uw":
                baseline["internal_power_uw"],
            "optimized_internal_uw":
                optimized["internal_power_uw"],
            "baseline_switching_uw":
                baseline["switching_power_uw"],
            "optimized_switching_uw":
                optimized["switching_power_uw"],
            "baseline_leakage_uw":
                baseline["leakage_power_uw"],
            "optimized_leakage_uw":
                optimized["leakage_power_uw"],
        }

        comparisons.append(comparison)

        print(f"\nConfiguration: {label}")
        print(f"Baseline power:  {baseline_power:.6f} uW")
        print(f"Optimized power: {optimized_power:.6f} uW")
        print(f"Power reduction: {reduction:+.2f}%")

        if reduction > 0:
            print("[RESULT] Optimized FIFO has lower estimated power")
        elif reduction < 0:
            print("[RESULT] Optimized FIFO has higher estimated power")
        else:
            print("[RESULT] Estimated power is unchanged")

    csv_file = OUT / "day30_fifo_power_comparison.csv"
    json_file = OUT / "day30_fifo_power_comparison.json"

    with csv_file.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(comparisons[0].keys())
        )

        writer.writeheader()
        writer.writerows(comparisons)

    report = {
        "status": "ANALYSIS_COMPLETED",
        "technology": "Nangate45 typical",
        "scope": "Pre-layout assumed-activity power estimation",
        "clock_period_ns": CLOCK_PERIOD_NS,
        "assumed_input_transitions_per_cycle":
            INPUT_ACTIVITY_PER_CYCLE,
        "assumed_input_transitions_per_ns":
            INPUT_ACTIVITY_PER_CYCLE / CLOCK_PERIOD_NS,
        "output_load_ff": OUTPUT_LOAD_FF,
        "mapped_implementations": len(records),
        "records": records,
        "comparison": comparisons,
        "limitations": [
            "Input activity is assumed, not obtained from VCD/SAIF",
            "Actual FIFO workloads and occupancy are not modeled",
            "No placement or routing",
            "No extracted interconnect parasitics",
            "No physical clock tree",
            "Power depends on assumed activity and output loads",
            "Reset is treated as inactive during power estimation",
        ],
    }

    json_file.write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8"
    )

    print("\n========== FINAL POWER VALIDATION ==========")
    print("[PASS] All eight FIFO power reports generated")
    print("CSV:", csv_file)
    print("JSON:", json_file)
    print("DAY 30 FIFO POWER ESTIMATION: COMPLETED")

    return 0


if __name__ == "__main__":
    sys.exit(main())
