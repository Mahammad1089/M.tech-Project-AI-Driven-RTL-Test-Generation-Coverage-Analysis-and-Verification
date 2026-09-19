#!/usr/bin/env python3

import json
import re
import sys
from pathlib import Path


def load_log(path):
    file_path = Path(path)

    if not file_path.exists():
        raise FileNotFoundError(
            f"Simulation log not found: {path}"
        )

    return file_path.read_text(
        encoding="utf-8",
        errors="replace"
    )


def find_number(text, patterns):
    """
    Search several possible summary formats and return
    the first integer found.
    """

    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE | re.MULTILINE
        )

        if match:
            return int(match.group(1))

    return None


def parse_result(text):
    """
    Parse generated ALU simulation output.

    Supported examples:

        PASS = 29
        FAIL = 0
        TOTAL = 29

    and:

        PASS TESTS = 29
        FAILED TESTS = 0
        TOTAL TESTS = 29
    """

    passed = find_number(
        text,
        [
            r"^\s*PASS\s*=\s*(\d+)\s*$",
            r"^\s*PASS(?:ED)?\s+TESTS?\s*[:=]\s*(\d+)\s*$",
            r"^\s*TESTS?\s+PASSED\s*[:=]\s*(\d+)\s*$",
        ]
    )

    failed = find_number(
        text,
        [
            r"^\s*FAIL\s*=\s*(\d+)\s*$",
            r"^\s*FAIL(?:ED)?\s+TESTS?\s*[:=]\s*(\d+)\s*$",
            r"^\s*TESTS?\s+FAILED\s*[:=]\s*(\d+)\s*$",
        ]
    )

    total = find_number(
        text,
        [
            # Current generated testbench format
            r"^\s*TOTAL\s*=\s*(\d+)\s*$",

            # Older/alternate formats
            r"^\s*TOTAL\s+TESTS?\s*[:=]\s*(\d+)\s*$",
            r"^\s*TESTS?\s+TOTAL\s*[:=]\s*(\d+)\s*$",
        ]
    )

    # If TOTAL is absent but PASS and FAIL are present,
    # calculate it safely.
    if total is None:
        if passed is not None and failed is not None:
            total = passed + failed

    result_match = re.search(
        r"TESTBENCH\s+RESULT\s*:\s*(PASS|FAIL)",
        text,
        flags=re.IGNORECASE
    )

    testbench_result = (
        result_match.group(1).upper()
        if result_match
        else None
    )

    return {
        "passed": passed,
        "failed": failed,
        "total": total,
        "testbench_result": testbench_result,
    }


def main():
    if len(sys.argv) != 3:
        print(
            "Usage:\n"
            "  python simulation/generated_result_parser.py "
            "<generated_simulation.log> "
            "<generated_simulation_report.json>"
        )
        return 2

    log_path = sys.argv[1]
    report_path = sys.argv[2]

    try:
        text = load_log(log_path)

    except FileNotFoundError as error:
        print("GENERATED RESULT PARSER: FAIL")
        print(f"ERROR: {error}")
        return 1

    result = parse_result(text)

    passed = result["passed"]
    failed = result["failed"]
    total = result["total"]
    testbench_result = result["testbench_result"]

    if total is None:
        print("GENERATED RESULT PARSER: FAIL")
        print(
            "ERROR: Could not find TOTAL/TOTAL TESTS "
            "in simulation log."
        )
        return 1

    if passed is None:
        print("GENERATED RESULT PARSER: FAIL")
        print(
            "ERROR: Could not find PASS count "
            "in simulation log."
        )
        return 1

    if failed is None:
        print("GENERATED RESULT PARSER: FAIL")
        print(
            "ERROR: Could not find FAIL count "
            "in simulation log."
        )
        return 1

    # Consistency check
    count_consistent = (
        passed + failed == total
    )

    if testbench_result is None:
        testbench_result = (
            "PASS"
            if failed == 0 and count_consistent
            else "FAIL"
        )

    parser_status = (
        "PASS"
        if (
            failed == 0
            and count_consistent
            and testbench_result == "PASS"
        )
        else "FAIL"
    )

    report = {
        "simulation_log": log_path,
        "total_tests": total,
        "passed_tests": passed,
        "failed_tests": failed,
        "testbench_result": testbench_result,
        "count_consistent": count_consistent,
        "status": parser_status,
    }

    output_path = Path(report_path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    output_path.write_text(
        json.dumps(
            report,
            indent=2
        ),
        encoding="utf-8"
    )

    print(
        "Total tests :",
        total
    )

    print(
        "Passed      :",
        passed
    )

    print(
        "Failed      :",
        failed
    )

    print(
        "TB result   :",
        testbench_result
    )

    print(
        "Counts valid:",
        count_consistent
    )

    print()

    if parser_status == "PASS":
        print(
            "GENERATED RESULT PARSER: PASS"
        )
        return 0

    print(
        "GENERATED RESULT PARSER: FAIL"
    )

    return 1


if __name__ == "__main__":
    sys.exit(main())
