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
INPUT_DELAY_NS = 0.2
OUTPUT_DELAY_NS = 0.2
INPUT_TRANSITION_NS = 0.05
OUTPUT_LOAD_FF = 5.0

SLACK_PATTERN = re.compile(
    r"(?im)^\s*"
    r"([+-]?(?:\d+(?:\.\d*)?|\.\d+))"
    r"\s+slack\s+\((MET|VIOLATED)\)\s*$"
)

ERROR_PATTERN = re.compile(
    r"(?im)^\s*(?:Error:|STA Error:)"
)

WARNING_PATTERN = re.compile(
    r"(?im)^\s*Warning:"
)


def build_tcl(top, netlist):
    lines = [
        f"read_liberty {LIB}",
        f"read_verilog {netlist}",
        f"link_design {top}",
        "",
        (
            "create_clock -name fifo_clk "
            f"-period {CLOCK_PERIOD_NS} [get_ports clk]"
        ),
        "",
    ]

    # Constrain only data and control inputs.
    # The clock input is constrained separately.
    input_ports = [
        "rst",
        "wr_en",
        "rd_en",
        "data_in*",
    ]

    for port in input_ports:
        lines.append(
            f"set_input_delay {INPUT_DELAY_NS} "
            f"-clock fifo_clk [get_ports {{{port}}}]"
        )

        lines.append(
            f"set_input_transition {INPUT_TRANSITION_NS} "
            f"[get_ports {{{port}}}]"
        )

    lines.extend([
        "",
        (
            f"set_output_delay {OUTPUT_DELAY_NS} "
            "-clock fifo_clk [all_outputs]"
        ),
        f"set_load {OUTPUT_LOAD_FF} [all_outputs]",
        "",
        'puts "FIFO_MAX_PATHS_BEGIN"',
        "report_checks -path_delay max -group_count 20",
        'puts "FIFO_MAX_PATHS_END"',
        'puts "FIFO_TIMING_ANALYSIS_COMPLETE"',
        "",
    ])

    return "\n".join(lines)


def analyse_design(name, top, config):
    label, width, depth, addr_width = config
    design_id = f"{name}_{label}"

    print(
        f"\n========== FIFO TIMING: {design_id.upper()} ==========",
        flush=True,
    )

    netlist = OUT / f"{design_id}_mapped.v"
    tcl_file = OUT / f"{design_id}_timing.tcl"
    log_file = OUT / f"{design_id}_timing.log"

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

    except subprocess.TimeoutExpired:
        print("[FAIL] OpenSTA timed out")
        return None

    except OSError as exc:
        print("[FAIL] Could not execute OpenSTA:", exc)
        return None

    output = result.stdout + "\n" + result.stderr

    log_file.write_text(
        output,
        encoding="utf-8",
    )

    if result.returncode != 0:
        print("[FAIL] OpenSTA exit code:", result.returncode)
        print(output[-2000:])
        return None

    if ERROR_PATTERN.search(output):
        print("[FAIL] OpenSTA errors detected")

        for line in output.splitlines():
            if ERROR_PATTERN.search(line):
                print(line)

        print("Log:", log_file)
        return None

    if WARNING_PATTERN.search(output):
        print("[FAIL] OpenSTA warnings require review")

        for line in output.splitlines():
            if WARNING_PATTERN.search(line):
                print(line)

        print("Log:", log_file)
        return None

    required_markers = [
        "FIFO_MAX_PATHS_BEGIN",
        "FIFO_MAX_PATHS_END",
        "FIFO_TIMING_ANALYSIS_COMPLETE",
    ]

    if any(marker not in output for marker in required_markers):
        print("[FAIL] Timing report incomplete")
        return None

    section = output.split(
        "FIFO_MAX_PATHS_BEGIN", 1
    )[1].split(
        "FIFO_MAX_PATHS_END", 1
    )[0]

    if "Startpoint:" not in section:
        print("[FAIL] No timing paths found")
        print("Log:", log_file)
        return None

    matches = SLACK_PATTERN.findall(section)

    if not matches:
        print("[FAIL] Could not extract setup slack")
        print(section[-2000:])
        return None

    slack_values = [
        float(value)
        for value, status in matches
    ]

    worst_slack = min(slack_values)

    violated = (
        worst_slack < 0
        or any(
            status == "VIOLATED"
            for value, status in matches
        )
    )

    status = "VIOLATED" if violated else "MET"

    record = {
        "design": name,
        "configuration": label,
        "data_width": width,
        "depth": depth,
        "addr_width": addr_width,
        "technology": "Nangate45 typical",
        "clock_period_ns": CLOCK_PERIOD_NS,
        "input_delay_ns": INPUT_DELAY_NS,
        "output_delay_ns": OUTPUT_DELAY_NS,
        "input_transition_ns": INPUT_TRANSITION_NS,
        "output_load_ff": OUTPUT_LOAD_FF,
        "reported_paths": len(matches),
        "worst_setup_slack_ns": worst_slack,
        "setup_status": status,
        "timing_log": str(log_file.relative_to(ROOT)),
    }

    print("[PASS] OpenSTA execution completed")
    print("Reported paths:", len(matches))
    print(f"Worst setup slack: {worst_slack:.4f} ns")
    print("Setup timing status:", status)

    return record


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    if not LIB.is_file():
        print("[FAIL] Nangate45 library missing")
        return 1

    print("=" * 70)
    print("DAY 30 STEP 5D - FIFO TIMING ANALYSIS")
    print("=" * 70)

    records = []
    failures = []

    for config in CONFIGURATIONS:
        for name, top in DESIGNS:
            record = analyse_design(name, top, config)

            if record is None:
                failures.append(f"{name}_{config[0]}")
            else:
                records.append(record)

    if failures or len(records) != 8:
        print("\n========== FINAL RESULT ==========")
        print("[FAIL] FIFO timing analysis incomplete")
        print("Failed designs:", ", ".join(failures))
        return 1

    csv_file = OUT / "day30_fifo_timing_comparison.csv"
    json_file = OUT / "day30_fifo_timing_comparison.json"

    with csv_file.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(records[0].keys()),
        )

        writer.writeheader()
        writer.writerows(records)

    lookup = {
        (row["design"], row["configuration"]): row
        for row in records
    }

    comparison = []

    print("\n========== FIFO TIMING COMPARISON ==========")

    for label, width, depth, addr_width in CONFIGURATIONS:
        baseline = lookup[("baseline", label)]
        optimized = lookup[("optimized", label)]

        base_slack = baseline["worst_setup_slack_ns"]
        opt_slack = optimized["worst_setup_slack_ns"]

        delta = opt_slack - base_slack

        comparison.append({
            "configuration": label,
            "baseline_slack_ns": base_slack,
            "optimized_slack_ns": opt_slack,
            "slack_change_ns": delta,
            "baseline_status": baseline["setup_status"],
            "optimized_status": optimized["setup_status"],
        })

        print(f"\nConfiguration: {label}")
        print(f"Baseline slack:  {base_slack:.4f} ns")
        print(f"Optimized slack: {opt_slack:.4f} ns")
        print(f"Slack change:    {delta:+.4f} ns")

        if delta > 0:
            print("[RESULT] Optimized FIFO has more setup margin")
        elif delta < 0:
            print("[RESULT] Optimized FIFO has less setup margin")
        else:
            print("[RESULT] Equal reported setup margin")

    violations = [
        row["design"] + "_" + row["configuration"]
        for row in records
        if row["setup_status"] != "MET"
    ]

    report = {
        "status": (
            "TIMING_VIOLATIONS"
            if violations
            else "ANALYSIS_COMPLETED"
        ),
        "technology": "Nangate45 typical",
        "scope": "Pre-layout maximum-delay timing",
        "clock_period_ns": CLOCK_PERIOD_NS,
        "records": records,
        "comparison": comparison,
        "limitations": [
            "No routed parasitics",
            "No post-placement or post-route timing",
            "Only reported maximum-delay paths analysed",
            "Hold timing is not certified",
            "Power is not measured in this step",
        ],
    }

    json_file.write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
    )

    print("\n========== FINAL TIMING VALIDATION ==========")

    if violations:
        print("[WARNING] Setup timing violations detected")
        print("Violating designs:", ", ".join(violations))
    else:
        print("[PASS] All eight FIFO designs meet setup timing")

    print("CSV:", csv_file)
    print("JSON:", json_file)
    print("DAY 30 FIFO TIMING ANALYSIS: COMPLETED")

    return 2 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
