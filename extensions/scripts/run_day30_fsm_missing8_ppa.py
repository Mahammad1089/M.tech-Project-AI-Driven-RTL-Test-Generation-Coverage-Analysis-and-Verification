#!/usr/bin/env python3
"""Day 30 FSM PPA extension: 8 new variants + 12 existing (read-only) records.

Requires the original Day 26 mapped PPA report, the completed 20-case
functional matrix, Yosys, OpenSTA (`sta`), and Nangate45 typical Liberty.

Run from ~/Mtech_project/AI_RTL_Verification:
    python3 extensions/scripts/run_day30_fsm_missing8_ppa.py

Only writes in extensions/results/day30/fsm_ppa_extension/.
"""

from __future__ import annotations

import csv
import json
import math
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path.home() / "Mtech_project/AI_RTL_Verification"
DAY26 = ROOT / "extensions/results/day26/ppa"
DAY26_SUMMARY = ROOT / "extensions/results/day26/day26_fsm_ppa_summary.csv"
MATRIX_CSV = ROOT / "extensions/results/day30/fsm_20_matrix/day30_fsm_20_matrix_results.csv"
MATRIX_DIR = MATRIX_CSV.parent
OUT = ROOT / "extensions/results/day30/fsm_ppa_extension"
LIB = ROOT / "extensions/technology/nangate45/NangateOpenCellLibrary_typical.lib"

PATTERNS = ("1011", "1101", "1001", "10101", "1110")
MISSING_PATTERNS = ("1001", "1110")
ARCHITECTURES = {
    "mealy": ("extensions/rtl/fsm_variants/fsm_mealy_ext.v", "fsm_mealy_ext"),
    "moore": ("extensions/rtl/fsm_variants/fsm_moore_ext.v", "fsm_moore_ext"),
}

CLOCK_NS = 10.0
INPUT_DELAY_NS = 0.2
OUTPUT_DELAY_NS = 0.2
GLOBAL_ACTIVITY = 0.1
DUTY_CYCLE = 0.5

NUMBER = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?"
AREA_RE = re.compile(r"Chip area for module[^\n:]*:\s*(" + NUMBER + r")", re.I)
SLACK_RE = re.compile(r"(?m)^\s*(" + NUMBER + r")\s+slack\s+\((MET|VIOLATED)\)\s*$")
POWER_RE = re.compile(
    r"(?m)^\s*Total\s+(" + NUMBER + r")\s+(" + NUMBER + r")\s+("
    + NUMBER + r")\s+(" + NUMBER + r")(?:\s|$)"
)
ERROR_RE = re.compile(r"(?im)^\s*(?:Error:|STA Error:)")
FIELDS = (
    "configuration", "area_um2", "startpoint", "endpoint", "setup_slack_ns",
    "data_arrival_ns", "internal_power_uw", "switching_power_uw",
    "leakage_power_uw", "total_power_uw", "timing_status", "mapping_log",
    "timing_log", "power_log",
)


def required_cases():
    return {
        f"{arch}_{pattern}_overlap_{overlap}"
        for pattern in PATTERNS for arch in ARCHITECTURES for overlap in (0, 1)
    }


def case_to_matrix_id(case):
    match = re.fullmatch(r"(mealy|moore)_([01]+)_overlap_([01])", case)
    if not match:
        raise ValueError(f"Invalid FSM case name: {case}")
    arch, pat, overlap = match.groups()
    return f"{arch}_{pat}_{'overlap' if overlap == '1' else 'nonoverlap'}"


def rel(path):
    return str(path.relative_to(ROOT))


def read_csv(path):
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError(f"Missing/empty evidence file: {path}")
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        records = list(reader)
    if not reader.fieldnames or not records:
        raise ValueError(f"CSV empty or missing header: {path}")
    return records


def positive_number(row, field, name):
    try:
        result = float(row[field])
    except (ValueError, TypeError, KeyError) as exc:
        raise ValueError(f"{name} has invalid {field}: {row.get(field)}") from exc
    if not math.isfinite(result) or result <= 0:
        raise ValueError(f"{name} has nonpositive/nonfinite {field}: {result}")
    return result


def check_preconditions():
    import shutil
    for command in ("yosys", "sta"):
        if shutil.which(command) is None:
            raise ValueError(f"Required command not installed: {command}")
    for path in [LIB, DAY26_SUMMARY, MATRIX_CSV]:
        if not path.is_file():
            raise ValueError(f"Missing required file: {path}")
    for arch, (rtl, _) in ARCHITECTURES.items():
        if not (ROOT / rtl).is_file():
            raise ValueError(f"Missing {arch} RTL: {rtl}")

    # Validate preexisting Day 26 summary, without changing its artifacts.
    older = read_csv(DAY26_SUMMARY)
    old_cases = {r.get("configuration") for r in older}
    expected_old = {
        f"{arch}_{pat}_overlap_{ov}"
        for arch in ARCHITECTURES
        for pat in ("1011", "1101", "10101")
        for ov in (0, 1)
    } | {"fsm_original_1011"}
    if len(older) != 13 or old_cases != expected_old:
        raise ValueError("Day 26 summary is not exactly the expected original 13 records")
    for record in older:
        case = record["configuration"]
        for field in ("area_um2", "total_power_uw"):
            positive_number(record, field, case)
        if record.get("timing_status") != "MET":
            raise ValueError(f"Day 26 timing not MET: {case}")
        if not (DAY26 / f"{case}_mapped.v").is_file():
            raise ValueError(f"Day 26 mapped netlist missing for {case}")
        for field in ("mapping_log", "timing_log", "power_log"):
            if not (ROOT / record[field]).is_file():
                raise ValueError(f"Day 26 {field} missing for {case}")

    # Testbench regression is evidence of tests, not independent coverage proof.
    functional = read_csv(MATRIX_CSV)
    expected_matrix = {case_to_matrix_id(case) for case in required_cases()}
    ids = [r.get("case_id") for r in functional]
    if len(ids) != 20 or set(ids) != expected_matrix or len(set(ids)) != 20:
        raise ValueError("20-case functional matrix has missing, duplicate or extra cases")
    for row in functional:
        case_id = row["case_id"]
        if row.get("result") != "PASS":
            raise ValueError(f"Functional matrix has non-PASS case: {case_id}")
        evidence_log = MATRIX_DIR / f"{case_id}.log"
        if not evidence_log.is_file() or evidence_log.stat().st_size == 0:
            raise ValueError(f"Functional case log missing: {evidence_log}")

    print("[PASS] Day 26 reference: original + 12 mapped variants")
    print("[PASS] FSM functional matrix: 20/20 PASS with logs present")
    print("[PASS] Original Day 26 artifacts are read-only")
    return older


def invoke(args, logfile, timeout):
    try:
        result = subprocess.run(
            args, cwd=ROOT, text=True, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, timeout=timeout, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ValueError(f"Execution failed: {' '.join(map(str, args[:3]))}: {exc}") from exc
    logfile.write_text(result.stdout, encoding="utf-8")
    if result.returncode != 0:
        raise ValueError(f"Command exited {result.returncode}: {logfile}\n{result.stdout[-1200:]}")
    if ERROR_RE.search(result.stdout):
        errors = [line for line in result.stdout.splitlines() if ERROR_RE.search(line)]
        raise ValueError(f"Errors in {logfile}: {errors[:6]}")
    return result.stdout


def synthesize(case, arch, pattern, overlap):
    rtl_rel, top = ARCHITECTURES[arch]
    mapped = OUT / f"{case}_mapped.v"
    log = OUT / f"{case}_mapping.log"
    console = OUT / f"{case}_console.log"
    params = f"chparam -set LENGTH {len(pattern)} -set PATTERN {int(pattern, 2)} -set OVERLAP {overlap} {top};"
    yosys_script = f"""
read_verilog -sv {rtl_rel};
{params}
hierarchy -check -top {top};
synth -top {top} -noabc;
dfflibmap -liberty {rel(LIB)};
abc -liberty {rel(LIB)};
clean;
check;
stat -liberty {rel(LIB)};
write_verilog -noattr -noexpr {rel(mapped)};
"""
    invoke(["yosys", "-Q", "-T", "-l", str(log), "-p", yosys_script], console, 180)
    if not log.is_file() or not mapped.is_file() or mapped.stat().st_size == 0:
        raise ValueError(f"Missing synthesis log/netlist: {case}")
    text = log.read_text(encoding="utf-8", errors="replace")
    areas = AREA_RE.findall(text)
    if not areas:
        raise ValueError(f"No Nangate45 chip area found: {log}")
    area = float(areas[-1])
    if not math.isfinite(area) or area <= 0:
        raise ValueError(f"Invalid Nangate45 chip area for {case}: {area}")
    return mapped, top, area, log


def timing(case, mapped, top):
    tcl = OUT / f"{case}_sta.tcl"
    log = OUT / f"{case}_timing.log"
    # Same Day 26 clock, I/O delays, reset exclusion, path-count settings.
    tcl.write_text(f"""
read_liberty {rel(LIB)}
read_verilog {rel(mapped)}
link_design {top}
create_clock -name fsm_clk -period {CLOCK_NS} [get_ports clk]
set_input_delay {INPUT_DELAY_NS} -clock fsm_clk [get_ports din]
set_output_delay {OUTPUT_DELAY_NS} -clock fsm_clk [get_ports detected]
set_false_path -from [get_ports rst]
puts "MAXIMUM_TIMING_PATHS_BEGIN"
report_checks -path_delay max -group_count 10
puts "MAXIMUM_TIMING_PATHS_END"
puts "MINIMUM_TIMING_PATHS_BEGIN"
report_checks -path_delay min -group_count 10
puts "MINIMUM_TIMING_PATHS_END"
puts "TIMING ANALYSIS COMPLETED"
""", encoding="utf-8")
    text = invoke(["sta", "-exit", str(tcl)], log, 120)
    if "TIMING ANALYSIS COMPLETED" not in text:
        raise ValueError(f"Missing timing completion marker for {case}")
    try:
        max_paths = text.split("MAXIMUM_TIMING_PATHS_BEGIN", 1)[1].split("MAXIMUM_TIMING_PATHS_END", 1)[0]
    except IndexError as exc:
        raise ValueError(f"Missing maximum-path section for {case}") from exc

    # Split independent max-delay paths and identify the one with smallest slack.
    paths = re.split(r"(?=^Startpoint:)", max_paths, flags=re.MULTILINE)
    candidates = []
    for path in paths:
        if not path.startswith("Startpoint:"):
            continue
        slacks = SLACK_RE.findall(path)
        if len(slacks) != 1:
            raise ValueError(f"Unexpected slack line count in {case} max path")
        slack_str, status = slacks[0]
        start = re.search(r"(?m)^Startpoint:\s*(.*)$", path)
        end = re.search(r"(?m)^Endpoint:\s*(.*)$", path)
        arrival = re.search(r"(?m)^\s*(" + NUMBER + r")\s+data arrival time\s*$", path)
        if not (start and end and arrival):
            raise ValueError(f"Incomplete timing path in {case}")
        candidates.append((float(slack_str), status, start.group(1), end.group(1), float(arrival.group(1))))
    if not candidates:
        raise ValueError(f"No parsable maximum paths: {case}")
    worst = min(candidates, key=lambda item: item[0])
    if worst[1] != "MET" or worst[0] < 0:
        raise ValueError(f"Timing violation {case}: {worst[0]} ns ({worst[1]})")
    if any(status == "VIOLATED" for _, status, *_ in candidates):
        raise ValueError(f"A reported setup path is violated: {case}")
    return {"setup_slack_ns": worst[0], "startpoint": worst[2],
            "endpoint": worst[3], "data_arrival_ns": worst[4],
            "timing_status": "MET", "timing_log": rel(log)}


def power(case, mapped, top):
    tcl = OUT / f"{case}_power.tcl"
    log = OUT / f"{case}_power.log"
    # EXACT Day 26 command: -global -activity 0.1. DO NOT replace with
    # UART/FIFO's -input -activity 1.0 (incomparable assumption).
    tcl.write_text(f"""
read_liberty {rel(LIB)}
read_verilog {rel(mapped)}
link_design {top}
create_clock -name fsm_clk -period {CLOCK_NS} [get_ports clk]
set_input_delay {INPUT_DELAY_NS} -clock fsm_clk [get_ports din]
set_output_delay {OUTPUT_DELAY_NS} -clock fsm_clk [get_ports detected]
set_false_path -from [get_ports rst]
puts "FSM POWER ANALYSIS"
puts "Activity setting: set_power_activity -global -activity {GLOBAL_ACTIVITY} -duty {DUTY_CYCLE}"
set_power_activity -global -activity {GLOBAL_ACTIVITY} -duty {DUTY_CYCLE}
puts "POWER_REPORT_BEGIN"
report_power
puts "POWER_REPORT_END"
puts "POWER ANALYSIS COMPLETED"
""", encoding="utf-8")
    text = invoke(["sta", "-exit", str(tcl)], log, 120)
    if "POWER ANALYSIS COMPLETED" not in text:
        raise ValueError(f"Missing power completion marker for {case}")
    try:
        section = text.split("POWER_REPORT_BEGIN", 1)[1].split("POWER_REPORT_END", 1)[0]
    except IndexError as exc:
        raise ValueError(f"Power report markers missing: {case}") from exc
    matches = POWER_RE.findall(section)
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one total-power row for {case}; found {len(matches)}. Log: {log}")
    internal, switching, leakage, total = [float(x) for x in matches[0]]
    if any(not math.isfinite(x) or x < 0 for x in (internal, switching, leakage, total)) or total <= 0:
        raise ValueError(f"Invalid power components for {case}")
    if abs((internal + switching + leakage) - total) > max(total * 0.02, 1e-10):
        raise ValueError(f"Power components do not add up for {case}")
    return {"internal_power_uw": internal * 1e6,
            "switching_power_uw": switching * 1e6,
            "leakage_power_uw": leakage * 1e6,
            "total_power_uw": total * 1e6,
            "power_log": rel(log)}


def main():
    if not ROOT.is_dir():
        raise ValueError(f"Project directory missing: {ROOT}")
    print("=" * 72, flush=True)
    print("DAY 30 STEP 6D - MISSING EIGHT FSM PPA + 20-CASE MERGE", flush=True)
    print("=" * 72, flush=True)
    older = check_preconditions()
    OUT.mkdir(parents=True, exist_ok=True)

    new_records = []
    failures = []
    for pattern in MISSING_PATTERNS:
        for arch in ARCHITECTURES:
            for overlap in (0, 1):
                case = f"{arch}_{pattern}_overlap_{overlap}"
                print(f"\n========== FSM PPA: {case.upper()} ==========", flush=True)
                try:
                    mapped, top, area, mapping_log = synthesize(case, arch, pattern, overlap)
                    print(f"[PASS] Mapping, area={area:.3f} um^2", flush=True)
                    timing_data = timing(case, mapped, top)
                    print(f"[PASS] Timing, slack={timing_data['setup_slack_ns']:.3f} ns", flush=True)
                    power_data = power(case, mapped, top)
                    print(f"[PASS] Power, total={power_data['total_power_uw']:.3f} uW", flush=True)
                    record = {"configuration": case, "area_um2": area,
                              **timing_data, **power_data, "mapping_log": rel(mapping_log)}
                    new_records.append(record)
                except (ValueError, OSError, KeyError) as exc:
                    print(f"[FAIL] {case}: {exc}", flush=True)
                    failures.append({"configuration": case, "error": str(exc)})

    # Preserve partial failure evidence; never pretend incomplete coverage passes.
    failures_path = OUT / "day30_fsm_missing8_failures.json"
    failures_path.write_text(json.dumps(failures, indent=2) + "\n", encoding="utf-8")
    if failures:
        print(f"\n[FAIL] Missing-eight PPA incomplete: {len(new_records)}/8 passed", flush=True)
        print("Failure record:", failures_path, flush=True)
        return 1

    old_ext = [row for row in older if row["configuration"] != "fsm_original_1011"]
    joined = old_ext + new_records
    names = [row["configuration"] for row in joined]
    if len(joined) != 20 or len(set(names)) != 20 or set(names) != required_cases():
        raise ValueError("Combined 20-case PPA has missing, duplicate, or extra configurations")
    for row in joined:
        if row["timing_status"] != "MET":
            raise ValueError(f"Timing status not MET: {row['configuration']}")
        for col in ("area_um2", "total_power_uw"):
            positive_number(row, col, row["configuration"])

    new_csv = OUT / "day30_fsm_missing8_ppa.csv"
    joined_csv = OUT / "day30_fsm_20_ppa_summary.csv"
    for path, records in ((new_csv, new_records), (joined_csv, joined)):
        with path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=FIELDS, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(records)

    original = next(row for row in older if row["configuration"] == "fsm_original_1011")
    report = {
        "status": "PASS", "functional_matrix": "20/20 existing testbench PASS",
        "mapping_and_ppa": "20/20 extended variants with area, setup timing and estimated power",
        "original_reference_separate": original,
        "old_extended_cases_reused": 12,
        "new_extended_cases_measured": 8,
        "technology": "Nangate45 typical",
        "clock_period_ns": CLOCK_NS,
        "input_delay_ns": INPUT_DELAY_NS,
        "output_delay_ns": OUTPUT_DELAY_NS,
        "power_activity_command": f"set_power_activity -global -activity {GLOBAL_ACTIVITY} -duty {DUTY_CYCLE}",
        "records": joined,
        "limitations": [
            "Power uses assumed global activity, not VCD/SAIF-derived activity.",
            "The original Day 26 script labels activity as transitions/ns; the tool's unit interpretation is not independently verified here.",
            "Area, timing and power are pre-layout estimates using Nangate45 typical.",
            "Only setup (max-path) timing status is accepted, hold is not certified.",
            "Existing parameterized testbench PASS does not independently prove positive-detection, overlap and reset coverage.",
        ],
    }
    joined_json = OUT / "day30_fsm_20_ppa_summary.json"
    joined_json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print("\n========== FSM PPA FINAL SUMMARY ==========")
    print("PREEXISTING EXTENDED CONFIGURATIONS: 12")
    print("NEW CONFIGURATIONS COMPLETED: 8")
    print("TOTAL EXTENDED CONFIGURATIONS: 20/20")
    print("ORIGINAL REFERENCE KEPT SEPARATE: 1")
    print("SETUP TIMING MET: 20/20")
    print("NEW-ONLY CSV:", new_csv)
    print("COMBINED CSV:", joined_csv)
    print("COMBINED JSON:", joined_json)
    print("DAY 30 FSM 20-CONFIGURATION PPA: PASS")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, OSError, KeyError) as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        sys.exit(1)
