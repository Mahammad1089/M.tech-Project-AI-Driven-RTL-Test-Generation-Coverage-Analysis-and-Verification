#!/usr/bin/env python3

import json
import re
import sys
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
DAY = ROOT / "extensions/results/day25"
PPA = DAY / "ppa"

FILES = {
    "equivalence": DAY / "alu_equivalence.log",
    "original_mapping": PPA / "original_mapping.log",
    "optimized_mapping": PPA / "optimized_mapping.log",
    "original_timing": PPA / "original_timing.log",
    "optimized_timing": PPA / "optimized_timing.log",
    "original_power": PPA / "original_power.log",
    "optimized_power": PPA / "optimized_power.log",
}

NUM = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?"


def load_logs():
    logs = {}
    for name, path in FILES.items():
        if not path.is_file():
            raise ValueError(f"Required file missing: {path}")
        logs[name] = path.read_text(errors="replace")
    return logs


def percent_reduction(original, optimized):
    if original <= 0:
        raise ValueError("Original measurement must be positive")
    return 100.0 * (original - optimized) / original


def extract_equivalence(text):
    values = {}
    for key in ("TOTAL CHECKS", "PASSED CHECKS", "FAILED CHECKS"):
        match = re.search(
            rf"^\s*{re.escape(key)}\s*:\s*(\d+)",
            text,
            re.MULTILINE | re.IGNORECASE,
        )
        if not match:
            raise ValueError(f"Missing equivalence field: {key}")
        values[key] = int(match.group(1))

    passed = (
        values["TOTAL CHECKS"] == 2048
        and values["PASSED CHECKS"] == 2048
        and values["FAILED CHECKS"] == 0
        and "DAY 25 ALU EQUIVALENCE: PASS" in text
    )

    return {
        "total": values["TOTAL CHECKS"],
        "passed": values["PASSED CHECKS"],
        "failed": values["FAILED CHECKS"],
        "status": "PASS" if passed else "FAIL",
    }


def extract_mapping(text):
    area_matches = re.findall(
        rf"Chip area for module\s+\\?\S+\s*:\s*({NUM})",
        text,
        re.IGNORECASE,
    )

    cell_matches = re.findall(
        r"Number of cells:\s*(\d+)",
        text,
        re.IGNORECASE,
    )

    if not area_matches or not cell_matches:
        raise ValueError(
            "Mapped cell area or cell count missing from Yosys log"
        )

    return {
        "area_um2": float(area_matches[-1]),
        "cells": int(cell_matches[-1]),
    }


def extract_timing(text):
    """
    Parse the worst maximum-delay path from OpenSTA.

    The parser explicitly separates max and min paths,
    reads the first positive arrival-time row,
    and handles the negative arrival-time row used
    in the slack calculation.
    """

    sections = re.split(
        r"(?=^\s*Startpoint:)",
        text,
        flags=re.MULTILINE,
    )

    paths = []

    for section in sections:
        if not re.search(
            r"^\s*Startpoint:",
            section,
            re.MULTILINE,
        ):
            continue

        if not re.search(
            r"^\s*Path Type:\s*max\s*$",
            section,
            re.MULTILINE | re.IGNORECASE,
        ):
            continue

        start = re.search(
            r"^\s*Startpoint:\s*(.+)$",
            section,
            re.MULTILINE,
        )

        end = re.search(
            r"^\s*Endpoint:\s*(.+)$",
            section,
            re.MULTILINE,
        )

        delay_match = re.search(
            rf"^\s*({NUM})\s+({NUM})\s+"
            r"(?:\^|v)?\s*input external delay\b",
            section,
            re.MULTILINE,
        )

        if not delay_match:
            # Some OpenSTA versions omit the edge marker.
            delay_match = re.search(
                rf"^\s*({NUM})\s+({NUM})\s+"
                r"input external delay\b",
                section,
                re.MULTILINE,
            )

        arrival_matches = re.findall(
            rf"^\s*({NUM})\s+data arrival time\s*$",
            section,
            re.MULTILINE,
        )

        required_matches = re.findall(
            rf"^\s*({NUM})\s+data required time\s*$",
            section,
            re.MULTILINE,
        )

        slack_match = re.search(
            rf"^\s*({NUM})\s+slack\s+"
            r"\((MET|VIOLATED)\)",
            section,
            re.MULTILINE | re.IGNORECASE,
        )

        if not all([
            start,
            end,
            delay_match,
            arrival_matches,
            required_matches,
            slack_match,
        ]):
            continue

        # The first arrival is the forward-path arrival.
        # The later negative arrival belongs to the
        # required-minus-arrival slack calculation.
        arrival = float(arrival_matches[0])
        required = float(required_matches[0])
        input_delay = float(delay_match.group(2))
        slack = float(slack_match.group(1))

        result = {
            "startpoint": start.group(1).strip(),
            "endpoint": end.group(1).strip(),
            "arrival_ns": arrival,
            "input_delay_ns": input_delay,
            "required_ns": required,
            "slack_ns": slack,
            "timing_status": slack_match.group(2).upper(),
            "cell_path_delay_ns": arrival - input_delay,
        }

        paths.append(result)

    if not paths:
        raise ValueError(
            "No complete maximum timing path found. "
            "Check the original and optimized OpenSTA reports."
        )

    return min(paths, key=lambda p: p["slack_ns"])


def extract_power(text):
    matches = re.findall(
        rf"^\s*Total\s+({NUM})\s+({NUM})\s+"
        rf"({NUM})\s+({NUM})(?:\s|$)",
        text,
        re.MULTILINE,
    )

    if not matches:
        raise ValueError("OpenSTA total power row not found")

    internal, switching, leakage, total = map(
        float, matches[-1]
    )

    if min(internal, switching, leakage, total) < 0:
        raise ValueError("Negative power value detected")

    return {
        "internal_w": internal,
        "switching_w": switching,
        "leakage_w": leakage,
        "total_w": total,
    }


def main():
    print("========== DAY 25 ALU COMPLETE DIAGNOSIS ==========")

    logs = load_logs()

    eq = extract_equivalence(logs["equivalence"])

    original_map = extract_mapping(logs["original_mapping"])
    optimized_map = extract_mapping(logs["optimized_mapping"])

    original_time = extract_timing(logs["original_timing"])
    optimized_time = extract_timing(logs["optimized_timing"])

    original_power = extract_power(logs["original_power"])
    optimized_power = extract_power(logs["optimized_power"])

    area0 = original_map["area_um2"]
    area1 = optimized_map["area_um2"]

    delay0 = original_time["cell_path_delay_ns"]
    delay1 = optimized_time["cell_path_delay_ns"]

    power0 = original_power["total_w"]
    power1 = optimized_power["total_w"]

    adp0 = area0 * delay0
    adp1 = area1 * delay1

    pdp0 = power0 * delay0 * 1e-9
    pdp1 = power1 * delay1 * 1e-9

    results = {
        "day": 25,
        "benchmark": "ALU",
        "generated_at_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "functional_equivalence": eq,
        "technology": {
            "library": "Nangate45 typical",
            "flow": "Pre-layout Yosys and OpenSTA",
        },
        "original": {
            "mapped_cells": original_map["cells"],
            "area_um2": area0,
            "timing": original_time,
            "power": original_power,
            "adp_um2_ns": adp0,
            "pdp_j": pdp0,
        },
        "optimized": {
            "mapped_cells": optimized_map["cells"],
            "area_um2": area1,
            "timing": optimized_time,
            "power": optimized_power,
            "adp_um2_ns": adp1,
            "pdp_j": pdp1,
        },
        "improvements_percent": {
            "mapped_cells": percent_reduction(
                original_map["cells"],
                optimized_map["cells"],
            ),
            "area": percent_reduction(area0, area1),
            "cell_path_delay": percent_reduction(delay0, delay1),
            "estimated_power": percent_reduction(power0, power1),
            "adp": percent_reduction(adp0, adp1),
            "pdp": percent_reduction(pdp0, pdp1),
        },
        "limitations": [
            "Equivalence covers binary input combinations only.",
            "Area is technology-mapped standard-cell area, not layout area.",
            "Timing excludes post-route interconnect parasitics.",
            "Delay is derived from rounded STA report values.",
            "Power is library-based and uses assumed switching activity.",
            "VCD-validated power has not been demonstrated.",
        ],
    }

    functional_ok = eq["status"] == "PASS"
    timing_met = (
        original_time["slack_ns"] >= 0
        and optimized_time["slack_ns"] >= 0
    )
    ppa_improved = (
        area1 < area0
        and delay1 < delay0
        and power1 < power0
    )

    if functional_ok and timing_met and ppa_improved:
        verdict = (
            "PASS - FUNCTIONALLY EQUIVALENT; "
            "PRE-LAYOUT PPA ESTIMATES IMPROVED"
        )
    else:
        verdict = "REVIEW REQUIRED"

    results["final_verdict"] = verdict

    lines = [
        "DAY 25 - COMPLETE ALU OPTIMIZATION DIAGNOSIS",
        "=" * 66,
        "",
        "1. FUNCTIONAL EQUIVALENCE",
        f"Total checks : {eq['total']}",
        f"Passed       : {eq['passed']}",
        f"Failed       : {eq['failed']}",
        f"Status       : {eq['status']}",
        "",
        "2. TECHNOLOGY-MAPPED CELL COUNT",
        f"Original     : {original_map['cells']}",
        f"Optimized    : {optimized_map['cells']}",
        f"Reduction    : {results['improvements_percent']['mapped_cells']:.2f}%",
        "",
        "3. STANDARD-CELL AREA",
        f"Original     : {area0:.6f} um^2",
        f"Optimized    : {area1:.6f} um^2",
        f"Reduction    : {results['improvements_percent']['area']:.2f}%",
        "",
        "4. CRITICAL-PATH TIMING",
        f"Original startpoint : {original_time['startpoint']}",
        f"Original endpoint   : {original_time['endpoint']}",
        f"Original arrival    : {original_time['arrival_ns']:.4f} ns",
        f"Original input delay: {original_time['input_delay_ns']:.4f} ns",
        f"Original cell delay : {delay0:.4f} ns",
        f"Original slack      : {original_time['slack_ns']:.4f} ns",
        "",
        f"Optimized startpoint : {optimized_time['startpoint']}",
        f"Optimized endpoint   : {optimized_time['endpoint']}",
        f"Optimized arrival    : {optimized_time['arrival_ns']:.4f} ns",
        f"Optimized input delay: {optimized_time['input_delay_ns']:.4f} ns",
        f"Optimized cell delay : {delay1:.4f} ns",
        f"Optimized slack      : {optimized_time['slack_ns']:.4f} ns",
        "",
        f"Delay reduction: {results['improvements_percent']['cell_path_delay']:.2f}%",
        "",
        "5. ESTIMATED POWER",
    ]

    for label, key in [
        ("Internal", "internal_w"),
        ("Switching", "switching_w"),
        ("Leakage", "leakage_w"),
        ("Total", "total_w"),
    ]:
        a = original_power[key] * 1e6
        b = optimized_power[key] * 1e6

        lines.extend([
            f"{label} power:",
            f"  Original  : {a:.6f} uW",
            f"  Optimized : {b:.6f} uW",
            f"  Reduction : {percent_reduction(a, b):.2f}%",
        ])

    lines.extend([
        "",
        "6. COMBINED EFFICIENCY METRICS",
        f"Original ADP  : {adp0:.6f} um^2*ns",
        f"Optimized ADP : {adp1:.6f} um^2*ns",
        f"ADP reduction : {results['improvements_percent']['adp']:.2f}%",
        "",
        f"Original PDP  : {pdp0 * 1e15:.6f} fJ",
        f"Optimized PDP : {pdp1 * 1e15:.6f} fJ",
        f"PDP reduction : {results['improvements_percent']['pdp']:.2f}%",
        "",
        "7. LIMITATIONS",
    ])

    for limitation in results["limitations"]:
        lines.append(f"- {limitation}")

    lines.extend([
        "",
        "8. FINAL DIAGNOSIS",
        verdict,
        "",
    ])

    DAY.mkdir(parents=True, exist_ok=True)

    txt_path = DAY / "day25_complete_diagnosis.txt"
    json_path = DAY / "day25_complete_diagnosis.json"

    txt_path.write_text("\n".join(lines))
    json_path.write_text(
        json.dumps(results, indent=2) + "\n"
    )

    print("\n".join(lines))
    print("GENERATED FILES:")
    print(txt_path.relative_to(ROOT))
    print(json_path.relative_to(ROOT))

    if verdict == "REVIEW REQUIRED":
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError) as error:
        print(f"DIAGNOSIS ERROR: {error}", file=sys.stderr)
        sys.exit(1)
