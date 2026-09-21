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
# NORMALIZATION
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


# ============================================================
# LIST EXTRACTION
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


# ============================================================
# GAP COUNT EXTRACTION
# ============================================================

def get_explicit_integer(data, keys):
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
    explicit = get_explicit_integer(
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
    explicit = get_explicit_integer(
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
    explicit = get_explicit_integer(
        data,
        (
            "total_gap_count",
            "gap_count",
            "remaining_gap_count",
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
# STATUS
# ============================================================

def get_status(data):
    for key in (
        "status",
        "gap_status",
        "analysis_status",
    ):

        if key in data:
            return normalize(
                data.get(key)
            )

    return ""


# ============================================================
# MAIN
# ============================================================

def main():

    if len(sys.argv) != 4:

        print(
            "Usage:\n"
            "  python coverage/compare_gaps.py "
            "<before_gaps.json> "
            "<after_gaps.json> "
            "<gap_comparison.json>"
        )

        return 2

    before_path = sys.argv[1]
    after_path = sys.argv[2]
    output_path = sys.argv[3]

    try:

        # ====================================================
        # LOAD FILES
        # ====================================================

        before = load_json(
            before_path
        )

        after = load_json(
            after_path
        )

        # ====================================================
        # BEFORE GAPS
        # ====================================================

        before_operation_gaps = get_operation_gaps(
            before
        )

        before_objective_gaps = get_objective_gaps(
            before
        )

        before_operation_count = (
            get_operation_gap_count(
                before
            )
        )

        before_objective_count = (
            get_objective_gap_count(
                before
            )
        )

        before_total = get_total_gap_count(
            before
        )

        # ====================================================
        # AFTER GAPS
        # ====================================================

        after_operation_gaps = get_operation_gaps(
            after
        )

        after_objective_gaps = get_objective_gaps(
            after
        )

        after_operation_count = (
            get_operation_gap_count(
                after
            )
        )

        after_objective_count = (
            get_objective_gap_count(
                after
            )
        )

        after_total = get_total_gap_count(
            after
        )

        # ====================================================
        # VALIDATE COUNTS
        # ====================================================

        if before_total < 0:
            raise ValueError(
                "Invalid before gap count."
            )

        if after_total < 0:
            raise ValueError(
                "Invalid after gap count."
            )

        # ====================================================
        # GAP CHANGE
        # ====================================================

        gap_change = (
            after_total
            - before_total
        )

        gap_reduction = (
            before_total
            - after_total
        )

        if after_total < before_total:

            trend = "IMPROVED"

        elif after_total == before_total:

            trend = "UNCHANGED"

        else:

            trend = "REGRESSION"

        # ====================================================
        # SET DIFFERENCES
        # ====================================================

        before_operation_set = {
            str(item)
            for item in before_operation_gaps
        }

        after_operation_set = {
            str(item)
            for item in after_operation_gaps
        }

        before_objective_set = {
            str(item)
            for item in before_objective_gaps
        }

        after_objective_set = {
            str(item)
            for item in after_objective_gaps
        }

        resolved_operations = sorted(
            before_operation_set
            - after_operation_set
        )

        new_operation_gaps = sorted(
            after_operation_set
            - before_operation_set
        )

        resolved_objectives = sorted(
            before_objective_set
            - after_objective_set
        )

        new_objective_gaps = sorted(
            after_objective_set
            - before_objective_set
        )

        # ====================================================
        # STATUS
        # ====================================================

        before_status = get_status(
            before
        )

        after_status = get_status(
            after
        )

        errors = []

        if trend == "REGRESSION":

            errors.append(
                "Gap count increased during "
                "closed-loop verification."
            )

        final_status = (
            "PASS"
            if not errors
            else "FAIL"
        )

        # ====================================================
        # JSON REPORT
        # ====================================================

        report = {
            "status":
                final_status,

            "trend":
                trend,

            "before_source":
                before_path,

            "after_source":
                after_path,

            "before_status":
                before_status,

            "after_status":
                after_status,

            "before_operation_gap_count":
                before_operation_count,

            "before_objective_gap_count":
                before_objective_count,

            "before_total_gap_count":
                before_total,

            "after_operation_gap_count":
                after_operation_count,

            "after_objective_gap_count":
                after_objective_count,

            "after_total_gap_count":
                after_total,

            "gap_change":
                gap_change,

            "gap_reduction":
                gap_reduction,

            "before_operation_gaps":
                sorted(
                    before_operation_set
                ),

            "after_operation_gaps":
                sorted(
                    after_operation_set
                ),

            "before_objective_gaps":
                sorted(
                    before_objective_set
                ),

            "after_objective_gaps":
                sorted(
                    after_objective_set
                ),

            "resolved_operations":
                resolved_operations,

            "new_operation_gaps":
                new_operation_gaps,

            "resolved_objectives":
                resolved_objectives,

            "new_objective_gaps":
                new_objective_gaps,
        }

        if errors:
            report["errors"] = errors

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
            "GAP COMPARISON: FAIL"
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
        "GAP COMPARISON"
    )

    print(
        "=" * 58
    )

    print(
        "Before operation gaps :",
        before_operation_count
    )

    print(
        "Before objective gaps :",
        before_objective_count
    )

    print(
        "Before total gaps     :",
        before_total
    )

    print()

    print(
        "After operation gaps  :",
        after_operation_count
    )

    print(
        "After objective gaps  :",
        after_objective_count
    )

    print(
        "After total gaps      :",
        after_total
    )

    print()

    print(
        "Gap reduction         :",
        gap_reduction
    )

    print(
        "Resolved operations   :",
        resolved_operations
    )

    print(
        "Resolved objectives   :",
        resolved_objectives
    )

    print(
        "New operation gaps    :",
        new_operation_gaps
    )

    print(
        "New objective gaps    :",
        new_objective_gaps
    )

    print(
        "=" * 58
    )

    print()
    print(
        "Trend:",
        trend
    )

    print()

    if errors:

        print(
            "GAP COMPARISON: FAIL"
        )

        for error in errors:
            print(
                " -",
                error
            )

        return 1

    print(
        "GAP COMPARISON: PASS"
    )

    return 0


if __name__ == "__main__":
    sys.exit(
        main()
    )
