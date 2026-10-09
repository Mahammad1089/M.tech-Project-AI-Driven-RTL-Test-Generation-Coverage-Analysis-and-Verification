#!/usr/bin/env python3
"""Independent detection/reset/overlap coverage for 20 FSM variants.
Run from project root after installing companion Verilog testbench.
Preserves existing RTL, testbenches, Day 26/30 results.
"""
import csv
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd()
OUT = ROOT / "extensions/results/day30/fsm_independent_coverage"
TB = ROOT / "extensions/testbench/tb_day30_fsm_independent_coverage.v"
RTL = [ROOT / "extensions/rtl/fsm_variants/fsm_mealy_ext.v",
       ROOT / "extensions/rtl/fsm_variants/fsm_moore_ext.v"]
TOP = "tb_day30_fsm_independent_coverage"
PATTERNS = ("1011", "1101", "1001", "10101", "1110")
FIELDS = ("TOTAL CYCLES", "TOTAL CHECKS", "PASSED CHECKS", "FAILED CHECKS",
          "RESET EVENTS", "OVERLAP DETECTIONS", "NONOVERLAP DETECTIONS",
          "OVERLAP NEGATIVE CYCLES", "NONOVERLAP NEGATIVE CYCLES",
          "SUPPRESSED OVERLAP OPPORTUNITIES", "PROPER BORDER LENGTH")
PASS_MARKER = "DAY 30 FSM INDEPENDENT COVERAGE: PASS"


def val(output, name):
    matches = re.findall(r"(?m)^\s*" + re.escape(name) + r":\s*(\d+)\s*$", output)
    if len(matches) != 1:
        raise ValueError(f"Expected one {name}, found {len(matches)}")
    return int(matches[0])


def run_case(pattern):
    name = f"pattern_{pattern}"
    executable = OUT / f"{name}.out"
    compile_log = OUT / f"{name}_compile.log"
    log = OUT / f"{name}.log"
    cmd = ["iverilog", "-g2012", "-s", TOP,
           "-P", f"{TOP}.LENGTH={len(pattern)}",
           "-P", f"{TOP}.PATTERN={int(pattern, 2)}",
           "-o", str(executable), *(str(p) for p in RTL), str(TB)]
    compilation = subprocess.run(cmd, cwd=ROOT, capture_output=True,
                                 text=True, timeout=120)
    compile_log.write_text(compilation.stdout + compilation.stderr, encoding="utf-8")
    if compilation.returncode:
        raise ValueError(f"Compilation failed: {compile_log}\n{compilation.stderr[-1200:]}")
    simulation = subprocess.run(["vvp", str(executable)], cwd=ROOT,
                                capture_output=True, text=True, timeout=180)
    output = simulation.stdout + "\n" + simulation.stderr
    log.write_text(output, encoding="utf-8")
    if simulation.returncode or PASS_MARKER not in output or "[FAIL]" in output:
        raise ValueError(f"Simulation failed: {log}\n{output[-1800:]}")
    if not re.search(rf"(?m)^PATTERN={pattern}\s+LENGTH={len(pattern)}\s+PROPER_BORDER=\d+", output):
        raise ValueError(f"Pattern override not confirmed: {log}")
    counts = {key: val(output, key) for key in FIELDS}
    if counts["FAILED CHECKS"] or counts["TOTAL CHECKS"] != counts["PASSED CHECKS"]:
        raise ValueError(f"Check counters inconsistent: {log}")
    if counts["TOTAL CHECKS"] != 4 * (counts["TOTAL CYCLES"] + counts["RESET EVENTS"]):
        raise ValueError(f"Missing clock-by-clock comparisons: {log}")
    if not all(counts[k] > 0 for k in ("RESET EVENTS", "OVERLAP DETECTIONS",
                                       "NONOVERLAP DETECTIONS", "OVERLAP NEGATIVE CYCLES",
                                       "NONOVERLAP NEGATIVE CYCLES")):
        raise ValueError(f"Insufficient coverage: {log}")
    border = counts["PROPER BORDER LENGTH"]
    suppressed = counts["SUPPRESSED OVERLAP OPPORTUNITIES"]
    if (border > 0 and suppressed <= 0) or (border == 0 and suppressed != 0):
        raise ValueError(f"Overlap-suppression coverage mismatch: {log}")
    print(f"[PASS] {pattern}: checks={counts['PASSED CHECKS']}, "
          f"overlap={counts['OVERLAP DETECTIONS']}, "
          f"nonoverlap={counts['NONOVERLAP DETECTIONS']}, "
          f"suppressed={suppressed}, resets={counts['RESET EVENTS']}", flush=True)
    return {"pattern": pattern, "status": "PASS", "log": str(log.relative_to(ROOT)), **counts}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    print("========== DAY 30 STEP 6E-2: INDEPENDENT FSM COVERAGE ==========")
    required = [TB, *RTL]
    for path in required:
        if not path.is_file():
            print("[FAIL] Missing source:", path)
            return 1
    records = []
    failures = []
    for pattern in PATTERNS:
        try:
            records.append(run_case(pattern))
        except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
            print(f"[FAIL] {pattern}: {exc}", flush=True)
            failures.append({"pattern": pattern, "reason": str(exc)})
    report = {
        "test": "Independent sliding-window FSM detection coverage",
        "required_patterns": len(PATTERNS), "required_variants": 20,
        "tested_variants": len(records) * 4,
        "status": "PASS" if not failures and len(records) == 5 else "FAIL",
        "records": records, "failures": failures,
        "timing": "Mealy compared pre-sampling-edge, Moore post-sampling-edge",
        "coverage_objectives": ["positive detections", "negative comparisons",
                                "reset output and recovery", "overlap suppression where possible"],
        "scope": "Simulation evidence, not formal proof or toggle/state coverage",
    }
    json_file = OUT / "day30_fsm_independent_coverage.json"
    csv_file = OUT / "day30_fsm_independent_coverage.csv"
    json_file.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if records:
        with csv_file.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(records[0]))
            writer.writeheader()
            writer.writerows(records)
    print("\n========== FINAL INDEPENDENT COVERAGE SUMMARY ==========")
    print("PATTERNS PASSED:", len(records), "/5")
    print("VARIANTS COVERED:", len(records) * 4, "/20")
    print("FAILED PATTERNS:", len(failures))
    print("TOTAL CHECKS PASSED:", sum(r["PASSED CHECKS"] for r in records))
    print("JSON:", json_file)
    print("CSV:", csv_file if records else "not generated")
    print("DAY 30 FSM INDEPENDENT COVERAGE:", report["status"])
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
