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
# GENERAL HELPERS
# ============================================================

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


def to_float(value):
    if value is None:
        return None

    try:
        return float(value)

    except (
        TypeError,
        ValueError
    ):
        return None


def to_int(value):
    if value is None:
        return None

    try:
        return int(value)

    except (
        TypeError,
        ValueError
    ):
        return None


# ============================================================
# COVERAGE EXTRACTION
# ============================================================

def get_coverage_percent(data, kind):
    """
    Supports current project format:

        operation_coverage_percent
        objective_coverage_percent

    Also supports older formats such as:

        operation_coverage:
            coverage_percent: 100.0

        objective_coverage:
            percentage: 100.0
    """

    # Current format
    for key in (
        f"{kind}_coverage_percent",
        f"{kind}_coverage_percentage",
    ):
        value = to_float(
            data.get(key)
        )

        if value is not None:
            return value

    # Older nested/direct format
    block = data.get(
        f"{kind}_coverage"
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

    value = to_float(
        block
    )

    if value is not None:
        return value

    return None


# ============================================================
# GAP EXTRACTION
# ============================================================

def get_list(data, *keys):
    for key in keys:

        value = data.get(key)

        if isinstance(value, list):
            return value

    return []


def get_operation_gaps(data):
    return get_list(
        data,
        "missing_operations",
        "operation_gaps",
        "remaining_operations",
        "remaining_operation_gaps",
        "uncovered_operations",
    )


def get_objective_gaps(data):
    return get_list(
        data,
        "missing_objectives",
        "objective_gaps",
        "remaining_objectives",
        "remaining_objective_gaps",
        "uncovered_objectives",
    )


def get_explicit_count(data, *keys):
    for key in keys:

        if key not in data:
            continue

        value = to_int(
            data.get(key)
        )

        if value is not None:
            return value

    return None


def get_operation_gap_count(data):
    value = get_explicit_count(
        data,
        "operation_gap_count",
        "missing_operation_count",
        "remaining_operation_gap_count",
    )

    if value is not None:
        return value

    return len(
        get_operation_gaps(data)
    )


def get_objective_gap_count(data):
    value = get_explicit_count(
        data,
        "objective_gap_count",
        "missing_objective_count",
        "remaining_objective_gap_count",
    )

    if value is not None:
        return value

    return len(
        get_objective_gaps(data)
    )


def get_total_gap_count(data):
    value = get_explicit_count(
        data,
        "total_gap_count",
        "remaining_gap_count",
        "gap_count",
        "total_gaps",
    )

    if value is not None:
        return value

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
    allowed_arg = sys.argv[3]
    output_path = sys.argv[4]

    try:

        # ----------------------------------------------------
        # Allowed gap threshold
        # ----------------------------------------------------

        allowed_remaining_gaps = to_int(
            allowed_arg
        )

        if allowed_remaining_gaps is None:
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
        # Load inputs
        # ----------------------------------------------------

        coverage = load_json(
            coverage_path
        )

        gaps = load_json(
            gaps_path
        )

        # ----------------------------------------------------
        # Coverage
        # ----------------------------------------------------

        operation_coverage = get_coverage_percent(
            coverage,
            "operation"
        )

        objective_coverage = get_coverage_percent(
            coverage,
            "objective"
        )

        if operation_coverage is None:
            raise ValueError(
                "Operation coverage percentage missing."
            )

        if objective_coverage is None:
            raise ValueError(
                "Objective coverage percentage missing."
            )

        if not (
            0.0
            <= operation_coverage
            <= 100.0
        ):
            raise ValueError(
                "Invalid operation coverage percentage."
            )

        if not (
            0.0
            <= objective_coverage
            <= 100.0
        ):
            raise ValueError(
                "Invalid objective coverage percentage."
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

        operation_gap_count = get_operation_gap_count(
            gaps
        )

        objective_gap_count = get_objective_gap_count(
            gaps
        )

        total_gap_count = get_total_gap_count(
            gaps
        )

        if operation_gap_count < 0:
            raise ValueError(
                "Operation gap count cannot be negative."
            )

        if objective_gap_count < 0:
            raise ValueError(
                "Objective gap count cannot be negative."
            )

        if total_gap_count < 0:
            raise ValueError(
                "Total gap count cannot be negative."
            )

        # ----------------------------------------------------
        # Status values
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
        # Validate status/data consistency
        # ----------------------------------------------------

        errors = []

        if (
            gap_status == "NO_GAPS"
            and total_gap_count != 0
        ):
            errors.append(
                "Gap status is NO_GAPS but "
                "remaining gap count is non-zero."
            )

        if (
            gap_status in (
                "GAPS_FOUND",
                "INCOMPLETE",
            )
            and total_gap_count == 0
        ):
            errors.append(
                "Gap status reports gaps but "
                "remaining gap count is zero."
            )

        # ----------------------------------------------------
        # Closure conditions
        # ----------------------------------------------------

        operation_coverage_ok = (
            operation_coverage >= 100.0
        )

        objective_coverage_ok = (
            objective_coverage >= 100.0
        )

        gap_threshold_ok = (
            total_gap_count
            <= allowed_remaining_gaps
        )

        coverage_status_ok = (
            coverage_status in (
                "",
                "PASS",
                "COMPLETE",
                "COMPLETED",
            )
        )

        gap_status_ok = (
            (
                total_gap_count == 0
                and gap_status in (
                    "",
                    "NO_GAPS",
                    "PASS",
                    "COMPLETE",
                    "COMPLETED",
                )
            )
            or
            (
                total_gap_count > 0
                and gap_status in (
                    "",
                    "GAPS_FOUND",
                    "INCOMPLETE",
                )
            )
        )

        closure_ready = (
            operation_coverage_ok
            and objective_coverage_ok
            and gap_threshold_ok
            and coverage_status_ok
            and gap_status_ok
            and not errors
        )

        if closure_ready:
            decision = "CLOSE"
            final_status = "PASS"

        else:
            decision = "CONTINUE"
            final_status = "FAIL"

        # ----------------------------------------------------
        # Add closure reasons
        # ----------------------------------------------------

        if not operation_coverage_ok:
            errors.append(
                "Operation coverage is below 100%."
            )

        if not objective_coverage_ok:
            errors.append(
                "Objective coverage is below 100%."
            )

        if not gap_threshold_ok:
            errors.append(
                "Remaining gaps exceed the allowed limit."
            )

        if not coverage_status_ok:
            errors.append(
                f"Coverage status is {coverage_status}."
            )

        if not gap_status_ok:
            errors.append(
                f"Gap status is inconsistent: "
                f"{gap_status or 'N/A'}."
            )

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

            "operation_coverage_ok":
                operation_coverage_ok,

            "objective_coverage_ok":
                objective_coverage_ok,

            "gap_threshold_ok":
                gap_threshold_ok,

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

        if errors:
            report[
                "reasons"
            ] = errors

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
    # TERMINAL OUTPUT
    # ========================================================

    print()
    print(
        "CLOSURE DECISION"
    )

    print(
        "=" * 55
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
        "=" * 55
    )

    print()
    print(
        "Decision:",
        decision
    )

    print()

    if closure_ready:

        print(
            "CLOSURE DECISION: PASS"
        )

        print(
            "Verification closure criteria are satisfied."
        )

        return 0

    print(
        "CLOSURE DECISION: FAIL"
    )

    for reason in errors:
        print(
            " -",
            reason
        )

    print(
        "Verification must continue."
    )

    return 1


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    sys.exit(
        main()
    )
