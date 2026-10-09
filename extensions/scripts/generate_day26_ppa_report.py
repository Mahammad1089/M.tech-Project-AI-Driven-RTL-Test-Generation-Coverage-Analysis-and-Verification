#!/usr/bin/env python3

import csv
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path.home() / "Mtech_project" / "AI_RTL_Verification"
PPA = ROOT / "extensions/results/day26/ppa"
OUT = ROOT / "extensions/results/day26"

CASES = [
    "fsm_original_1011",
    "mealy_10101_overlap_0",
    "mealy_10101_overlap_1",
    "mealy_1011_overlap_0",
    "mealy_1011_overlap_1",
    "mealy_1101_overlap_0",
    "mealy_1101_overlap_1",
    "moore_10101_overlap_0",
    "moore_10101_overlap_1",
    "moore_1011_overlap_0",
    "moore_1011_overlap_1",
    "moore_1101_overlap_0",
    "moore_1101_overlap_1",
]

NUMBER = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"

def read_required(path):
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError(f"Missing or empty report: {path}")
    return path.read_text(errors="replace")

def reject_errors(text, name):
    if re.search(r"(?im)^\s*(?:Error:|STA Error:)", text):
        raise ValueError(f"OpenSTA/Yosys errors detected: {name}")

def parse_area(text, name):
    matches = re.findall(
        rf"Chip area for module\s+.*?:\s*({NUMBER})",
        text,
        flags=re.I,
    )
    if not matches:
        raise ValueError(f"Mapped area not found: {name}")
    return float(matches[-1])

def parse_timing(text, name):
    if "TIMING ANALYSIS COMPLETED" not in text:
        raise ValueError(f"Timing completion marker missing: {name}")

    maximum = re.search(
        r"MAXIMUM TIMING PATHS(.*?)MINIMUM TIMING PATHS",
        text,
        flags=re.S,
    )
    if maximum is None:
        raise ValueError(f"Maximum timing section missing: {name}")

    section = maximum.group(1)

    start = re.search(r"(?m)^Startpoint:\s*(.+)$", section)
    end = re.search(r"(?m)^Endpoint:\s*(.+)$", section)

    slack = re.search(
        rf"(?m)^\s*({NUMBER})\s+slack\s+\((?:MET|VIOLATED)\)",
        section,
    )

    arrival = re.search(
        rf"(?m)^\s*({NUMBER})\s+data arrival time\s*$",
        section,
    )

    if not all((start, end, slack, arrival)):
        raise ValueError(f"Incomplete maximum timing path: {name}")

    return {
        "startpoint": start.group(1).strip(),
        "endpoint": end.group(1).strip(),
        "setup_slack_ns": float(slack.group(1)),
        "data_arrival_ns": float(arrival.group(1)),
    }

def parse_power(text, name):
    if "POWER ANALYSIS COMPLETED" not in text:
        raise ValueError(f"Power completion marker missing: {name}")

    rows = re.findall(
        rf"(?m)^\s*Total\s+({NUMBER})\s+({NUMBER})"
        rf"\s+({NUMBER})\s+({NUMBER})\s+100\.0%",
        text,
    )

    if len(rows) != 1:
        raise ValueError(
            f"Expected exactly one total-power row for {name}; "
            f"found {len(rows)}"
        )

    internal, switching, leakage, total = map(float, rows[0])

    if min(internal, switching, leakage, total) < 0:
        raise ValueError(f"Negative power value: {name}")

    if abs((internal + switching + leakage) - total) > max(
        total * 0.02, 1e-10
    ):
        raise ValueError(f"Power components inconsistent: {name}")

    # OpenSTA report_power values are interpreted as watts.
    # Convert to microwatts for presentation.
    return {
        "internal_power_uw": internal * 1e6,
        "switching_power_uw": switching * 1e6,
        "leakage_power_uw": leakage * 1e6,
        "total_power_uw": total * 1e6,
    }

def main():
    print("=" * 65)
    print("DAY 26 - CONSOLIDATED FSM PPA REPORT")
    print("=" * 65)

    records = []
    errors = []

    for name in CASES:
        try:
            mapping_path = PPA / f"{name}_mapping.log"
            timing_path = PPA / f"{name}_timing.log"
            power_path = PPA / f"{name}_power.log"
            netlist_path = PPA / f"{name}_mapped.v"

            if not netlist_path.is_file():
                raise ValueError(f"Missing mapped netlist: {netlist_path}")

            mapping = read_required(mapping_path)
            timing = read_required(timing_path)
            power = read_required(power_path)

            reject_errors(mapping, name)
            reject_errors(timing, name)
            reject_errors(power, name)

            area = parse_area(mapping, name)
            t = parse_timing(timing, name)
            p = parse_power(power, name)

            if area <= 0:
                raise ValueError(f"Invalid mapped area: {name}")

            if t["setup_slack_ns"] < 0:
                raise ValueError(f"Setup timing violation: {name}")

            record = {
                "configuration": name,
                "area_um2": area,
                **t,
                **p,
                "timing_status": "MET",
                "mapping_log": str(mapping_path.relative_to(ROOT)),
                "timing_log": str(timing_path.relative_to(ROOT)),
                "power_log": str(power_path.relative_to(ROOT)),
            }

            records.append(record)

            print(
                f"[PASS] {name:<26} "
                f"Area={area:.3f} um2  "
                f"Slack={t['setup_slack_ns']:.3f} ns  "
                f"Power={p['total_power_uw']:.3f} uW"
            )

        except (ValueError, OSError) as exc:
            errors.append(str(exc))
            print(f"[FAIL] {name}: {exc}")

    print()
    print(f"Configurations expected : {len(CASES)}")
    print(f"Configurations passed   : {len(records)}")
    print(f"Configurations failed   : {len(errors)}")

    if errors:
        print()
        print("DAY 26 CONSOLIDATED PPA: FAIL")
        for error in errors:
            print("ERROR:", error)
        return 1

    OUT.mkdir(parents=True, exist_ok=True)

    csv_path = OUT / "day26_fsm_ppa_summary.csv"
    json_path = OUT / "day26_fsm_ppa_summary.json"
    txt_path = OUT / "day26_fsm_ppa_report.txt"

    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=list(records[0].keys()),
        )
        writer.writeheader()
        writer.writerows(records)

    report = {
        "day": 26,
        "title": "FSM Technology-Mapped PPA Comparison",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "technology": "Nangate45 typical Liberty",
        "clock_period_ns": 10.0,
        "input_delay_ns": 0.2,
        "output_delay_ns": 0.2,
        "switching_activity_transitions_per_ns": 0.1,
        "duty_cycle": 0.5,
        "configuration_count": len(records),
        "status": "PASS",
        "records": records,
        "limitations": [
            "Pre-layout technology-mapped estimates only.",
            "Power uses assumed switching activity, not VCD/SAIF.",
            "Data arrival time includes input delay for input-origin paths.",
            "Different FSM variants are not necessarily functionally equivalent.",
            "Positive setup slack does not establish hold closure.",
            "No post-route parasitics or physical layout effects included.",
        ],
    }

    json_path.write_text(json.dumps(report, indent=2) + "\n")

    lines = [
        "DAY 26 - FSM CONSOLIDATED PPA REPORT",
        "=" * 80,
        "",
        f"Configurations: {len(records)}",
        "Technology: Nangate45 typical",
        "Clock period: 10 ns",
        "Power activity: assumed 0.1 transitions/ns",
        "",
        f"{'Configuration':<27} {'Area (um2)':>12} "
        f"{'Slack (ns)':>12} {'Power (uW)':>12}",
        "-" * 80,
    ]

    for r in records:
        lines.append(
            f"{r['configuration']:<27} "
            f"{r['area_um2']:>12.3f} "
            f"{r['setup_slack_ns']:>12.3f} "
            f"{r['total_power_uw']:>12.3f}"
        )

    lowest_area = min(records, key=lambda r: r["area_um2"])
    lowest_power = min(records, key=lambda r: r["total_power_uw"])
    highest_slack = max(records, key=lambda r: r["setup_slack_ns"])

    lines.extend([
        "",
        "SUMMARY",
        "-" * 80,
        f"Lowest mapped area: {lowest_area['configuration']}",
        f"Lowest estimated power: {lowest_power['configuration']}",
        f"Highest reported setup slack: {highest_slack['configuration']}",
        "",
        "LIMITATIONS",
    ])

    for limitation in report["limitations"]:
        lines.append("- " + limitation)

    lines.extend([
        "",
        "FINAL STATUS: PASS - 13 PPA RECORDS EXTRACTED",
        "",
    ])

    txt_path.write_text("\n".join(lines))

    print()
    print("Generated files:")
    for path in (csv_path, json_path, txt_path):
        print(path.relative_to(ROOT))

    print()
    print("DAY 26 CONSOLIDATED PPA: PASS")
    return 0

if __name__ == "__main__":
    sys.exit(main())
