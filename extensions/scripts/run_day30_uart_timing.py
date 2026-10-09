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
    {
        "name": "baseline_tx",
        "top": "uart_tx",
        "inputs": ["rst", "start", "data_in*"],
    },
    {
        "name": "optimized_tx",
        "top": "uart_tx_opt",
        "inputs": ["rst", "start", "data_in*"],
    },
    {
        "name": "baseline_rx",
        "top": "uart_rx",
        "inputs": ["rst", "rx"],
    },
    {
        "name": "optimized_rx",
        "top": "uart_rx_opt",
        "inputs": ["rst", "rx"],
    },
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


def build_tcl(design, netlist):
    top = design["top"]

    lines = [
        f"read_liberty {LIB}",
        f"read_verilog {netlist}",
        f"link_design {top}",
        "",
        (
            "create_clock -name uart_clk "
            f"-period {CLOCK_PERIOD_NS} [get_ports clk]"
        ),
        "",
    ]

    # Apply data/control constraints explicitly.
    # Do not apply input delay to the clock port.
    for port in design["inputs"]:
        port_expression = f"[get_ports {{{port}}}]"

        lines.append(
            f"set_input_delay {INPUT_DELAY_NS} "
            f"-clock uart_clk {port_expression}"
        )

        lines.append(
            f"set_input_transition {INPUT_TRANSITION_NS} "
            f"{port_expression}"
        )

    lines.extend([
        "",
        (
            f"set_output_delay {OUTPUT_DELAY_NS} "
            "-clock uart_clk [all_outputs]"
        ),
        f"set_load {OUTPUT_LOAD_FF} [all_outputs]",
        "",
        'puts "UART_MAX_PATHS_BEGIN"',
        "report_checks -path_delay max -group_count 20",
        'puts "UART_MAX_PATHS_END"',
        'puts "UART_TIMING_ANALYSIS_COMPLETE"',
        "",
    ])

    return "\n".join(lines)


def analyse_design(design):
    name = design["name"]
    top = design["top"]

    print(
        f"\n========== UART TIMING: {name.upper()} ==========",
        flush=True,
    )

    netlist = PPA / f"{name}_mapped.v"
    tcl_file = PPA / f"{name}_timing.tcl"
    log_file = PPA / f"{name}_timing.log"

    if not netlist.is_file():
        print("[FAIL] Mapped netlist missing:", netlist)
        return None

    tcl_file.write_text(
        build_tcl(design, netlist),
        encoding="utf-8",
    )

    try:
        process = subprocess.run(
            ["sta", "-exit", str(tcl_file)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=120,
        )

    except subprocess.TimeoutExpired:
        print("[FAIL] OpenSTA timeout")
        return None

    except OSError as exc:
        print("[FAIL] Cannot execute OpenSTA:", exc)
        return None

    output = process.stdout + "\n" + process.stderr

    log_file.write_text(
        output,
        encoding="utf-8",
    )

    if process.returncode != 0:
        print("[FAIL] OpenSTA exited with an error")
        print(output[-2500:])
        return None

    if ERROR_PATTERN.search(output):
        print("[FAIL] OpenSTA reported an error")

        for line in output.splitlines():
            if ERROR_PATTERN.search(line):
                print(line)

        return None

    if WARNING_PATTERN.search(output):
        print("[WARNING] OpenSTA warnings detected")

        for line in output.splitlines():
            if WARNING_PATTERN.search(line):
                print(line)

        print(
            "[FAIL] Review warnings before accepting "
            "timing results"
        )
        return None

    if "UART_TIMING_ANALYSIS_COMPLETE" not in output:
        print("[FAIL] Completion marker missing")
        return None

    if (
        "UART_MAX_PATHS_BEGIN" not in output
        or "UART_MAX_PATHS_END" not in output
    ):
        print("[FAIL] Timing report markers missing")
        return None

    timing_section = output.split(
        "UART_MAX_PATHS_BEGIN", 1
    )[1].split(
        "UART_MAX_PATHS_END", 1
    )[0]

    if "Startpoint:" not in timing_section:
        print("[FAIL] No timing paths found")
        return None

    matches = SLACK_PATTERN.findall(timing_section)

    if not matches:
        print("[FAIL] Slack values could not be parsed")
        print(timing_section[-2500:])
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
        "top_module": top,
        "technology": "Nangate45 typical",
        "clks_per_bit": 16,
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
    print("Reported timing paths:", len(matches))
    print(f"Worst setup slack: {worst_slack:.4f} ns")
    print("Setup timing:", status)
    print("Log:", log_file)

    return record


def main():
    PPA.mkdir(parents=True, exist_ok=True)

    if not LIB.is_file():
        print("[FAIL] Nangate45 library missing")
        return 1

    print("=" * 65)
    print("DAY 30 STEP 4E-4 - UART TIMING ANALYSIS")
    print("=" * 65)

    records = []
    failures = []

    for design in DESIGNS:
        record = analyse_design(design)

        if record is None:
            failures.append(design["name"])
        else:
            records.append(record)

    if failures or len(records) != 4:
        print("\n========== FINAL RESULT ==========")
        print("[FAIL] Timing analysis incomplete")
        print("Failed designs:", ", ".join(failures))
        return 1

    csv_file = PPA / "day30_uart_timing_comparison.csv"
    json_file = PPA / "day30_uart_timing_comparison.json"

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

    violations = [
        row["design"]
        for row in records
        if row["setup_status"] == "VIOLATED"
    ]

    report = {
        "status": (
            "TIMING_VIOLATIONS"
            if violations
            else "ANALYSIS_COMPLETED"
        ),
        "technology": "Nangate45 typical",
        "scope": "Pre-layout maximum-path timing",
        "constraints": {
            "clock_period_ns": CLOCK_PERIOD_NS,
            "input_delay_ns": INPUT_DELAY_NS,
            "output_delay_ns": OUTPUT_DELAY_NS,
            "input_transition_ns": INPUT_TRANSITION_NS,
            "output_load_ff": OUTPUT_LOAD_FF,
        },
        "records": records,
        "limitations": [
            "No routed interconnect parasitics",
            "Default CLKS_PER_BIT=16",
            "Only reported maximum-delay paths assessed",
            "Hold timing not certified",
            "Power not measured",
        ],
    }

    json_file.write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
    )

    print("\n========== UART TIMING COMPARISON ==========")

    for block in ("tx", "rx"):
        baseline = next(
            row for row in records
            if row["design"] == f"baseline_{block}"
        )

        optimized = next(
            row for row in records
            if row["design"] == f"optimized_{block}"
        )

        baseline_slack = baseline["worst_setup_slack_ns"]
        optimized_slack = optimized["worst_setup_slack_ns"]

        delta = optimized_slack - baseline_slack

        print(f"\nUART {block.upper()}")
        print(f"Baseline slack: {baseline_slack:.4f} ns")
        print(f"Optimized slack: {optimized_slack:.4f} ns")
        print(f"Slack difference: {delta:+.4f} ns")

        if delta > 0:
            print("[RESULT] Optimized design has more setup margin")
        elif delta < 0:
            print("[RESULT] Optimized design has less setup margin")
        else:
            print("[RESULT] Equal reported setup margin")

    print("\n========== FINAL TIMING VALIDATION ==========")

    if violations:
        print("[WARNING] Setup timing violations found")
        print("Violating designs:", ", ".join(violations))
    else:
        print("[PASS] All four designs meet reported setup timing")

    print("CSV:", csv_file)
    print("JSON:", json_file)
    print("DAY 30 UART TIMING ANALYSIS: COMPLETED")

    return 2 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
