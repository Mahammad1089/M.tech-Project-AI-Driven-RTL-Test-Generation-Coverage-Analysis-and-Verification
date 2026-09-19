#!/usr/bin/env python3

import json
import sys
from pathlib import Path


# ============================================================
# PROJECT PATHS
# ============================================================

ROOT = Path(__file__).resolve().parent.parent

DAY13_GAPS = (
    ROOT / "results/alu/day13/coverage_gaps.json"
)

DAY14_HERMES_RESULT = (
    ROOT / "results/alu/day14/day14_hermes_result.json"
)

TARGETED_CANDIDATES = (
    ROOT / "results/alu/day14/targeted_candidate_tests.json"
)

TARGET_GAP_VALIDATION = (
    ROOT / "results/alu/day14/target_gap_validation.json"
)

TARGETED_VALIDATED = (
    ROOT / "results/alu/day14/targeted_validated_tests.json"
)

TARGETED_REJECTED = (
    ROOT / "results/alu/day14/targeted_rejected_tests.json"
)

TARGETED_VALIDATION_REPORT = (
    ROOT / "results/alu/day14/targeted_validation_report.json"
)

SUMMARY_FILE = (
    ROOT / "results/alu/day14/day14_summary.json"
)


# ============================================================
# JSON HELPERS
# ============================================================

def load_json(path, required=True):
    if not path.exists():
        if required:
            raise FileNotFoundError(
                f"File not found: {path}"
            )
        return {}

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


def save_json(path, data):
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            data,
            f,
            indent=2,
        )


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


def get_list(data, *keys):
    for key in keys:
        value = data.get(key)

        if isinstance(value, list):
            return value

    return []


# ============================================================
# MAIN
# ============================================================

def main():

    try:
        gaps = load_json(
            DAY13_GAPS
        )

        candidates = load_json(
            TARGETED_CANDIDATES,
            required=False,
        )

        gap_validation = load_json(
            TARGET_GAP_VALIDATION,
            required=False,
        )

        validated = load_json(
            TARGETED_VALIDATED,
            required=False,
        )

        rejected = load_json(
            TARGETED_REJECTED,
            required=False,
        )

        validation_report = load_json(
            TARGETED_VALIDATION_REPORT,
            required=False,
        )

        hermes_result = load_json(
            DAY14_HERMES_RESULT,
            required=False,
        )

    except (
        FileNotFoundError,
        json.JSONDecodeError,
        ValueError,
    ) as error:

        print(
            "DAY 14 SUMMARY: FAIL"
        )

        print(
            f"ERROR: {error}"
        )

        return 1

    # ========================================================
    # DAY-13 GAP STATE
    # ========================================================

    gap_status = normalize(
        gaps.get("status")
    )

    missing_operations = get_list(
        gaps,
        "missing_operations",
        "operation_gaps",
    )

    missing_objectives = get_list(
        gaps,
        "missing_objectives",
        "objective_gaps",
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

    gaps_detected = gaps.get(
        "gaps_detected"
    )

    no_gaps = (
        total_gap_count == 0
        and (
            gap_status in (
                "NO_GAPS",
                "PASS",
                "COMPLETE",
            )
            or gaps_detected is False
        )
    )

    gaps_found = (
        total_gap_count > 0
        or gap_status in (
            "GAPS_FOUND",
            "INCOMPLETE",
        )
        or gaps_detected is True
    )

    # ========================================================
    # DAY-14 TARGETED CANDIDATES
    # ========================================================

    candidate_scenarios = get_list(
        candidates,
        "scenarios",
        "targeted_tests",
        "tests",
    )

    candidate_count = candidates.get(
        "scenario_count"
    )

    if candidate_count is None:
        candidate_count = len(
            candidate_scenarios
        )

    try:
        candidate_count = int(
            candidate_count
        )
    except (
        TypeError,
        ValueError,
    ):
        candidate_count = len(
            candidate_scenarios
        )

    candidate_mode = normalize(
        candidates.get("mode")
    )

    candidate_generation_status = normalize(
        candidates.get(
            "generation_status"
        )
    )

    # ========================================================
    # GAP VALIDATION
    # ========================================================

    gap_validation_status = normalize(
        gap_validation.get(
            "status"
        )
    )

    # ========================================================
    # VALIDATED TESTS
    # ========================================================

    validated_tests = get_list(
        validated,
        "validated_tests",
        "scenarios",
    )

    validated_count = validated.get(
        "validated_test_count"
    )

    if validated_count is None:
        validated_count = len(
            validated_tests
        )

    try:
        validated_count = int(
            validated_count
        )
    except (
        TypeError,
        ValueError,
    ):
        validated_count = len(
            validated_tests
        )

    # ========================================================
    # REJECTED TESTS
    # ========================================================

    rejected_tests = get_list(
        rejected,
        "rejected_tests",
        "rejected_scenarios",
    )

    rejected_count = (
        rejected.get(
            "rejected_test_count"
        )
    )

    if rejected_count is None:
        rejected_count = rejected.get(
            "rejected_count"
        )

    if rejected_count is None:
        rejected_count = len(
            rejected_tests
        )

    try:
        rejected_count = int(
            rejected_count
        )
    except (
        TypeError,
        ValueError,
    ):
        rejected_count = len(
            rejected_tests
        )

    # ========================================================
    # VALIDATION REPORT STATUS
    # ========================================================

    deterministic_status = normalize(
        validation_report.get(
            "status"
        )
    )

    deterministic_required = (
        validation_report.get(
            "deterministic_validation_required"
        )
    )

    # ========================================================
    # CHECK HERMES RESULT EXISTS
    # ========================================================

    hermes_result_exists = (
        DAY14_HERMES_RESULT.exists()
        and DAY14_HERMES_RESULT.stat().st_size > 0
    )

    # ========================================================
    # FINAL VALIDATION
    # ========================================================

    errors = []

    if no_gaps:

        # ----------------------------------------------------
        # Correct NO_GAPS behavior
        # ----------------------------------------------------

        if candidate_count != 0:
            errors.append(
                "Targeted candidate count must be 0 "
                "when Day 13 reports NO_GAPS."
            )

        if validated_count != 0:
            errors.append(
                "Validated targeted-test count must be 0 "
                "when Day 13 reports NO_GAPS."
            )

        if rejected_count != 0:
            errors.append(
                "Rejected targeted-test count must be 0 "
                "when no targeted tests were generated."
            )

        if candidate_mode not in (
            "",
            "NO_GAPS",
        ):
            errors.append(
                f"Unexpected candidate mode: "
                f"{candidate_mode}"
            )

        if candidate_generation_status not in (
            "",
            "NO_TARGETED_GENERATION_REQUIRED",
        ):
            errors.append(
                "Unexpected generation status for "
                "NO_GAPS flow."
            )

        if gap_validation_status not in (
            "",
            "PASS",
            "COMPLETE",
        ):
            errors.append(
                "Target-gap validation did not PASS."
            )

        if deterministic_required is True:
            errors.append(
                "Deterministic targeted validation should "
                "not be required in NO_GAPS mode."
            )

        day14_mode = "NO_GAPS"

    elif gaps_found:

        # ----------------------------------------------------
        # GAPS_FOUND behavior
        # ----------------------------------------------------

        if candidate_count <= 0:
            errors.append(
                "Day 13 reported gaps but no targeted "
                "candidate tests were generated."
            )

        if gap_validation_status not in (
            "PASS",
            "COMPLETE",
        ):
            errors.append(
                "Target-gap validation did not PASS."
            )

        if validated_count <= 0:
            errors.append(
                "No targeted tests passed deterministic "
                "validation."
            )

        if deterministic_status not in (
            "PASS",
            "COMPLETE",
        ):
            errors.append(
                "Deterministic validation report did not PASS."
            )

        day14_mode = "TARGETED_GENERATION"

    else:

        errors.append(
            "Unable to determine Day-13 gap state."
        )

        day14_mode = "UNKNOWN"

    # ========================================================
    # FINAL STATUS
    # ========================================================

    final_status = (
        "PASS"
        if not errors
        else "FAIL"
    )

    # ========================================================
    # SUMMARY JSON
    # ========================================================

    summary = {
        "day":
            14,

        "dut":
            "alu",

        "stage":
            "Hermes feedback and targeted regeneration",

        "day13_gap_status":
            gap_status,

        "gaps_detected":
            bool(
                total_gap_count > 0
            ),

        "operation_gap_count":
            operation_gap_count,

        "objective_gap_count":
            objective_gap_count,

        "total_gap_count":
            total_gap_count,

        "mode":
            day14_mode,

        "hermes_result_exists":
            hermes_result_exists,

        "targeted_candidate_count":
            candidate_count,

        "validated_targeted_count":
            validated_count,

        "rejected_targeted_count":
            rejected_count,

        "target_gap_validation_status":
            gap_validation_status,

        "generation_status":
            candidate_generation_status,

        "deterministic_validation_required":
            (
                False
                if no_gaps
                else True
            ),

        "deterministic_validation_status":
            (
                "SKIPPED"
                if no_gaps
                else deterministic_status
            ),

        "targeted_regeneration_required":
            not no_gaps,

        "next_stage":
            "DAY_15_FINAL_ANALYSIS",

        "status":
            final_status,
    }

    if errors:
        summary[
            "errors"
        ] = errors

    save_json(
        SUMMARY_FILE,
        summary,
    )

    # ========================================================
    # TERMINAL REPORT
    # ========================================================

    print()
    print(
        "DAY 14 SUMMARY"
    )

    print(
        "=" * 55
    )

    print(
        "Day-13 gap status        :",
        gap_status
    )

    print(
        "Operation gaps           :",
        operation_gap_count
    )

    print(
        "Objective gaps           :",
        objective_gap_count
    )

    print(
        "Total gaps               :",
        total_gap_count
    )

    print(
        "Day-14 mode              :",
        day14_mode
    )

    print(
        "Targeted candidates      :",
        candidate_count
    )

    print(
        "Validated targeted tests :",
        validated_count
    )

    print(
        "Rejected targeted tests  :",
        rejected_count
    )

    print(
        "Target-gap validation    :",
        gap_validation_status or "N/A"
    )

    print(
        "Deterministic validation :",
        (
            "SKIPPED"
            if no_gaps
            else (
                deterministic_status
                or "UNKNOWN"
            )
        )
    )

    print(
        "=" * 55
    )

    if errors:

        print(
            "DAY 14 SUMMARY: FAIL"
        )

        for error in errors:
            print(
                " -",
                error
            )

        return 1

    print(
        "DAY 14 SUMMARY: PASS"
    )

    if no_gaps:

        print(
            "No verified coverage gaps were present."
        )

        print(
            "Targeted regeneration and deterministic "
            "targeted-test validation were not required."
        )

    else:

        print(
            "Verified Day-13 coverage gaps were handled "
            "through targeted regeneration."
        )

    return 0


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    sys.exit(
        main()
    )
