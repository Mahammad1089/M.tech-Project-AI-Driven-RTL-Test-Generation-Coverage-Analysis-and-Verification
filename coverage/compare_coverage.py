#!/usr/bin/env python3

import json
import sys
from pathlib import Path


# ============================================================
# JSON UTILITIES
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

    if not isinstance(data, dict):
        raise ValueError(
            f"{path} must contain a JSON object."
        )

    return data


def save_json(path, data):
    file_path = Path(path)

    file_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with file_path.open(
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            data,
            f,
            indent=2
        )


# ============================================================
# VALUE HELPERS
# ============================================================

def to_float(value):
    if value is None:
        return None

    try:
        return float(value)

    except (
        TypeError,
        ValueError,
    ):
        return None


def get_percentage(data, coverage_type):
    """
    Supports both current and older coverage JSON formats.

    Current:
        operation_coverage_percent
        objective_coverage_percent

    Older examples:
        operation_coverage:
            coverage_percent
            percentage

        objective_coverage:
            coverage_percent
            percentage
    """

    # --------------------------------------------------------
    # Current top-level format
    # --------------------------------------------------------

    direct_keys = (
        f"{coverage_type}_coverage_percent",
        f"{coverage_type}_coverage_percentage",
    )

    for key in direct_keys:
        value = to_float(
            data.get(key)
        )

        if value is not None:
            return value

    # --------------------------------------------------------
    # Older nested format
    # --------------------------------------------------------

    block = data.get(
        f"{coverage_type}_coverage"
    )

    if isinstance(block, dict):

        for key in (
            "coverage_percent",
            "percentage",
            "percent",
        ):
            value = to_float(
                block.get(key)
            )

            if value is not None:
                return value

    # --------------------------------------------------------
    # Direct numeric older format
    # --------------------------------------------------------

    value = to_float(
        block
    )

    if value is not None:
        return value

    return None


def get_integer(data, keys):
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


def get_list(data, *keys):
    for key in keys:

        value = data.get(key)

        if isinstance(value, list):
            return value

    return []


def get_status(data):
    return str(
        data.get(
            "status",
            ""
        )
    ).strip().upper()


# ============================================================
# MAIN
# ============================================================

def main():

    if len(sys.argv) != 4:

        print(
            "Usage:\n"
            "  python coverage/compare_coverage.py "
            "<baseline_coverage.json> "
            "<closed_loop_coverage.json> "
            "<coverage_comparison.json>"
        )

        return 2

    baseline_path = sys.argv[1]
    closed_loop_path = sys.argv[2]
    output_path = sys.argv[3]

    try:

        # ====================================================
        # LOAD FILES
        # ====================================================

        baseline = load_json(
            baseline_path
        )

        closed_loop = load_json(
            closed_loop_path
        )

        # ====================================================
        # READ OPERATION COVERAGE
        # ====================================================

        baseline_operation = get_percentage(
            baseline,
            "operation"
        )

        closed_operation = get_percentage(
            closed_loop,
            "operation"
        )

        if baseline_operation is None:
            raise ValueError(
                "Baseline operation coverage percentage "
                "is missing."
            )

        if closed_operation is None:
            raise ValueError(
                "Closed-loop operation coverage percentage "
                "is missing."
            )

        # ====================================================
        # READ OBJECTIVE COVERAGE
        # ====================================================

        baseline_objective = get_percentage(
            baseline,
            "objective"
        )

        closed_objective = get_percentage(
            closed_loop,
            "objective"
        )

        if baseline_objective is None:
            raise ValueError(
                "Baseline objective coverage percentage "
                "is missing."
            )

        if closed_objective is None:
            raise ValueError(
                "Closed-loop objective coverage percentage "
                "is missing."
            )

        # ====================================================
        # READ COUNTS
        # ====================================================

        baseline_operation_count = get_integer(
            baseline,
            (
                "functional_operation_count",
                "operation_count",
                "total_operations",
            )
        )

        baseline_covered_operations = get_integer(
            baseline,
            (
                "covered_operation_count",
                "covered_operations",
            )
        )

        closed_operation_count = get_integer(
            closed_loop,
            (
                "functional_operation_count",
                "operation_count",
                "total_operations",
            )
        )

        closed_covered_operations = get_integer(
            closed_loop,
            (
                "covered_operation_count",
                "covered_operations",
            )
        )

        baseline_objective_count = get_integer(
            baseline,
            (
                "objective_count",
                "verification_objectives",
                "total_objectives",
            )
        )

        baseline_covered_objectives = get_integer(
            baseline,
            (
                "covered_objective_count",
                "covered_objectives",
            )
        )

        closed_objective_count = get_integer(
            closed_loop,
            (
                "objective_count",
                "verification_objectives",
                "total_objectives",
            )
        )

        closed_covered_objectives = get_integer(
            closed_loop,
            (
                "covered_objective_count",
                "covered_objectives",
            )
        )

        # ====================================================
        # READ MISSING COVERAGE
        # ====================================================

        baseline_missing_operations = get_list(
            baseline,
            "missing_operations"
        )

        closed_missing_operations = get_list(
            closed_loop,
            "missing_operations"
        )

        baseline_missing_objectives = get_list(
            baseline,
            "missing_objectives"
        )

        closed_missing_objectives = get_list(
            closed_loop,
            "missing_objectives"
        )

        # ====================================================
        # CALCULATE CHANGES
        # ====================================================

        operation_change = round(
            closed_operation
            - baseline_operation,
            2
        )

        objective_change = round(
            closed_objective
            - baseline_objective,
            2
        )

        # ====================================================
        # DETERMINE TREND
        # ====================================================

        if (
            operation_change > 0
            or objective_change > 0
        ):

            trend = "IMPROVED"

        elif (
            operation_change == 0
            and objective_change == 0
        ):

            trend = "UNCHANGED"

        else:

            trend = "REGRESSION"

        # ====================================================
        # STATUS CHECK
        # ====================================================

        baseline_status = get_status(
            baseline
        )

        closed_status = get_status(
            closed_loop
        )

        errors = []

        if operation_change < 0:
            errors.append(
                "Operation coverage regressed."
            )

        if objective_change < 0:
            errors.append(
                "Objective coverage regressed."
            )

        if (
            closed_status
            and closed_status
            not in (
                "PASS",
                "COMPLETE",
                "COMPLETED",
            )
        ):
            errors.append(
                f"Closed-loop coverage status is "
                f"{closed_status}."
            )

        final_status = (
            "PASS"
            if not errors
            else "FAIL"
        )

        # ====================================================
        # BUILD JSON REPORT
        # ====================================================

        report = {
            "status":
                final_status,

            "trend":
                trend,

            "baseline_source":
                baseline_path,

            "closed_loop_source":
                closed_loop_path,

            "baseline_status":
                baseline_status,

            "closed_loop_status":
                closed_status,

            "baseline_operation_coverage_percent":
                baseline_operation,

            "closed_loop_operation_coverage_percent":
                closed_operation,

            "operation_coverage_change_percent":
                operation_change,

            "baseline_objective_coverage_percent":
                baseline_objective,

            "closed_loop_objective_coverage_percent":
                closed_objective,

            "objective_coverage_change_percent":
                objective_change,

            "baseline_operation_count":
                baseline_operation_count,

            "baseline_covered_operations":
                baseline_covered_operations,

            "closed_loop_operation_count":
                closed_operation_count,

            "closed_loop_covered_operations":
                closed_covered_operations,

            "baseline_objective_count":
                baseline_objective_count,

            "baseline_covered_objectives":
                baseline_covered_objectives,

            "closed_loop_objective_count":
                closed_objective_count,

            "closed_loop_covered_objectives":
                closed_covered_objectives,

            "baseline_missing_operations":
                baseline_missing_operations,

            "closed_loop_missing_operations":
                closed_missing_operations,

            "baseline_missing_objectives":
                baseline_missing_objectives,

            "closed_loop_missing_objectives":
                closed_missing_objectives,

            "coverage_improvement_claimed":
                (
                    trend == "IMPROVED"
                ),
        }

        if errors:
            report[
                "errors"
            ] = errors

        # ====================================================
        # SAVE REPORT
        # ====================================================

        save_json(
            output_path,
            report
        )

    except (
        FileNotFoundError,
        json.JSONDecodeError,
        ValueError,
    ) as error:

        print(
            "COVERAGE COMPARISON: FAIL"
        )

        print(
            f"ERROR: {error}"
        )

        return 1

    # ========================================================
    # TERMINAL OUTPUT
    # ========================================================

    print()
    print(
        "COVERAGE COMPARISON"
    )

    print(
        "=" * 60
    )

    print(
        "Baseline operation coverage    :",
        f"{baseline_operation}%"
    )

    print(
        "Closed-loop operation coverage :",
        f"{closed_operation}%"
    )

    print(
        "Operation coverage change      :",
        f"{operation_change:+.2f}%"
    )

    print()

    print(
        "Baseline objective coverage    :",
        f"{baseline_objective}%"
    )

    print(
        "Closed-loop objective coverage :",
        f"{closed_objective}%"
    )

    print(
        "Objective coverage change      :",
        f"{objective_change:+.2f}%"
    )

    print()

    print(
        "Baseline missing operations    :",
        baseline_missing_operations
    )

    print(
        "Closed-loop missing operations :",
        closed_missing_operations
    )

    print(
        "Baseline missing objectives    :",
        baseline_missing_objectives
    )

    print(
        "Closed-loop missing objectives :",
        closed_missing_objectives
    )

    print(
        "=" * 60
    )

    # ========================================================
    # REQUIRED STEP-35 FORMAT
    # ========================================================

    print()
    print(
        "Trend:",
        trend
    )

    print()

    if errors:

        print(
            "COVERAGE COMPARISON: FAIL"
        )

        for error in errors:

            print(
                " -",
                error
            )

        return 1

    print(
        "COVERAGE COMPARISON: PASS"
    )

    return 0


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    sys.exit(
        main()
    )
