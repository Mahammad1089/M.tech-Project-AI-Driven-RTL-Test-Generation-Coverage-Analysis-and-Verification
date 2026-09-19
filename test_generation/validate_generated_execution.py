#!/usr/bin/env python3

import json
import sys
from pathlib import Path


def load_json(path):
    file_path = Path(path)

    if not file_path.exists():
        raise FileNotFoundError(
            f"File not found: {path}"
        )

    with file_path.open(
        "r",
        encoding="utf-8",
    ) as f:
        return json.load(f)


def get_validated_tests(data):
    """
    Extract validated scenarios from supported Day-10 formats.

    Supports:
        validated_tests
        scenarios
        validated_scenarios
        tests
        test_cases
    """

    if isinstance(data, list):
        return data

    if not isinstance(data, dict):
        return []

    for key in (
        "validated_tests",
        "scenarios",
        "validated_scenarios",
        "tests",
        "test_cases",
    ):
        value = data.get(key)

        if isinstance(value, list):
            return value

    return []


def get_number(data, keys):
    """
    Return the first numeric field found from a list of keys.
    """

    if not isinstance(data, dict):
        return None

    for key in keys:
        value = data.get(key)

        if value is not None:
            try:
                return int(value)
            except (TypeError, ValueError):
                pass

    return None


def main():
    if len(sys.argv) != 3:
        print(
            "Usage:\n"
            "  python "
            "test_generation/validate_generated_execution.py "
            "<validated_tests.json> "
            "<generated_simulation_report.json>"
        )
        return 2

    validated_path = sys.argv[1]
    simulation_report_path = sys.argv[2]

    try:
        validated_data = load_json(
            validated_path
        )

        simulation_data = load_json(
            simulation_report_path
        )

    except (
        FileNotFoundError,
        json.JSONDecodeError,
    ) as error:
        print(
            "EXECUTION CROSS-CHECK: FAIL"
        )
        print(
            f"ERROR: {error}"
        )
        return 1

    validated_tests = get_validated_tests(
        validated_data
    )

    validated_count = len(
        validated_tests
    )

    simulated_tests = get_number(
        simulation_data,
        (
            "total_tests",
            "simulated_tests",
            "total",
            "test_count",
        ),
    )

    failed_tests = get_number(
        simulation_data,
        (
            "failed_tests",
            "fail_count",
            "failed",
            "fails",
        ),
    )

    passed_tests = get_number(
        simulation_data,
        (
            "passed_tests",
            "pass_count",
            "passed",
            "passes",
        ),
    )

    testbench_result = None

    if isinstance(
        simulation_data,
        dict,
    ):
        testbench_result = (
            simulation_data.get(
                "testbench_result"
            )
            or simulation_data.get(
                "status"
            )
        )

    print(
        "Validated scenarios :",
        validated_count
    )

    print(
        "Simulated tests      :",
        simulated_tests
    )

    print(
        "Passed tests         :",
        passed_tests
    )

    print(
        "Failed tests         :",
        failed_tests
    )

    # --------------------------------------------------------
    # Check required simulation information
    # --------------------------------------------------------

    if simulated_tests is None:
        print(
            "EXECUTION CROSS-CHECK: FAIL"
        )
        print(
            "Simulation report does not contain "
            "a valid total test count."
        )
        return 1

    if failed_tests is None:
        print(
            "EXECUTION CROSS-CHECK: FAIL"
        )
        print(
            "Simulation report does not contain "
            "a valid failed-test count."
        )
        return 1

    # --------------------------------------------------------
    # Count comparison
    # --------------------------------------------------------

    if validated_count != simulated_tests:
        print(
            "EXECUTION CROSS-CHECK: FAIL"
        )
        print(
            "Scenario count does not match "
            "simulation test count."
        )
        return 1

    # --------------------------------------------------------
    # Failure check
    # --------------------------------------------------------

    if failed_tests != 0:
        print(
            "EXECUTION CROSS-CHECK: FAIL"
        )
        print(
            f"{failed_tests} generated test(s) failed."
        )
        return 1

    # --------------------------------------------------------
    # Optional pass-count consistency
    # --------------------------------------------------------

    if (
        passed_tests is not None
        and passed_tests + failed_tests
        != simulated_tests
    ):
        print(
            "EXECUTION CROSS-CHECK: FAIL"
        )
        print(
            "PASS + FAIL count does not match "
            "the total simulated test count."
        )
        return 1

    # --------------------------------------------------------
    # Optional testbench-status check
    # --------------------------------------------------------

    if testbench_result is not None:
        normalized_result = (
            str(testbench_result)
            .strip()
            .upper()
        )

        if normalized_result not in (
            "PASS",
            "SUCCESS",
        ):
            print(
                "EXECUTION CROSS-CHECK: FAIL"
            )
            print(
                "Simulation report status is:",
                testbench_result
            )
            return 1

    print()
    print(
        "EXECUTION CROSS-CHECK: PASS"
    )

    print(
        "All validated scenarios were executed "
        "successfully."
    )

    return 0


if __name__ == "__main__":
    sys.exit(
        main()
    )
