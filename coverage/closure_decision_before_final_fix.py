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
# BASIC HELPERS
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


def normalize(value):
    if value is None:
        return ""

    return (
        str(value)
        .strip()
        .upper()
        .replace("-", "_")
        .replace(" ", "_")
    )


# ============================================================
# COVERAGE EXTRACTION
# ============================================================

def get_coverage_percentage(
    data,
    coverage_type
):
    """
    Supports the formats used across the project.

    Current:
        operation_coverage_percent
        objective_coverage_percent

    Older:
        operation_coverage:
            coverage_percent / percentage

        objective_coverage:
            coverage_percent / percentage
    """

    # Current format
    for key in (
        f"{coverage_type}_coverage_percent",
        f"{coverage_type}_coverage_percentage",
    ):
        value = to_float(
            data.get(key)
        )

        if value is not None:
            return value

    # Older nested format
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

    # Direct numeric fallback
    value = to_float(
        block
    )

    if value is not None:
        return value

    return None


# ============================================================
# GAP EXTRACTION
# ============================================================

def get_list(data, keys):
    for key in keys:

        value = data.get(key)

        if isinstance(value, list):
            return value

    return []


def get_operation_gaps(data):
    return get_list(
        data,
        (
            "missing_operations",
            "operation_gaps",
            "remaining_operations",
            "remaining_operation_gaps",
            "uncovered_operations",
        )
    )


def get_objective_gaps(data):
    return get_list(
        data,
        (
            "missing_objectives",
            "objective_gaps",
            "remaining_objectives",
            "remaining_objective_gaps",
            "uncovered_objectives",
        )
    )


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


def get_operation_gap_count(data):
    explicit = get_integer(
        data,
        (
            "operation_gap_count",
            "missing_operation_count",
            "remaining_operation_gap_count",
        )
    )

    if explicit is not None:
        return explicit

    return len(
        get_operation_gaps(data)
    )


def get_objective_gap_count(data):
    explicit = get_integer(
        data,
        (
            "objective_gap_count",
            "missing_objective_count",
            "remaining_objective_gap_count",
        )
    )

    if explicit is not None:
        return explicit

    return len(
        get_objective_gaps(data)
    )


def get_total_gap_count(data):
    explicit = get_integer(
        data,
        (
            "total_gap_count",
            "remaining_gap_count",
            "gap_count",
            "total_gaps",
        )
    )

    if explicit is not None:
        return explicit

    return (
        get_operation_gap_count(data)
        + get_objective_gap_count(data)
    )


# ============================================================
# MAIN
# ============================================================

def main():

    if len(sys.argv) != 5:

        print(
            "Usage:\n"
            "  python coverage/closure_decision.py "
            "<closed_loop_coverage.json> "
            "<remaining_gaps.json> "
            "<allowed_remaining_gaps> "
            "<closure_decision.json>"
        )

        return 2

    coverage_path = sys.argv[1]
    gaps_path = sys.argv[2]
    allowed_gap_arg = sys.argv[3]
    output_path = sys.argv[4]

    try:

        # ----------------------------------------------------
        # Parse allowed gap threshold
        # ----------------------------------------------------

        try:
            allowed_remaining_gaps = int(
                allowed_gap_arg
            )

        except ValueError:
            raise ValueError(
                "Allowed remaining gap count "
                "must be an integer."
            )

        if allowed_remaining_gaps < 0:
            raise ValueError(
                "Allowed remaining gap count "
                "cannot be negative."
            )

        # ----------------------------------------------------
        # Load reports
        # ----------------------------------------------------

        coverage = load_json(
            coverage_path
        )

        gaps = load_json(
            gaps_path
        )

        # ----------------------------------------------------
        # Coverage percentages
        # ----------------------------------------------------

        operation_coverage = (
            get_coverage_percentage(
                coverage,
                "operation"
            )
        )

        objective_coverage = (
            get_coverage_percentage(
                coverage,
                "objective"
            )
        )

        if operation_coverage is None:
            raise ValueError(
                "Operation coverage percentage missing."
            )

        if objective_coverage is None:
            raise ValueError(
                "Objective coverage percentage missing."
            )

        # ----------------------------------------------------
        # Remaining gaps
        # ----------------------------------------------------

        operation_gaps = get_operation_gaps(
            gaps
        )

        objective_gaps = get_objective_gaps(
            gaps
        )

        operation_gap_count = (
            get_operation_gap_count(
                gaps
            )
        )

        objective_gap_count = (
            get_objective_gap_count(
                gaps
            )
        )

        total_gap_count = (
            get_total_gap_count(
                gaps
            )
        )

        if total_gap_count < 0:
            raise ValueError(
                "Remaining gap count cannot be negative."
            )

        # ----------------------------------------------------
        # Status
        # ----------------------------------------------------

        coverage_status = normalize(
            coverage.get(
                "status"
            )
        )

        gap_status = normalize(
            gaps.get(
                "status",
                gaps.get(
                    "gap_status"
                )
            )
        )

        # ----------------------------------------------------
        # Closure conditions
        # ----------------------------------------------------

        operation_coverage_complete = (
            operation_coverage >= 100.0
        )

        objective_coverage_complete = (
            objective_coverage >= 100.0
        )

        gaps_within_limit = (
            total_gap_count
            <= allowed_remaining_gaps
        )

        no_actual_gaps = (
            total_gap_count == 0
        )

        coverage_pass = (
            coverage_status in (
                "",
                "PASS",
                "COMPLETE",
                "COMPLETED",
            )
        )

        # For this verification flow, closure is safest only
        # when functional coverage is complete and no gaps remain.
        closure_ready = (
            operation_coverage_complete
            and objective_coverage_complete
            and no_actual_gaps
            and coverage_pass
        )

        if closure_ready:
            decision = "CLOSE"

        else:
            decision = "CONTINUE"

        final_status = "PASS"

        # ----------------------------------------------------
        # Build report
        # ----------------------------------------------------

        report = {
            "status":
                final_status,

            "decision":
                decision,

            "coverage_source":
                coverage_path,

            "gap_source":
                gaps_path,

            "operation_coverage_percent":
                operation_coverage,

            "objective_coverage_percent":
                objective_coverage,

            "operation_gap_count":
                operation_gap_count,

            "objective_gap_count":
                objective_gap_count,

            "total_gap_count":
                total_gap_count,

            "allowed_remaining_gaps":
                allowed_remaining_gaps,

            "operation_coverage_complete":
                operation_coverage_complete,

            "objective_coverage_complete":
                objective_coverage_complete,

            "gaps_within_allowed_limit":
                gaps_within_limit,

            "no_remaining_gaps":
                no_actual_gaps,

            "coverage_status":
                coverage_status,

            "gap_status":
                gap_status,

            "missing_operations":
                operation_gaps,

            "missing_objectives":
                objective_gaps,

            "closure_ready":
                closure_ready,
        }

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
            "CLOSURE DECISION: FAIL"
        )

        print(
            f"ERROR: {error}"
        )

        return 1

    # ========================================================
    # TERMINAL REPORT
    # ========================================================

    print()
    print(
        "CLOSURE DECISION"
    )

    print(
        "=" * 58
    )

    print(
        "Operation coverage      :",
        f"{operation_coverage}%"
    )

    print(
        "Objective coverage      :",
        f"{objective_coverage}%"
    )

    print(
        "Operation gaps          :",
        operation_gap_count
    )

    print(
        "Objective gaps          :",
        objective_gap_count
    )

    print(
        "Total remaining gaps    :",
        total_gap_count
    )

    print(
        "Allowed remaining gaps  :",
        allowed_remaining_gaps
    )

    print(
        "Coverage status         :",
        coverage_status or "N/A"
    )

    print(
        "Gap status              :",
        gap_status or "N/A"
    )

    print(
        "=" * 58
    )

    print()
    print(
        "Decision:",
        decision
    )

    print()

    print(
        "CLOSURE DECISION: PASS"
    )

    if decision == "CLOSE":

        print(
            "Verification closure criteria are satisfied."
        )

    else:

        print(
            "Verification should continue because "
            "closure criteria are not yet satisfied."
        )

    return 0


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    sys.exit(
        main()
    )
