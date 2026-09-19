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
            f"JSON file must contain an object: {path}"
        )

    return data


def get_float(data, new_key, old_key=None):
    """
    Read current Day-12/Day-13 percentage fields,
    while also supporting the older nested format.
    """

    value = data.get(new_key)

    if value is not None:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    if old_key:
        old_value = data.get(old_key)

        if isinstance(old_value, dict):
            value = old_value.get(
                "coverage_percent"
            )

            if value is not None:
                try:
                    return float(value)
                except (TypeError, ValueError):
                    return None

    return None


def normalize_list(value):
    if not value:
        return []

    if not isinstance(value, list):
        return []

    return sorted(
        str(item)
        for item in value
    )


def main():

    if len(sys.argv) != 3:

        print(
            "Usage:\n"
            "  python coverage/validate_gap_source.py "
            "<functional_coverage.json> "
            "<coverage_gaps.json>"
        )

        return 2

    try:

        coverage = load_json(
            sys.argv[1]
        )

        gaps = load_json(
            sys.argv[2]
        )

    except (
        FileNotFoundError,
        json.JSONDecodeError,
        ValueError,
    ) as error:

        print(
            "GAP SOURCE VALIDATION: FAIL"
        )

        print(
            f"ERROR: {error}"
        )

        return 1

    # ========================================================
    # DAY-12 FUNCTIONAL COVERAGE
    # ========================================================

    coverage_operation_percent = get_float(
        coverage,
        "operation_coverage_percent",
        "operation_coverage",
    )

    coverage_objective_percent = get_float(
        coverage,
        "objective_coverage_percent",
        "objective_coverage",
    )

    coverage_missing_operations = normalize_list(
        coverage.get(
            "missing_operations",
            []
        )
    )

    coverage_missing_objectives = normalize_list(
        coverage.get(
            "missing_objectives",
            []
        )
    )

    coverage_validated_scenarios = coverage.get(
        "validated_scenario_count"
    )

    coverage_functional_operations = coverage.get(
        "functional_operation_count"
    )

    coverage_covered_operations = coverage.get(
        "covered_operation_count"
    )

    coverage_objective_count = coverage.get(
        "objective_count"
    )

    coverage_covered_objectives = coverage.get(
        "covered_objective_count"
    )

    coverage_status = str(
        coverage.get(
            "status",
            ""
        )
    ).strip().upper()

    # ========================================================
    # DAY-13 GAP ANALYSIS
    # ========================================================

    gap_operation_percent = get_float(
        gaps,
        "operation_coverage_percent",
        "operation_coverage",
    )

    gap_objective_percent = get_float(
        gaps,
        "objective_coverage_percent",
        "objective_coverage",
    )

    gap_missing_operations = normalize_list(
        gaps.get(
            "missing_operations",
            gaps.get(
                "operation_gaps",
                []
            )
        )
    )

    gap_missing_objectives = normalize_list(
        gaps.get(
            "missing_objectives",
            gaps.get(
                "objective_gaps",
                []
            )
        )
    )

    gap_validated_scenarios = gaps.get(
        "validated_scenarios"
    )

    gap_functional_operations = gaps.get(
        "functional_operation_count"
    )

    gap_covered_operations = gaps.get(
        "covered_operation_count"
    )

    gap_objective_count = gaps.get(
        "objective_count"
    )

    gap_covered_objectives = gaps.get(
        "covered_objective_count"
    )

    gap_status = str(
        gaps.get(
            "status",
            ""
        )
    ).strip().upper()

    gaps_detected = gaps.get(
        "gaps_detected"
    )

    # ========================================================
    # DISPLAY
    # ========================================================

    print(
        "GAP SOURCE VALIDATION"
    )

    print(
        "=" * 52
    )

    print(
        "Day-12 validated scenarios :",
        coverage_validated_scenarios
    )

    print(
        "Day-13 validated scenarios :",
        gap_validated_scenarios
    )

    print(
        "Day-12 functional ops      :",
        coverage_functional_operations
    )

    print(
        "Day-13 functional ops      :",
        gap_functional_operations
    )

    print(
        "Day-12 covered ops         :",
        coverage_covered_operations
    )

    print(
        "Day-13 covered ops         :",
        gap_covered_operations
    )

    print(
        "Day-12 operation coverage  :",
        coverage_operation_percent,
        "%"
    )

    print(
        "Day-13 operation coverage  :",
        gap_operation_percent,
        "%"
    )

    print(
        "Day-12 objective coverage  :",
        coverage_objective_percent,
        "%"
    )

    print(
        "Day-13 objective coverage  :",
        gap_objective_percent,
        "%"
    )

    print(
        "Day-12 missing operations  :",
        coverage_missing_operations
    )

    print(
        "Day-13 missing operations  :",
        gap_missing_operations
    )

    print(
        "Day-12 missing objectives  :",
        coverage_missing_objectives
    )

    print(
        "Day-13 missing objectives  :",
        gap_missing_objectives
    )

    print(
        "Day-12 status              :",
        coverage_status
    )

    print(
        "Day-13 gap status          :",
        gap_status
    )

    print(
        "=" * 52
    )

    # ========================================================
    # CONSISTENCY CHECKS
    # ========================================================

    errors = []

    if coverage_operation_percent is None:
        errors.append(
            "Day-12 operation coverage is missing."
        )

    if gap_operation_percent is None:
        errors.append(
            "Day-13 operation coverage is missing."
        )

    if coverage_objective_percent is None:
        errors.append(
            "Day-12 objective coverage is missing."
        )

    if gap_objective_percent is None:
        errors.append(
            "Day-13 objective coverage is missing."
        )

    if (
        coverage_validated_scenarios
        != gap_validated_scenarios
    ):
        errors.append(
            "Validated scenario counts do not match."
        )

    if (
        coverage_functional_operations
        != gap_functional_operations
    ):
        errors.append(
            "Functional-operation counts do not match."
        )

    if (
        coverage_covered_operations
        != gap_covered_operations
    ):
        errors.append(
            "Covered-operation counts do not match."
        )

    if (
        coverage_objective_count
        != gap_objective_count
    ):
        errors.append(
            "Objective counts do not match."
        )

    if (
        coverage_covered_objectives
        != gap_covered_objectives
    ):
        errors.append(
            "Covered-objective counts do not match."
        )

    if (
        coverage_operation_percent is not None
        and gap_operation_percent is not None
        and coverage_operation_percent
        != gap_operation_percent
    ):
        errors.append(
            "Operation coverage percentages do not match."
        )

    if (
        coverage_objective_percent is not None
        and gap_objective_percent is not None
        and coverage_objective_percent
        != gap_objective_percent
    ):
        errors.append(
            "Objective coverage percentages do not match."
        )

    if (
        coverage_missing_operations
        != gap_missing_operations
    ):
        errors.append(
            "Missing-operation lists do not match."
        )

    if (
        coverage_missing_objectives
        != gap_missing_objectives
    ):
        errors.append(
            "Missing-objective lists do not match."
        )

    if coverage_status not in (
        "PASS",
        "COMPLETE",
    ):
        errors.append(
            f"Unexpected Day-12 status: {coverage_status}"
        )

    # If no gaps exist, Day-13 should say so.
    total_gap_count = (
        len(gap_missing_operations)
        + len(gap_missing_objectives)
    )

    if total_gap_count == 0:

        if gap_status not in (
            "NO_GAPS",
            "PASS",
            "COMPLETE",
        ):
            errors.append(
                f"Unexpected Day-13 no-gap status: "
                f"{gap_status}"
            )

        if gaps_detected is True:
            errors.append(
                "gaps_detected is true even though "
                "no gaps are listed."
            )

    else:

        if gap_status not in (
            "GAPS_FOUND",
            "INCOMPLETE",
        ):
            errors.append(
                f"Unexpected Day-13 gap status: "
                f"{gap_status}"
            )

    # ========================================================
    # FINAL RESULT
    # ========================================================

    if errors:

        print()

        print(
            "GAP SOURCE VALIDATION: FAIL"
        )

        for error in errors:
            print(
                " -",
                error
            )

        return 1

    print()

    print(
        "GAP SOURCE VALIDATION: PASS"
    )

    print(
        "Day-13 gap analysis is consistent with "
        "the Day-12 functional coverage report."
    )

    return 0


if __name__ == "__main__":
    sys.exit(
        main()
    )
