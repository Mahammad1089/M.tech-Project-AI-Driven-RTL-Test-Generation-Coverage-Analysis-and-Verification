#!/usr/bin/env python3

import json
import sys
from pathlib import Path


# ============================================================
# JSON HELPERS
# ============================================================

def load_json(path):
    file_path = Path(path)

    if not file_path.exists():
        raise FileNotFoundError(
            f"File not found: {path}"
        )

    with file_path.open(
        "r",
        encoding="utf-8"
    ) as f:
        data = json.load(f)

    return data


# ============================================================
# TEST EXTRACTION
# ============================================================

def extract_tests(data):
    """
    Supports the JSON formats used throughout the project.

    Accepted:
      [...]
      {"revalidated_tests": [...]}
      {"validated_tests": [...]}
      {"scenarios": [...]}
      {"tests": [...]}
      {"test_cases": [...]}
    """

    if isinstance(data, list):
        return data

    if not isinstance(data, dict):
        return []

    for key in (
        "revalidated_tests",
        "validated_tests",
        "scenarios",
        "tests",
        "test_cases",
        "combined_tests",
    ):
        value = data.get(key)

        if isinstance(value, list):
            return value

    return []


# ============================================================
# INTEGER EXTRACTION
# ============================================================

def get_integer(data, keys):
    if not isinstance(data, dict):
        return None

    for key in keys:
        value = data.get(key)

        if value is None:
            continue

        try:
            return int(value)

        except (
            TypeError,
            ValueError,
        ):
            continue

    return None


# ============================================================
# STATUS EXTRACTION
# ============================================================

def get_status(data):
    if not isinstance(data, dict):
        return ""

    value = data.get("status")

    if value is None:
        value = data.get(
            "simulation_status"
        )

    if value is None:
        value = data.get(
            "result"
        )

    if value is None:
        return ""

    return str(value).strip().upper()


# ============================================================
# MAIN
# ============================================================

def main():

    if len(sys.argv) != 3:
        print(
            "Usage:\n"
            "  python "
            "test_generation/validate_day15_execution.py "
            "<revalidated_tests.json> "
            "<closed_loop_simulation_report.json>"
        )
        return 2

    test_path = sys.argv[1]
    simulation_path = sys.argv[2]

    try:
        test_data = load_json(
            test_path
        )

        simulation_data = load_json(
            simulation_path
        )

    except (
        FileNotFoundError,
        json.JSONDecodeError,
    ) as error:

        print(
            "DAY 15 EXECUTION VALIDATION: FAIL"
        )

        print(
            f"ERROR: {error}"
        )

        return 1

    # ========================================================
    # REVALIDATED TESTS
    # ========================================================

    tests = extract_tests(
        test_data
    )

    revalidated_count = len(
        tests
    )

    if revalidated_count == 0:
        print(
            "DAY 15 EXECUTION VALIDATION: FAIL"
        )

        print(
            "ERROR: No revalidated tests."
        )

        return 1

    # ========================================================
    # SIMULATION COUNTS
    # ========================================================

    simulated_tests = get_integer(
        simulation_data,
        (
            "simulated_tests",
            "total_tests",
            "test_count",
            "total",
            "executed_tests",
        )
    )

    passed_tests = get_integer(
        simulation_data,
        (
            "passed_tests",
            "pass_count",
            "passed",
            "passes",
        )
    )

    failed_tests = get_integer(
        simulation_data,
        (
            "failed_tests",
            "fail_count",
            "failed",
            "fails",
        )
    )

    simulation_status = get_status(
        simulation_data
    )

    # ========================================================
    # FALLBACK DERIVATION
    # ========================================================

    if (
        simulated_tests is None
        and passed_tests is not None
        and failed_tests is not None
    ):
        simulated_tests = (
            passed_tests
            + failed_tests
        )

    if failed_tests is None:
        failed_tests = 0

    if (
        passed_tests is None
        and simulated_tests is not None
    ):
        passed_tests = (
            simulated_tests
            - failed_tests
        )

    # ========================================================
    # DISPLAY
    # ========================================================

    print(
        "DAY 15 EXECUTION VALIDATION"
    )

    print(
        "=" * 52
    )

    print(
        "Revalidated tests     :",
        revalidated_count
    )

    print(
        "Simulated tests       :",
        simulated_tests
    )

    print(
        "Passed tests          :",
        passed_tests
    )

    print(
        "Failed tests          :",
        failed_tests
    )

    print(
        "Simulation status     :",
        simulation_status or "N/A"
    )

    print(
        "=" * 52
    )

    # ========================================================
    # VALIDATION CHECKS
    # ========================================================

    errors = []

    if simulated_tests is None:
        errors.append(
            "Simulation test count is missing."
        )

    elif simulated_tests != revalidated_count:
        errors.append(
            "Revalidated test count does not match "
            "the closed-loop simulation count."
        )

    if passed_tests is None:
        errors.append(
            "Passed-test count is missing."
        )

    if failed_tests is None:
        errors.append(
            "Failed-test count is missing."
        )

    elif failed_tests != 0:
        errors.append(
            f"{failed_tests} test(s) failed during "
            "closed-loop simulation."
        )

    if (
        simulated_tests is not None
        and passed_tests is not None
        and failed_tests is not None
        and (
            passed_tests + failed_tests
            != simulated_tests
        )
    ):
        errors.append(
            "Passed + failed test count does not "
            "match simulated test count."
        )

    if (
        passed_tests is not None
        and passed_tests != revalidated_count
        and failed_tests == 0
    ):
        errors.append(
            "Passed-test count does not match "
            "revalidated test count."
        )

    if (
        simulation_status
        and simulation_status
        not in (
            "PASS",
            "SUCCESS",
            "COMPLETE",
            "COMPLETED",
        )
    ):
        errors.append(
            f"Unexpected simulation status: "
            f"{simulation_status}"
        )

    # ========================================================
    # FINAL RESULT
    # ========================================================

    if errors:

        print()

        print(
            "DAY 15 EXECUTION VALIDATION: FAIL"
        )

        for error in errors:
            print(
                " -",
                error
            )

        return 1

    print()

    print(
        "DAY 15 EXECUTION VALIDATION: PASS"
    )

    print(
        "All revalidated tests were executed "
        "successfully in the closed-loop simulation."
    )

    return 0


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    sys.exit(
        main()
    )
