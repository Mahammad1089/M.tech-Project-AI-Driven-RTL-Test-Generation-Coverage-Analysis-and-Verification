#!/usr/bin/env python3

import json
import sys
from pathlib import Path


# ============================================================
# JSON LOADER
# ============================================================

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
            "Coverage-gap report must contain "
            "a JSON object."
        )

    return data


# ============================================================
# COMPATIBILITY HELPERS
# ============================================================

def get_operation_gaps(data):
    """
    Support both current and older Day-13 formats.
    """

    value = data.get(
        "missing_operations"
    )

    if isinstance(value, list):
        return value

    value = data.get(
        "operation_gaps"
    )

    if isinstance(value, list):
        return value

    return []


def get_objective_gaps(data):
    """
    Support both current and older Day-13 formats.
    """

    value = data.get(
        "missing_objectives"
    )

    if isinstance(value, list):
        return value

    value = data.get(
        "objective_gaps"
    )

    if isinstance(value, list):
        return value

    return []


# ============================================================
# MAIN
# ============================================================

def main():

    if len(sys.argv) != 2:

        print(
            "Usage:\n"
            "  python coverage/print_gaps.py "
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

        print(
            "COVERAGE GAP REPORT: FAIL"
        )

        print(
            f"ERROR: {error}"
        )

        return 1

    # --------------------------------------------------------
    # Current Day-13 fields
    # --------------------------------------------------------

    status = str(
        data.get(
            "status",
            "UNKNOWN"
        )
    ).strip().upper()

    gaps_detected = bool(
        data.get(
            "gaps_detected",
            False
        )
    )

    validated_scenarios = data.get(
        "validated_scenarios",
        0
    )

    rtl_branches = data.get(
        "rtl_branch_count",
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

    operation_coverage = data.get(
        "operation_coverage_percent",
        0.0
    )

    objective_count = data.get(
        "objective_count",
        0
    )

    covered_objectives = data.get(
        "covered_objective_count",
        0
    )

    objective_coverage = data.get(
        "objective_coverage_percent",
        0.0
    )

    operation_gaps = get_operation_gaps(
        data
    )

    objective_gaps = get_objective_gaps(
        data
    )

    category_gaps = data.get(
        "missing_objectives_by_category",
        {}
    )

    functional_ops = data.get(
        "functional_operations",
        []
    )

    coverage_source = data.get(
        "coverage_source",
        "Unknown"
    )

    recommendation = data.get(
        "recommendation",
        "No recommendation available."
    )

    operation_gap_count = len(
        operation_gaps
    )

    objective_gap_count = len(
        objective_gaps
    )

    total_gap_count = (
        operation_gap_count
        + objective_gap_count
    )

    # ========================================================
    # HEADER
    # ========================================================

    print()
    print("=" * 60)
    print("DAY 13 - COVERAGE GAP REPORT")
    print("=" * 60)

    print(
        "DUT                    : ALU"
    )

    print(
        "Gap status             :",
        status
    )

    print(
        "Gaps detected          :",
        gaps_detected
    )

    print(
        "Validated scenarios    :",
        validated_scenarios
    )

    print(
        "RTL branches           :",
        rtl_branches
    )

    print(
        "Functional operations  :",
        functional_operations
    )

    print(
        "Covered operations     :",
        covered_operations
    )

    print(
        "Operation coverage     :",
        f"{operation_coverage}%"
    )

    print(
        "Objectives             :",
        objective_count
    )

    print(
        "Covered objectives     :",
        covered_objectives
    )

    print(
        "Objective coverage     :",
        f"{objective_coverage}%"
    )

    print(
        "Operation gaps         :",
        operation_gap_count
    )

    print(
        "Objective gaps         :",
        objective_gap_count
    )

    print(
        "Total gaps             :",
        total_gap_count
    )

    print("=" * 60)

    # ========================================================
    # OPERATION GAPS
    # ========================================================

    print()
    print("OPERATION GAPS")
    print("-" * 60)

    if operation_gaps:

        for operation in operation_gaps:
            print(
                " -",
                operation
            )

    else:

        print(
            "None"
        )

    # ========================================================
    # OBJECTIVE GAPS
    # ========================================================

    print()
    print("OBJECTIVE GAPS")
    print("-" * 60)

    if objective_gaps:

        for objective in objective_gaps:
            print(
                " -",
                objective
            )

    else:

        print(
            "None"
        )

    # ========================================================
    # CATEGORY GAP SUMMARY
    # ========================================================

    print()
    print("OBJECTIVE GAPS BY CATEGORY")
    print("-" * 60)

    if (
        isinstance(
            category_gaps,
            dict
        )
        and category_gaps
    ):

        for category in sorted(
            category_gaps.keys()
        ):

            print(
                f"{category:20} : "
                f"{category_gaps[category]}"
            )

    else:

        print(
            "None"
        )

    # ========================================================
    # FUNCTIONAL OPERATIONS
    # ========================================================

    print()
    print("FUNCTIONAL OPERATIONS ANALYZED")
    print("-" * 60)

    if isinstance(
        functional_ops,
        list
    ) and functional_ops:

        for operation in functional_ops:
            print(
                " -",
                operation
            )

    else:

        print(
            "No operation list available."
        )

    # ========================================================
    # SOURCE
    # ========================================================

    print()
    print("COVERAGE SOURCE")
    print("-" * 60)

    print(
        coverage_source
    )

    # ========================================================
    # RECOMMENDATION
    # ========================================================

    print()
    print("RECOMMENDATION")
    print("-" * 60)

    print(
        recommendation
    )

    # ========================================================
    # FINAL RESULT
    # ========================================================

    print()
    print("=" * 60)

    if total_gap_count == 0:

        print(
            "COVERAGE GAP RESULT: PASS"
        )

        print(
            "No functional-operation or "
            "verification-objective gaps were detected."
        )

    else:

        print(
            "COVERAGE GAP RESULT: GAPS FOUND"
        )

        print(
            "Additional targeted tests are required "
            "for the reported gaps."
        )

    print("=" * 60)

    return 0


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    sys.exit(
        main()
    )
