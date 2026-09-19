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


def get_percentage(data, new_key, old_block=None):
    """
    Read percentage from the current Day-12 format,
    while also supporting older nested formats.
    """

    value = data.get(new_key)

    if value is not None:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    if old_block:
        block = data.get(old_block)

        if isinstance(block, dict):
            value = block.get("coverage_percent")

            if value is not None:
                try:
                    return float(value)
                except (TypeError, ValueError):
                    return None

    return None


def main():

    if len(sys.argv) != 2:
        print(
            "Usage:\n"
            "  python coverage/validate_coverage.py "
            "<functional_coverage.json>"
        )
        return 2

    path = sys.argv[1]

    try:
        data = load_json(path)

    except (
        FileNotFoundError,
        json.JSONDecodeError,
    ) as error:

        print("COVERAGE VALIDATION: FAIL")
        print(f"ERROR: {error}")
        return 1

    operation_coverage = get_percentage(
        data,
        "operation_coverage_percent",
        "operation_coverage",
    )

    objective_coverage = get_percentage(
        data,
        "objective_coverage_percent",
        "objective_coverage",
    )

    missing_operations = data.get(
        "missing_operations",
        []
    )

    missing_objectives = data.get(
        "missing_objectives",
        []
    )

    status = str(
        data.get("status", "")
    ).strip().upper()

    validated_scenarios = data.get(
        "validated_scenario_count",
        0
    )

    functional_operations = data.get(
        "functional_operation_count",
        0
    )

    covered_operations = data.get(
        "covered_operation_count",
        0
    )

    objective_count = data.get(
        "objective_count",
        0
    )

    covered_objectives = data.get(
        "covered_objective_count",
        0
    )

    print("COVERAGE VALIDATION")
    print("=" * 45)

    print(
        "Validated scenarios :",
        validated_scenarios
    )

    print(
        "Functional operations:",
        functional_operations
    )

    print(
        "Covered operations  :",
        covered_operations
    )

    print(
        "Operation coverage  :",
        operation_coverage,
        "%"
    )

    print(
        "Objectives          :",
        objective_count
    )

    print(
        "Covered objectives  :",
        covered_objectives
    )

    print(
        "Objective coverage  :",
        objective_coverage,
        "%"
    )

    print(
        "Missing operations  :",
        missing_operations
    )

    print(
        "Missing objectives  :",
        missing_objectives
    )

    print(
        "Coverage status     :",
        status
    )

    print("=" * 45)

    errors = []

    if operation_coverage is None:
        errors.append(
            "Operation coverage percentage is missing."
        )

    if objective_coverage is None:
        errors.append(
            "Objective coverage percentage is missing."
        )

    if validated_scenarios <= 0:
        errors.append(
            "No validated scenarios were found."
        )

    if functional_operations <= 0:
        errors.append(
            "No functional operations were found."
        )

    if objective_count <= 0:
        errors.append(
            "No verification objectives were found."
        )

    if missing_operations:
        errors.append(
            "One or more RTL operations are missing coverage."
        )

    if missing_objectives:
        errors.append(
            "One or more verification objectives are missing coverage."
        )

    if (
        operation_coverage is not None
        and operation_coverage < 100.0
    ):
        errors.append(
            f"Operation coverage is only "
            f"{operation_coverage}%."
        )

    if (
        objective_coverage is not None
        and objective_coverage < 100.0
    ):
        errors.append(
            f"Objective coverage is only "
            f"{objective_coverage}%."
        )

    if status not in ("PASS", "COMPLETE"):
        errors.append(
            f"Functional coverage report status is "
            f"'{status or 'missing'}'."
        )

    if errors:
        print()
        print("COVERAGE VALIDATION: FAIL")

        for error in errors:
            print(" -", error)

        return 1

    print()
    print("COVERAGE VALIDATION: PASS")
    print(
        "All functional operations and verification "
        "objectives are covered."
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
