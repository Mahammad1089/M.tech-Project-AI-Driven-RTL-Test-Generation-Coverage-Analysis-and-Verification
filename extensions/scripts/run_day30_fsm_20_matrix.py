#!/usr/bin/env python3

import csv
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd()

OUT = (
    ROOT
    / "extensions/results/day30/fsm_20_matrix"
)

PATTERNS = [
    "1011",
    "1101",
    "1001",
    "10101",
    "1110",
]

ARCHITECTURES = {
    "mealy": {
        "rtl": (
            "extensions/rtl/fsm_variants/"
            "fsm_mealy_ext.v"
        ),
        "tb": (
            "extensions/testbench/"
            "tb_fsm_mealy_ext.v"
        ),
        "top": "tb_fsm_mealy_ext",
        "pass_marker": (
            "DAY 26 MEALY VERIFICATION: PASS"
        ),
    },
    "moore": {
        "rtl": (
            "extensions/rtl/fsm_variants/"
            "fsm_moore_ext.v"
        ),
        "tb": (
            "extensions/testbench/"
            "tb_fsm_moore_ext.v"
        ),
        "top": "tb_fsm_moore_ext",
        "pass_marker": (
            "DAY 26 MOORE VERIFICATION: PASS"
        ),
    },
}

PARAMETER_PATTERN = re.compile(
    r"PATTERN\s*=\s*([01]+)\s+"
    r"LENGTH\s*=\s*(\d+)\s+"
    r"OVERLAP\s*=\s*(\d+)",
    re.IGNORECASE,
)

FAILURE_PATTERN = re.compile(
    r"(?im)^\s*(?:"
    r"\[FAIL\]|"
    r"DAY\s+26\s+.*VERIFICATION\s*:\s*FAIL|"
    r"FAILED\s+CHECKS\s*:\s*[1-9]\d*"
    r")"
)


def extract_count(text, label):
    match = re.search(
        rf"(?im)^\s*{re.escape(label)}\s*[:=]\s*(\d+)",
        text,
    )

    if match:
        return int(match.group(1))

    return None


def run_case(pattern, architecture, overlap):
    config = ARCHITECTURES[architecture]

    mode = "overlap" if overlap else "nonoverlap"

    case_id = (
        f"{architecture}_{pattern}_{mode}"
    )

    print(
        f"\n========== FSM {case_id.upper()} ==========",
        flush=True,
    )

    rtl = ROOT / config["rtl"]
    tb = ROOT / config["tb"]

    output_file = OUT / f"{case_id}.out"
    compile_log = OUT / f"{case_id}_compile.log"
    sim_log = OUT / f"{case_id}.log"

    record = {
        "case_id": case_id,
        "pattern": pattern,
        "length": len(pattern),
        "architecture": architecture,
        "overlap": overlap,
        "detection_mode": mode,
        "compile_status": "NOT_RUN",
        "simulation_status": "NOT_RUN",
        "parameter_validation": "NOT_RUN",
        "total_checks": None,
        "passed_checks": None,
        "failed_checks": None,
        "result": "FAIL",
        "reason": "",
        "simulation_log": str(
            sim_log.relative_to(ROOT)
        ),
    }

    for path in (rtl, tb):
        if not path.is_file():
            record["reason"] = (
                f"Required file missing: {path}"
            )
            print("[FAIL]", record["reason"])
            return record

    top = config["top"]

    # Decimal numeric override avoids shell quoting
    # problems with Verilog binary literals.
    pattern_value = int(pattern, 2)

    compile_command = [
        "iverilog",
        "-g2012",
        "-s",
        top,
        "-P",
        f"{top}.LENGTH={len(pattern)}",
        "-P",
        f"{top}.PATTERN={pattern_value}",
        "-P",
        f"{top}.OVERLAP={overlap}",
        "-o",
        str(output_file),
        str(rtl),
        str(tb),
    ]

    try:
        compilation = subprocess.run(
            compile_command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        record["reason"] = (
            f"Compilation exception: {exc}"
        )
        print("[FAIL]", record["reason"])
        return record

    compile_output = (
        compilation.stdout
        + "\n"
        + compilation.stderr
    )

    compile_log.write_text(
        compile_output,
        encoding="utf-8",
    )

    if compilation.returncode != 0:
        record["compile_status"] = "FAIL"
        record["reason"] = (
            "Icarus Verilog compilation failed"
        )
        print("[FAIL] Compilation")
        print(compile_output[-1500:])
        return record

    record["compile_status"] = "PASS"
    print("[PASS] Compilation")

    try:
        simulation = subprocess.run(
            ["vvp", str(output_file)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        record["reason"] = (
            f"Simulation exception: {exc}"
        )
        print("[FAIL]", record["reason"])
        return record

    output = (
        simulation.stdout
        + "\n"
        + simulation.stderr
    )

    sim_log.write_text(
        output,
        encoding="utf-8",
    )

    if simulation.returncode != 0:
        record["simulation_status"] = "FAIL"
        record["reason"] = (
            "Simulation returned nonzero exit code"
        )
        print("[FAIL] Simulation")
        print(output[-1500:])
        return record

    record["simulation_status"] = "PASS"

    # Verify the testbench actually received
    # the requested parameters.
    matches = PARAMETER_PATTERN.findall(output)

    expected = (
        pattern,
        str(len(pattern)),
        str(overlap),
    )

    if expected not in matches:
        record["parameter_validation"] = "FAIL"
        record["reason"] = (
            "Requested pattern/length/overlap "
            "not confirmed in simulation output"
        )
        print("[FAIL]", record["reason"])
        print("Expected:", expected)
        print("Observed:", matches[:5])
        return record

    record["parameter_validation"] = "PASS"

    pass_marker = config["pass_marker"]

    if not re.search(
        rf"(?m)^\s*{re.escape(pass_marker)}\s*$",
        output,
    ):
        record["reason"] = (
            "Expected functional PASS marker missing"
        )
        print("[FAIL]", record["reason"])
        print(output[-1500:])
        return record

    if FAILURE_PATTERN.search(output):
        record["reason"] = (
            "Functional failure message detected"
        )
        print("[FAIL]", record["reason"])
        print(output[-1500:])
        return record

    record["total_checks"] = extract_count(
        output, "TOTAL CHECKS"
    )
    record["passed_checks"] = extract_count(
        output, "PASSED CHECKS"
    )
    record["failed_checks"] = extract_count(
        output, "FAILED CHECKS"
    )

    if record["failed_checks"] not in (None, 0):
        record["reason"] = (
            "Nonzero failed-check count"
        )
        print("[FAIL]", record["reason"])
        return record

    total = record["total_checks"]
    passed = record["passed_checks"]
    failed = record["failed_checks"]

    if total is not None and passed is not None:
        if failed is not None and total != passed + failed:
            record["reason"] = (
                "Inconsistent verification counters"
            )
            print("[FAIL]", record["reason"])
            return record

        if total <= 0:
            record["reason"] = (
                "No functional checks reported"
            )
            print("[FAIL]", record["reason"])
            return record

    record["result"] = "PASS"
    record["reason"] = (
        "Existing parameterized testbench passed"
    )

    print("[PASS] Parameter validation")
    print("[PASS] Functional verification")
    print("Pattern:", pattern)
    print("Architecture:", architecture)
    print("Detection mode:", mode)

    if total is not None:
        print("Total checks:", total)

    if passed is not None:
        print("Passed checks:", passed)

    print("Log:", sim_log)

    return record


def main():
    OUT.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("=" * 72)
    print("DAY 30 STEP 6B - COMPLETE FSM FUNCTIONAL MATRIX")
    print("=" * 72)

    results = []

    # 5 patterns × 2 architectures × 2 overlap modes
    for pattern in PATTERNS:
        for architecture in ("mealy", "moore"):
            for overlap in (1, 0):
                result = run_case(
                    pattern,
                    architecture,
                    overlap,
                )

                results.append(result)

    passed = sum(
        row["result"] == "PASS"
        for row in results
    )

    failed = len(results) - passed

    csv_path = OUT / (
        "day30_fsm_20_matrix_results.csv"
    )

    json_path = OUT / (
        "day30_fsm_20_matrix_results.json"
    )

    fields = [
        "case_id",
        "pattern",
        "length",
        "architecture",
        "overlap",
        "detection_mode",
        "compile_status",
        "simulation_status",
        "parameter_validation",
        "total_checks",
        "passed_checks",
        "failed_checks",
        "result",
        "reason",
        "simulation_log",
    ]

    with csv_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fields,
        )

        writer.writeheader()
        writer.writerows(results)

    report = {
        "scope": (
            "Existing parameterized FSM "
            "testbench regression"
        ),
        "required_configurations": 20,
        "executed_configurations": len(results),
        "passed_configurations": passed,
        "failed_configurations": failed,
        "status": (
            "PASS"
            if passed == 20
            else "FAIL"
        ),
        "results": results,
        "limitations": [
            "This stage reuses existing functional testbenches",
            "Independent reference-model coverage is not "
            "established by this runner alone",
            "FSM PPA analysis is not performed",
            "Formal equivalence is not performed",
        ],
    }

    json_path.write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
    )

    print("\n" + "=" * 72)
    print("FSM 20-CONFIGURATION SUMMARY")
    print("=" * 72)

    print("REQUIRED CONFIGURATIONS: 20")
    print(
        "EXECUTED CONFIGURATIONS:",
        len(results),
    )
    print("PASSED CONFIGURATIONS:", passed)
    print("FAILED CONFIGURATIONS:", failed)

    print("\n========== CONFIGURATION RESULTS ==========")

    for row in results:
        print(
            f"{row['case_id']:<30} "
            f"{row['result']}"
        )

    print("\nCSV:", csv_path)
    print("JSON:", json_path)

    if passed == 20:
        print(
            "DAY 30 FSM 20-CONFIGURATION "
            "FUNCTIONAL MATRIX: PASS"
        )
        return 0

    print(
        "DAY 30 FSM 20-CONFIGURATION "
        "FUNCTIONAL MATRIX: FAIL"
    )

    print("\nFAILED CONFIGURATIONS:")

    for row in results:
        if row["result"] == "FAIL":
            print(
                f"  {row['case_id']}: "
                f"{row['reason']}"
            )

    return 1


if __name__ == "__main__":
    sys.exit(main())
