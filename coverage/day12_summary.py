#!/usr/bin/env python3

import json
import sys
from pathlib import Path
from typing import Any, Dict


# ============================================================
# PROJECT PATHS
# ============================================================

COVERAGE_FILE = Path(
    "results/alu/day12/functional_coverage.json"
)

CSV_FILE = Path(
    "results/alu/day12/operation_coverage.csv"
)

SUMMARY_FILE = Path(
    "results/alu/day12/day12_summary.json"
)


# ============================================================
# JSON UTILITIES
# ============================================================

def load_json(path: Path) -> Dict[str, Any]:

    if not path.exists():
        raise FileNotFoundError(
            f"File not found: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError(
            "Coverage report must contain a JSON object."
        )

    return data


# ============================================================
# COMPATIBILITY HELPERS
# ============================================================

def get_operation_coverage(data):
    """
    Support current and older functional coverage formats.
    """

    value = data.get(
        "operation_coverage_percent"
    )

    if value is not None:
        return float(value)

    old = data.get(
        "operation_coverage"
    )

    if isinstance(old, dict):
        value = old.get(
            "coverage_percent"
        )

        if value is not None:
            return float(value)

    return 0.0


def get_objective_coverage(data):
    """
    Support current and older objective coverage formats.
    """

    value = data.get(
        "objective_coverage_percent"
    )

    if value is not None:
        return float(value)

    old = data.get(
        "objective_coverage"
    )

    if isinstance(old, dict):
        value = old.get(
            "coverage_percent"
        )

        if value is not None:
            return float(value)

    return 0.0


# ============================================================
# MAIN
# ============================================================

def main() -> int:

    try:

        coverage = load_json(
            COVERAGE_FILE
        )

    except (
        FileNotFoundError,
        json.JSONDecodeError,
        ValueError,
    ) as error:

        print(
            "DAY 12 SUMMARY: FAIL"
        )

        print(
            f"ERROR: {error}"
        )

        return 1

    # --------------------------------------------------------
    # Current Day-12 values
    # --------------------------------------------------------

    coverage_status = str(
        coverage.get(
            "status",
            "UNKNOWN"
        )
    ).strip().upper()

    validated_scenarios = int(
        coverage.get(
            "validated_scenario_count",
            0
        )
        or 0
    )

    rtl_branches = int(
        coverage.get(
            "rtl_branch_count",
            0
        )
        or 0
    )

    functional_operations = int(
        coverage.get(
            "functional_operation_count",
            0
        )
        or 0
    )

    covered_operations = int(
        coverage.get(
            "covered_operation_count",
            0
        )
        or 0
    )

    operation_coverage = (
        get_operation_coverage(
            coverage
        )
    )

    objective_count = int(
        coverage.get(
            "objective_count",
            0
        )
        or 0
    )

    covered_objectives = int(
        coverage.get(
            "covered_objective_count",
            0
        )
        or 0
    )

    objective_coverage = (
        get_objective_coverage(
            coverage
        )
    )

    operations = coverage.get(
        "operations",
        {}
    )

    categories = coverage.get(
        "category_coverage",
        {}
    )

    missing_operations = (
        coverage.get(
            "missing_operations",
            []
        )
        or []
    )

    missing_objectives = (
        coverage.get(
            "missing_objectives",
            []
        )
        or []
    )

    # --------------------------------------------------------
    # Artifact checks
    # --------------------------------------------------------

    coverage_file_exists = (
        COVERAGE_FILE.exists()
        and COVERAGE_FILE.stat().st_size > 0
    )

    csv_exists = (
        CSV_FILE.exists()
        and CSV_FILE.stat().st_size > 0
    )

    # --------------------------------------------------------
    # Category summary
    # --------------------------------------------------------

    category_summary = {}

    if isinstance(
        categories,
        dict,
    ):

        for category, info in (
            categories.items()
        ):

            if not isinstance(
                info,
                dict,
            ):
                continue

            category_summary[
                category
            ] = {
                "total_objectives":
                    info.get(
                        "total_objectives",
                        0
                    ),

                "covered_objectives":
                    info.get(
                        "covered_objectives",
                        0
                    ),

                "scenario_hits":
                    info.get(
                        "scenario_hits",
                        0
                    ),

                "coverage_percent":
                    info.get(
                        "coverage_percent",
                        0.0
                    ),
            }

    # --------------------------------------------------------
    # Operation summary
    # --------------------------------------------------------

    operation_summary = {}

    if isinstance(
        operations,
        dict,
    ):

        for operation, info in (
            operations.items()
        ):

            if not isinstance(
                info,
                dict,
            ):
                continue

            operation_summary[
                operation
            ] = {
                "covered":
                    bool(
                        info.get(
                            "covered",
                            False
                        )
                    ),

                "hits":
                    int(
                        info.get(
                            "hits",
                            0
                        )
                        or 0
                    ),
            }

    # --------------------------------------------------------
    # Day-12 consistency checks
    # --------------------------------------------------------

    operation_count_valid = (
        functional_operations > 0
        and covered_operations
        == functional_operations
    )

    objective_count_valid = (
        objective_count > 0
        and covered_objectives
        == objective_count
    )

    no_missing_coverage = (
        not missing_operations
        and not missing_objectives
    )

    full_operation_coverage = (
        operation_coverage >= 100.0
    )

    full_objective_coverage = (
        objective_coverage >= 100.0
    )

    day12_pass = all(
        [
            coverage_status
            in (
                "PASS",
                "COMPLETE",
            ),

            validated_scenarios > 0,

            operation_count_valid,

            objective_count_valid,

            full_operation_coverage,

            full_objective_coverage,

            no_missing_coverage,

            coverage_file_exists,

            csv_exists,
        ]
    )

    final_status = (
        "PASS"
        if day12_pass
        else "FAIL"
    )

    # --------------------------------------------------------
    # Summary JSON
    # --------------------------------------------------------

    summary = {
        "day": 12,

        "dut": "alu",

        "stage":
            "Functional coverage analysis",

        "validated_scenarios":
            validated_scenarios,

        "rtl_branches":
            rtl_branches,

        "functional_operations":
            functional_operations,

        "covered_operations":
            covered_operations,

        "operation_coverage_percent":
            operation_coverage,

        "verification_objectives":
            objective_count,

        "covered_objectives":
            covered_objectives,

        "objective_coverage_percent":
            objective_coverage,

        "missing_operations":
            missing_operations,

        "missing_objectives":
            missing_objectives,

        "operation_count_valid":
            operation_count_valid,

        "objective_count_valid":
            objective_count_valid,

        "full_operation_coverage":
            full_operation_coverage,

        "full_objective_coverage":
            full_objective_coverage,

        "coverage_file":
            str(
                COVERAGE_FILE
            ),

        "coverage_file_exists":
            coverage_file_exists,

        "coverage_csv":
            str(
                CSV_FILE
            ),

        "coverage_csv_exists":
            csv_exists,

        "operations":
            operation_summary,

        "category_coverage":
            category_summary,

        "coverage_source":
            (
                "validated Day-10 scenarios "
                "executed in Day 11"
            ),

        "status":
            final_status,
    }

    # --------------------------------------------------------
    # Write summary
    # --------------------------------------------------------

    SUMMARY_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    SUMMARY_FILE.write_text(
        json.dumps(
            summary,
            indent=2,
        ),
        encoding="utf-8",
    )

    # --------------------------------------------------------
    # Terminal output
    # --------------------------------------------------------

    print()
    print(
        "DAY 12 SUMMARY"
    )

    print(
        "=" * 50
    )

    print(
        "Validated scenarios   :",
        validated_scenarios
    )

    print(
        "RTL branches          :",
        rtl_branches
    )

    print(
        "Functional operations :",
        functional_operations
    )

    print(
        "Covered operations    :",
        covered_operations
    )

    print(
        "Operation coverage    :",
        f"{operation_coverage}%"
    )

    print(
        "Objectives            :",
        objective_count
    )

    print(
        "Covered objectives    :",
        covered_objectives
    )

    print(
        "Objective coverage    :",
        f"{objective_coverage}%"
    )

    print(
        "Missing operations    :",
        missing_operations
    )

    print(
        "Missing objectives    :",
        missing_objectives
    )

    print(
        "Coverage JSON exists  :",
        coverage_file_exists
    )

    print(
        "Coverage CSV exists   :",
        csv_exists
    )

    print(
        "=" * 50
    )

    print(
        "DAY 12 STATUS         :",
        final_status
    )

    print()

    if final_status == "PASS":

        print(
            "All executable RTL operations and "
            "verification objectives are covered."
        )

        return 0

    print(
        "Day-12 coverage summary contains "
        "one or more incomplete checks."
    )

    return 1


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    sys.exit(
        main()
    )
