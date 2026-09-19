#!/usr/bin/env python3

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


# ============================================================
# JSON UTILITIES
# ============================================================

def load_json(path: str) -> Any:
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


# ============================================================
# DAY-10 VALIDATED TEST EXTRACTION
# ============================================================

def get_validated_tests(
    data: Any,
) -> List[Dict[str, Any]]:
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
        return [
            item
            for item in data
            if isinstance(item, dict)
        ]

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
            return [
                item
                for item in value
                if isinstance(item, dict)
            ]

    return []


# ============================================================
# INTEGER FIELD EXTRACTION
# ============================================================

def get_integer(
    data: Any,
    keys,
) -> Optional[int]:

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
# STATUS NORMALIZATION
# ============================================================

def get_status(
    data: Any,
) -> Optional[str]:

    if not isinstance(data, dict):
        return None

    value = data.get(
        "status"
    )

    if value is None:
        return None

    return (
        str(value)
        .strip()
        .upper()
    )


# ============================================================
# MAIN VALIDATION
# ============================================================

def main() -> int:

    if len(sys.argv) != 4:

        print(
            "Usage:\n"
            "  python "
            "coverage/validate_execution_source.py "
            "<validated_tests.json> "
            "<generated_simulation_report.json> "
            "<functional_coverage.json>"
        )

        return 2

    validated_path = sys.argv[1]
    simulation_path = sys.argv[2]
    coverage_path = sys.argv[3]

    try:

        validated_data = load_json(
            validated_path
        )

        simulation_data = load_json(
            simulation_path
        )

        coverage_data = load_json(
            coverage_path
        )

    except (
        FileNotFoundError,
        json.JSONDecodeError,
    ) as error:

        print(
            "COVERAGE SOURCE VALIDATION: FAIL"
        )

        print(
            f"ERROR: {error}"
        )

        return 1

    # --------------------------------------------------------
    # Day-10 validated scenarios
    # --------------------------------------------------------

    validated_tests = get_validated_tests(
        validated_data
    )

    validated_count = len(
        validated_tests
    )

    # --------------------------------------------------------
    # Day-11 simulation report
    # --------------------------------------------------------

    simulated_count = get_integer(
        simulation_data,
        (
            "total_tests",
            "simulated_tests",
            "total",
            "test_count",
        ),
    )

    passed_count = get_integer(
        simulation_data,
        (
            "passed_tests",
            "pass_count",
            "passed",
            "passes",
        ),
    )

    failed_count = get_integer(
        simulation_data,
        (
            "failed_tests",
            "fail_count",
            "failed",
            "fails",
        ),
    )

    simulation_status = get_status(
        simulation_data
    )

    # --------------------------------------------------------
    # Day-12 functional coverage report
    # --------------------------------------------------------

    coverage_scenario_count = get_integer(
        coverage_data,
        (
            "validated_scenario_count",
            "validated_scenarios",
            "scenario_count",
            "coverage_scenarios",
        ),
    )

    operation_coverage = None

    if isinstance(
        coverage_data,
        dict,
    ):
        value = coverage_data.get(
            "operation_coverage_percent"
        )

        if value is not None:
            try:
                operation_coverage = float(
                    value
                )
            except (
                TypeError,
                ValueError,
            ):
                operation_coverage = None

    objective_coverage = None

    if isinstance(
        coverage_data,
        dict,
    ):
        value = coverage_data.get(
            "objective_coverage_percent"
        )

        if value is not None:
            try:
                objective_coverage = float(
                    value
                )
            except (
                TypeError,
                ValueError,
            ):
                objective_coverage = None

    coverage_status = get_status(
        coverage_data
    )

    missing_operations = []

    missing_objectives = []

    if isinstance(
        coverage_data,
        dict,
    ):
        missing_operations = (
            coverage_data.get(
                "missing_operations",
                []
            )
            or []
        )

        missing_objectives = (
            coverage_data.get(
                "missing_objectives",
                []
            )
            or []
        )

    # --------------------------------------------------------
    # Evidence report
    # --------------------------------------------------------

    print(
        "COVERAGE SOURCE VALIDATION"
    )

    print(
        "=" * 48
    )

    print(
        "Validated scenarios :",
        validated_count
    )

    print(
        "Simulated tests      :",
        simulated_count
    )

    print(
        "Passed tests         :",
        passed_count
    )

    print(
        "Failed tests         :",
        failed_count
    )

    print(
        "Coverage scenarios   :",
        coverage_scenario_count
    )

    print(
        "Operation coverage   :",
        operation_coverage,
        "%"
    )

    print(
        "Objective coverage   :",
        objective_coverage,
        "%"
    )

    print(
        "Simulation status    :",
        simulation_status
    )

    print(
        "Coverage status      :",
        coverage_status
    )

    print(
        "=" * 48
    )

    # --------------------------------------------------------
    # Validation checks
    # --------------------------------------------------------

    errors = []

    if validated_count <= 0:

        errors.append(
            "No validated scenarios were found."
        )

    if simulated_count is None:

        errors.append(
            "Day-11 simulation test count is missing."
        )

    if coverage_scenario_count is None:

        errors.append(
            "Day-12 coverage scenario count is missing."
        )

    if (
        simulated_count is not None
        and validated_count
        != simulated_count
    ):

        errors.append(
            "Validated scenario count does not "
            "match Day-11 simulation count."
        )

    if (
        coverage_scenario_count is not None
        and validated_count
        != coverage_scenario_count
    ):

        errors.append(
            "Validated scenario count does not "
            "match Day-12 coverage scenario count."
        )

    if (
        simulated_count is not None
        and coverage_scenario_count is not None
        and simulated_count
        != coverage_scenario_count
    ):

        errors.append(
            "Day-11 simulation count does not "
            "match Day-12 coverage count."
        )

    if failed_count is None:

        errors.append(
            "Day-11 failed-test count is missing."
        )

    elif failed_count != 0:

        errors.append(
            f"{failed_count} Day-11 test(s) failed."
        )

    if (
        passed_count is not None
        and failed_count is not None
        and simulated_count is not None
        and (
            passed_count + failed_count
            != simulated_count
        )
    ):

        errors.append(
            "PASS + FAIL does not match "
            "Day-11 total test count."
        )

    if (
        operation_coverage is None
    ):

        errors.append(
            "Operation coverage percentage is missing."
        )

    elif operation_coverage < 100.0:

        errors.append(
            "Operation coverage is below 100%."
        )

    if (
        objective_coverage is None
    ):

        errors.append(
            "Objective coverage percentage is missing."
        )

    elif objective_coverage < 100.0:

        errors.append(
            "Objective coverage is below 100%."
        )

    if missing_operations:

        errors.append(
            "Functional coverage contains "
            "missing operations."
        )

    if missing_objectives:

        errors.append(
            "Functional coverage contains "
            "missing objectives."
        )

    if (
        simulation_status is not None
        and simulation_status
        not in (
            "PASS",
            "SUCCESS",
        )
    ):

        errors.append(
            "Day-11 simulation report is not PASS."
        )

    if (
        coverage_status is not None
        and coverage_status
        not in (
            "PASS",
            "COMPLETE",
        )
    ):

        errors.append(
            "Day-12 functional coverage report "
            "is not PASS."
        )

    # --------------------------------------------------------
    # Final result
    # --------------------------------------------------------

    if errors:

        print()

        print(
            "COVERAGE SOURCE VALIDATION: FAIL"
        )

        for error in errors:
            print(
                " -",
                error
            )

        return 1

    print()

    print(
        "COVERAGE SOURCE VALIDATION: PASS"
    )

    print(
        "Day-12 coverage is traceable to the same "
        "validated scenarios executed in Day 11."
    )

    return 0


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    sys.exit(
        main()
    )
