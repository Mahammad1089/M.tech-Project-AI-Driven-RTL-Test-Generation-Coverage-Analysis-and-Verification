#!/usr/bin/env python3

import json
import sys
from pathlib import Path


# ============================================================
# FILE PATHS
# ============================================================

GAP_FILE = Path(
    "results/alu/day13/coverage_gaps.json"
)

FEEDBACK_FILE = Path(
    "results/alu/day13/day14_feedback_input.json"
)

SUMMARY_FILE = Path(
    "results/alu/day13/day13_summary.json"
)


# ============================================================
# JSON UTILITIES
# ============================================================

def load_json(path):
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
            f"{path} must contain a JSON object."
        )

    return data


# ============================================================
# MAIN
# ============================================================

def main():

    try:
        gaps = load_json(
            GAP_FILE
        )

    except (
        FileNotFoundError,
        json.JSONDecodeError,
        ValueError,
    ) as error:

        print("DAY 13 SUMMARY: FAIL")
        print(error)
        return 1

    # --------------------------------------------------------
    # Read current gap-analysis format
    # --------------------------------------------------------

    gap_status = str(
        gaps.get(
            "status",
            ""
        )
    ).strip().upper()

    gaps_detected = bool(
        gaps.get(
            "gaps_detected",
            False
        )
    )

    validated_scenarios = int(
        gaps.get(
            "validated_scenarios",
            0
        )
        or 0
    )

    rtl_branches = int(
        gaps.get(
            "rtl_branch_count",
            0
        )
        or 0
    )

    functional_operations = int(
        gaps.get(
            "functional_operation_count",
            0
        )
        or 0
    )

    covered_operations = int(
        gaps.get(
            "covered_operation_count",
            0
        )
        or 0
    )

    operation_coverage = float(
        gaps.get(
            "operation_coverage_percent",
            0.0
        )
        or 0.0
    )

    objective_count = int(
        gaps.get(
            "objective_count",
            0
        )
        or 0
    )

    covered_objectives = int(
        gaps.get(
            "covered_objective_count",
            0
        )
        or 0
    )

    objective_coverage = float(
        gaps.get(
            "objective_coverage_percent",
            0.0
        )
        or 0.0
    )

    missing_operations = (
        gaps.get(
            "missing_operations",
            []
        )
        or []
    )

    missing_objectives = (
        gaps.get(
            "missing_objectives",
            []
        )
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

    # --------------------------------------------------------
    # Validate the status
    # --------------------------------------------------------

    valid_statuses = {
        "NO_GAPS",
        "GAPS_FOUND",
        "PASS",
        "COMPLETE",
        "INCOMPLETE",
    }

    if gap_status not in valid_statuses:
        print(
            "DAY 13 SUMMARY: FAIL"
        )
        print(
            f"Invalid gap status: {gap_status}"
        )
        return 1

    # --------------------------------------------------------
    # Check status against actual gap lists
    # --------------------------------------------------------

    consistency_errors = []

    if total_gap_count == 0:

        if gap_status not in {
            "NO_GAPS",
            "PASS",
            "COMPLETE",
        }:
            consistency_errors.append(
                "Gap status indicates gaps, but "
                "no gaps are present."
            )

        if gaps_detected:
            consistency_errors.append(
                "gaps_detected is True even though "
                "total gap count is zero."
            )

    else:

        if gap_status not in {
            "GAPS_FOUND",
            "INCOMPLETE",
        }:
            consistency_errors.append(
                "Gap status does not indicate the "
                "reported coverage gaps."
            )

        if not gaps_detected:
            consistency_errors.append(
                "gaps_detected is False even though "
                "coverage gaps are present."
            )

    # --------------------------------------------------------
    # Basic coverage consistency
    # --------------------------------------------------------

    if functional_operations <= 0:
        consistency_errors.append(
            "No functional operations were analyzed."
        )

    if objective_count <= 0:
        consistency_errors.append(
            "No verification objectives were analyzed."
        )

    if (
        total_gap_count == 0
        and covered_operations
        != functional_operations
    ):
        consistency_errors.append(
            "Operation counts are inconsistent."
        )

    if (
        total_gap_count == 0
        and covered_objectives
        != objective_count
    ):
        consistency_errors.append(
            "Objective counts are inconsistent."
        )

    # --------------------------------------------------------
    # Day-14 feedback artifact
    # --------------------------------------------------------

    feedback_exists = (
        FEEDBACK_FILE.exists()
        and FEEDBACK_FILE.stat().st_size > 0
    )

    if not feedback_exists:
        consistency_errors.append(
            "Day-14 feedback input is missing."
        )

    # --------------------------------------------------------
    # Final Day-13 status
    # --------------------------------------------------------

    final_status = (
        "PASS"
        if not consistency_errors
        else "FAIL"
    )

    summary = {
        "day": 13,
        "dut": "alu",
        "stage": "Coverage gap analysis",

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

        "operation_gap_count":
            operation_gap_count,

        "objective_gap_count":
            objective_gap_count,

        "total_gap_count":
            total_gap_count,

        "missing_operations":
            missing_operations,

        "missing_objectives":
            missing_objectives,

        "gaps_detected":
            gaps_detected,

        "gap_status":
            gap_status,

        "feedback_input":
            str(FEEDBACK_FILE),

        "feedback_input_exists":
            feedback_exists,

        "next_stage":
            "DAY_14_FEEDBACK_AND_TARGETED_REGENERATION",

        "status":
            final_status,
    }

    # --------------------------------------------------------
    # Save summary
    # --------------------------------------------------------

    SUMMARY_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    SUMMARY_FILE.write_text(
        json.dumps(
            summary,
            indent=2
        ),
        encoding="utf-8"
    )

    # --------------------------------------------------------
    # Terminal output
    # --------------------------------------------------------

    print()
    print("DAY 13 SUMMARY")
    print("=" * 50)

    print(
        "Validated scenarios  :",
        validated_scenarios
    )

    print(
        "Functional operations:",
        functional_operations
    )

    print(
        "Covered operations   :",
        covered_operations
    )

    print(
        "Operation coverage   :",
        f"{operation_coverage}%"
    )

    print(
        "Objectives           :",
        objective_count
    )

    print(
        "Covered objectives   :",
        covered_objectives
    )

    print(
        "Objective coverage   :",
        f"{objective_coverage}%"
    )

    print(
        "Operation gaps       :",
        operation_gap_count
    )

    print(
        "Objective gaps       :",
        objective_gap_count
    )

    print(
        "Total gaps           :",
        total_gap_count
    )

    print(
        "Gap status           :",
        gap_status
    )

    print(
        "Day-14 input exists  :",
        feedback_exists
    )

    print("=" * 50)

    if consistency_errors:

        print(
            "DAY 13 SUMMARY: FAIL"
        )

        for error in consistency_errors:
            print(
                " -",
                error
            )

        return 1

    print(
        "DAY 13 SUMMARY: PASS"
    )

    if total_gap_count == 0:
        print(
            "No functional-operation or "
            "verification-objective gaps remain."
        )
    else:
        print(
            "Coverage gaps were detected and "
            "prepared for Day-14 feedback."
        )

    return 0


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    sys.exit(
        main()
    )
