#!/usr/bin/env python3

import csv
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path.home() / "Mtech_project" / "AI_RTL_Verification"
BASE = ROOT / "extensions/results/day26"
PPA = BASE / "ppa"

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

NUM = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"

passed = 0
failed = 0
warnings = 0
messages = []

def check(condition, message):
    global passed, failed
    if condition:
        passed += 1
        messages.append("[PASS] " + message)
    else:
        failed += 1
        messages.append("[FAIL] " + message)

def warn(message):
    global warnings
    warnings += 1
    messages.append("[WARN] " + message)

def read(path):
    if not path.is_file():
        return None
    return path.read_text(errors="replace")

def close(a, b, tolerance):
    return math.isfinite(a) and math.isfinite(b) and abs(a-b) <= tolerance

def number_after(pattern, text):
    match = re.search(pattern, text, re.I | re.M)
    return float(match.group(1)) if match else None

def main():
    print("=" * 68)
    print("DAY 26 - FINAL INDEPENDENT EVIDENCE VERIFICATION")
    print("=" * 68)

    csv_path = BASE / "day26_fsm_ppa_summary.csv"
    json_path = BASE / "day26_fsm_ppa_summary.json"
    txt_path = BASE / "day26_fsm_ppa_report.txt"

    check(csv_path.is_file(), "CSV report exists")
    check(json_path.is_file(), "JSON report exists")
    check(txt_path.is_file(), "Text report exists")

    if not csv_path.is_file() or not json_path.is_file():
        finish()
        return

    try:
        with csv_path.open(newline="") as f:
            rows = list(csv.DictReader(f))
        data = json.loads(json_path.read_text())
    except (OSError, ValueError, csv.Error) as exc:
        check(False, f"Report parsing: {exc}")
        finish()
        return

    check(len(rows) == 13, "CSV contains 13 configurations")
    check(data.get("configuration_count") == 13,
          "JSON configuration count is 13")
    check(data.get("status") == "PASS", "JSON status is PASS")

    csv_by_name = {r["configuration"]: r for r in rows}
    json_records = data.get("records", [])
    json_by_name = {
        r["configuration"]: r for r in json_records
        if isinstance(r, dict) and "configuration" in r
    }

    check(len(csv_by_name) == len(rows), "No duplicate CSV cases")
    check(len(json_by_name) == 13, "JSON has 13 unique cases")
    check(set(csv_by_name) == set(CASES),
          "CSV case names match required configurations")
    check(set(json_by_name) == set(CASES),
          "JSON case names match required configurations")

    for case in CASES:
        row = csv_by_name.get(case)
        record = json_by_name.get(case)

        if row is None or record is None:
            check(False, f"{case}: missing consolidated record")
            continue

        mapping = read(PPA / f"{case}_mapping.log")
        timing = read(PPA / f"{case}_timing.log")
        power = read(PPA / f"{case}_power.log")
        netlist = PPA / f"{case}_mapped.v"

        check(
            all(x is not None for x in (mapping, timing, power))
            and netlist.is_file() and netlist.stat().st_size > 0,
            f"{case}: all four source artifacts exist"
        )

        if any(x is None for x in (mapping, timing, power)):
            continue

        check(
            not any(
                re.search(r"(?im)^\s*Error:", content)
                for content in (mapping, timing, power)
            ),
            f"{case}: no source-log errors"
        )

        area_matches = re.findall(
            rf"Chip area for module\s+.*?:\s*({NUM})",
            mapping,
            re.I
        )

        area = float(area_matches[-1]) if area_matches else None

        max_section = re.search(
            r"MAXIMUM TIMING PATHS(.*?)MINIMUM TIMING PATHS",
            timing,
            re.S
        )

        section = max_section.group(1) if max_section else ""

        slack = number_after(
            rf"^\s*({NUM})\s+slack\s+\((?:MET|VIOLATED)\)",
            section
        )

        arrival = number_after(
            rf"^\s*({NUM})\s+data arrival time\s*$",
            section
        )

        power_match = re.search(
            rf"^\s*Total\s+({NUM})\s+({NUM})"
            rf"\s+({NUM})\s+({NUM})\s+100\.0%",
            power,
            re.M
        )

        total_uw = (
            float(power_match.group(4)) * 1e6
            if power_match else None
        )

        check(
            area is not None
            and close(area, float(row["area_um2"]), 0.001)
            and close(area, float(record["area_um2"]), 0.001),
            f"{case}: area matches source mapping log"
        )

        check(
            slack is not None
            and slack >= 0
            and close(slack, float(row["setup_slack_ns"]), 0.011)
            and close(slack, float(record["setup_slack_ns"]), 0.011),
            f"{case}: nonnegative setup slack matches timing log"
        )

        check(
            arrival is not None
            and close(arrival, float(row["data_arrival_ns"]), 0.011)
            and close(arrival, float(record["data_arrival_ns"]), 0.011),
            f"{case}: arrival time matches timing log"
        )

        check(
            total_uw is not None
            and close(total_uw, float(row["total_power_uw"]), 0.011)
            and close(total_uw, float(record["total_power_uw"]), 0.011),
            f"{case}: power matches source power log"
        )

        check(
            "TIMING ANALYSIS COMPLETED" in timing
            and "POWER ANALYSIS COMPLETED" in power,
            f"{case}: analysis completion markers present"
        )

    print()
    print("========== FUNCTIONAL EVIDENCE ==========")

    # Discover saved logs only; do not mistake a PPA report
    # for functional verification evidence.
    logs = [
        p for p in BASE.rglob("*.log")
        if "ppa" not in p.relative_to(BASE).parts
    ]

    for family in ("mealy", "moore"):
        evidence = []
        for path in logs:
            content = read(path) or ""
            if re.search(
                rf"DAY\s+26\s+{family.upper()}\s+VERIFICATION:\s+PASS",
                content
            ) and re.search(r"FAILED CHECKS\s*:\s*0", content):
                evidence.append(path)

        if evidence:
            check(True, f"{family}: saved PASS evidence found")
            print(f"{family} evidence files: {len(evidence)}")
        else:
            warn(
                f"{family}: no saved PASS log found; "
                "previous terminal results are not independently "
                "verified by this script"
            )

    warn(
        "Power is based on assumed switching activity; "
        "VCD/SAIF validation is not established"
    )
    warn(
        "Hold closure, post-layout timing and cross-variant "
        "functional equivalence are outside this check"
    )

    finish()

def finish():
    output = [
        "",
        "=" * 68,
        "DAY 26 FINAL VERIFICATION RESULTS",
        "=" * 68,
        *messages,
        "",
        f"Passed checks : {passed}",
        f"Failed checks : {failed}",
        f"Warnings      : {warnings}",
        "",
    ]

    if failed:
        status = "FAIL"
    elif any(
        "no saved PASS log found" in msg
        for msg in messages
    ):
        status = "PPA PASS - FUNCTIONAL EVIDENCE INCOMPLETE"
    else:
        status = "PASS - CHECKED EVIDENCE CONSISTENT"

    output.append("FINAL STATUS: " + status)

    text = "\n".join(output) + "\n"
    print(text)

    BASE.mkdir(parents=True, exist_ok=True)
    path = BASE / "day26_final_verification.txt"
    path.write_text(text)

    print("Saved:", path.relative_to(ROOT))

    if failed:
        sys.exit(1)
    if "INCOMPLETE" in status:
        sys.exit(2)

if __name__ == "__main__":
    main()
