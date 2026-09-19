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
        data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError(
            "Coverage-gap report must contain a JSON object."
        )

    return data


def main():

    if len(sys.argv) != 2:
        print(
            "Usage:\n"
            "  python coverage/validate_gaps.py "
            "<coverage_gaps.json>"
        )
        return 2

    try:
        data = load_json(
            sys.argv[1]
        )

    except (
        FileNotFoundError,
        json.JSONDecodeError,
        ValueError,
    ) as error:

        print("GAP VALIDATION: FAIL")
        print(f"ERROR: {error}")
        return 1

    # --------------------------------------------------------
    # CURRENT DAY-13 FORMAT
    # --------------------------------------------------------

    missing_operations = (
        data.get("missing_operations", [])
        or []
    )

    missing_objectives = (
        data.get("missing_objectives", [])
        or []
    )

    operation_gap_count = len(
        missing_operations
    )

    objective_gap_count = len(
        missing_objectives
    )

    total_gap_count = (
        operation_gap_count
        + objective_gap_count
    )

    gaps_detected = data.get(
        "gaps_detected"
    )

    if gaps_detected is None:
        gaps_detected = (
            total_gap_count > 0
        )

    status = str(
        data.get(
            "status",
            ""
        )
    ).strip().upper()

    operation_coverage = data.get(
        "operation_coverage_percent"
    )

    objective_coverage = data.get(
        "objective_coverage_percent"
    )

    functional_operations = data.get(
        "functional_operation_count"
    )

    covered_operations = data.get(
        "covered_operation_count"
    )

    objective_count = data.get(
        "objective_count"
    )

    covered_objectives = data.get(
        "covered_objective_count"
    )

    validated_scenarios = data.get(
        "validated_scenarios"
    )

    # --------------------------------------------------------
    # TERMINAL REPORT
    # --------------------------------------------------------

    print("GAP VALIDATION")
    print("=" * 50)

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
        "Operation gaps      :",
        operation_gap_count
    )

    print(
        "Objective gaps      :",
        objective_gap_count
    )

    print(
        "Total gaps          :",
        total_gap_count
    )

    print(
        "Gap status          :",
        status
    )

    print("=" * 50)

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    errors = []

    if functional_operations is None:
        errors.append(
            "functional_operation_count is missing."
        )

    if covered_operations is None:
        errors.append(
            "covered_operation_count is missing."
        )

    if objective_count is None:
        errors.append(
            "objective_count is missing."
        )

    if covered_objectives is None:
        errors.append(
            "covered_objective_count is missing."
        )

    if operation_coverage is None:
        errors.append(
            "operation_coverage_percent is missing."
        )

    if objective_coverage is None:
        errors.append(
            "objective_coverage_percent is missing."
        )

    # Internal consistency
    if (
        functional_operations is not None
        and covered_operations is not None
        and operation_gap_count == 0
        and covered_operations
        != functional_operations
    ):
        errors.append(
            "Operation counts are inconsistent."
        )

    if (
        objective_count is not None
        and covered_objectives is not None
        and objective_gap_count == 0
        and covered_objectives
        != objective_count
    ):
        errors.append(
            "Objective counts are inconsistent."
        )

    if (
        gaps_detected is False
        and total_gap_count != 0
    ):
        errors.append(
            "gaps_detected is false but gap lists are not empty."
        )

    if (
        gaps_detected is True
        and total_gap_count == 0
    ):
        errors.append(
            "gaps_detected is true but no gaps are listed."
        )

    # Status consistency
    if total_gap_count == 0:

        if status not in (
            "NO_GAPS",
            "PASS",
            "COMPLETE",
        ):
            errors.append(
                f"Unexpected no-gap status: {status}"
            )

    else:

        if status not in (
            "GAPS_FOUND",
            "INCOMPLETE",
        ):
            errors.append(
                f"Unexpected gap status: {status}"
            )

    # --------------------------------------------------------
    # RESULT
    # --------------------------------------------------------

    if errors:

        print()
        print("GAP VALIDATION: FAIL")

        for error in errors:
            print(" -", error)

        return 1

    print()

    if total_gap_count == 0:

        print("GAP VALIDATION: PASS")
        print(
            "No functional-operation or objective gaps detected."
        )

    else:

        print("GAP VALIDATION: PASS")
        print(
            "Coverage gaps were detected and reported consistently."
        )

        print(
            "Missing operations:",
            missing_operations
        )

        print(
            "Missing objectives:",
            missing_objectives
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
