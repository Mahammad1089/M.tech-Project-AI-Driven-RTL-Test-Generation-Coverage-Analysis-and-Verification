#!/usr/bin/env python3

import json
import subprocess
import sys
from pathlib import Path


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = Path(
    __file__
).resolve().parent.parent


# ============================================================
# INPUT FILES
# ============================================================

DAY6_KNOWLEDGE = (
    PROJECT_ROOT
    / "results/alu/day6/alu_knowledge.json"
)

DAY7_OBJECTIVES = (
    PROJECT_ROOT
    / "results/alu/day7/verification_objectives.json"
)

DAY13_GAPS = (
    PROJECT_ROOT
    / "results/alu/day13/coverage_gaps.json"
)

DAY14_FEEDBACK = (
    PROJECT_ROOT
    / "results/alu/day13/day14_feedback_input.json"
)


# ============================================================
# DAY-14 FILES
# ============================================================

DAY14_DIR = (
    PROJECT_ROOT
    / "results/alu/day14"
)

PROMPT_FILE = (
    PROJECT_ROOT
    / "hermes/prompts/alu_day14_feedback_prompt.txt"
)

HERMES_RESULT = (
    DAY14_DIR
    / "day14_hermes_result.json"
)

TARGETED_CANDIDATES = (
    DAY14_DIR
    / "targeted_candidate_tests.json"
)

TARGET_GAP_VALIDATION = (
    DAY14_DIR
    / "target_gap_validation.json"
)

TARGETED_VALIDATED = (
    DAY14_DIR
    / "targeted_validated_tests.json"
)

TARGETED_REJECTED = (
    DAY14_DIR
    / "targeted_rejected_tests.json"
)

TARGETED_VALIDATION_REPORT = (
    DAY14_DIR
    / "targeted_validation_report.json"
)


# ============================================================
# PYTHON FILES
# ============================================================

PROMPT_BUILDER = (
    PROJECT_ROOT
    / "hermes/day14_feedback_prompt.py"
)

HERMES_INTERFACE = (
    PROJECT_ROOT
    / "hermes/hermes_interface.py"
)

TARGETED_EXTRACTOR = (
    PROJECT_ROOT
    / "test_generation/targeted_scenario_extractor.py"
)

TARGET_GAP_VALIDATOR = (
    PROJECT_ROOT
    / "test_generation/validate_targeted_gaps.py"
)

TEST_VALIDATOR = (
    PROJECT_ROOT
    / "test_generation/test_validator.py"
)


# ============================================================
# TERMINAL HELPERS
# ============================================================

def separator():
    print()
    print("=" * 60)


def title(text):
    separator()
    print(text)
    separator()


def fail_pipeline(message):
    print()
    print(message)
    print()
    print("=" * 60)
    print(
        "DAY 14 HERMES FEEDBACK PIPELINE: FAIL"
    )
    print("=" * 60)
    return 1


# ============================================================
# JSON HELPERS
# ============================================================

def load_json(path):
    if not path.exists():
        raise FileNotFoundError(
            f"File not found: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8"
    ) as f:
        return json.load(f)


def save_json(path, data):
    path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with path.open(
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            data,
            f,
            indent=2
        )


# ============================================================
# COMMAND RUNNER
# ============================================================

def run_command(command):
    result = subprocess.run(
        command,
        cwd=PROJECT_ROOT
    )

    return result.returncode


# ============================================================
# DAY-13 GAP STATE
# ============================================================

def get_day13_state():
    data = load_json(
        DAY13_GAPS
    )

    status = str(
        data.get(
            "status",
            ""
        )
    ).strip().upper()

    missing_operations = (
        data.get(
            "missing_operations",
            []
        )
        or []
    )

    missing_objectives = (
        data.get(
            "missing_objectives",
            []
        )
        or []
    )

    gaps_detected = data.get(
        "gaps_detected"
    )

    total_gaps = (
        len(missing_operations)
        + len(missing_objectives)
    )

    no_gaps = (
        total_gaps == 0
        and (
            status
            in (
                "NO_GAPS",
                "PASS",
                "COMPLETE"
            )
            or gaps_detected is False
        )
    )

    gaps_found = (
        total_gaps > 0
        or status
        in (
            "GAPS_FOUND",
            "INCOMPLETE"
        )
        or gaps_detected is True
    )

    return {
        "status":
            status,

        "missing_operations":
            missing_operations,

        "missing_objectives":
            missing_objectives,

        "total_gaps":
            total_gaps,

        "no_gaps":
            no_gaps,

        "gaps_found":
            gaps_found,
    }


# ============================================================
# CREATE NO-GAP VALIDATION ARTIFACTS
# ============================================================

def create_no_gap_artifacts():
    """
    In the NO_GAPS branch there are deliberately zero
    targeted candidate tests.

    Create explicit PASS artifacts rather than passing
    an empty candidate list into the normal Day-10
    deterministic validator.
    """

    validated = {
        "status":
            "PASS",

        "mode":
            "NO_GAPS",

        "generation_status":
            "NO_TARGETED_GENERATION_REQUIRED",

        "validated_test_count":
            0,

        "validated_tests":
            [],

        "scenarios":
            [],

        "reason":
            (
                "No targeted validation was required "
                "because Day 13 reported no coverage gaps."
            ),
    }

    rejected = {
        "status":
            "PASS",

        "mode":
            "NO_GAPS",

        "generation_status":
            "NO_TARGETED_GENERATION_REQUIRED",

        "rejected_count":
            0,

        "rejected_test_count":
            0,

        "rejected_scenarios":
            [],

        "rejected_tests":
            [],

        "reason":
            (
                "No targeted tests were generated, "
                "therefore no targeted tests were rejected."
            ),
    }

    report = {
        "status":
            "PASS",

        "mode":
            "NO_GAPS",

        "generation_status":
            "NO_TARGETED_GENERATION_REQUIRED",

        "candidate_test_count":
            0,

        "validated_test_count":
            0,

        "rejected_test_count":
            0,

        "deterministic_validation_required":
            False,

        "reason":
            (
                "Day 13 achieved complete coverage. "
                "No targeted candidate tests required "
                "deterministic validation."
            ),
    }

    save_json(
        TARGETED_VALIDATED,
        validated
    )

    save_json(
        TARGETED_REJECTED,
        rejected
    )

    save_json(
        TARGETED_VALIDATION_REPORT,
        report
    )


# ============================================================
# MAIN
# ============================================================

def main():
    DAY14_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    PROMPT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # ========================================================
    # CHECK DAY-13 STATE
    # ========================================================

    try:
        state = get_day13_state()

    except (
        FileNotFoundError,
        json.JSONDecodeError
    ) as error:
        return fail_pipeline(
            f"ERROR: {error}"
        )

    print()
    print(
        "DAY 13 GAP STATE"
    )
    print(
        "=" * 60
    )

    print(
        "Status          :",
        state["status"]
    )

    print(
        "Operation gaps  :",
        len(
            state["missing_operations"]
        )
    )

    print(
        "Objective gaps  :",
        len(
            state["missing_objectives"]
        )
    )

    print(
        "Total gaps      :",
        state["total_gaps"]
    )

    # ========================================================
    # STEP 1
    # ========================================================

    title(
        "1. BUILD FEEDBACK PROMPT"
    )

    rc = run_command(
        [
            sys.executable,
            str(PROMPT_BUILDER),
            str(DAY14_FEEDBACK),
            str(DAY6_KNOWLEDGE),
            str(DAY7_OBJECTIVES),
            str(PROMPT_FILE),
        ]
    )

    if rc != 0:
        return fail_pipeline(
            "1. BUILD FEEDBACK PROMPT: FAIL"
        )

    print()
    print(
        "1. BUILD FEEDBACK PROMPT: PASS"
    )

    # ========================================================
    # STEP 2
    # ========================================================

    title(
        "2. RUN HERMES"
    )

    if not HERMES_INTERFACE.exists():
        return fail_pipeline(
            "ERROR: hermes/hermes_interface.py "
            "was not found."
        )

    rc = run_command(
        [
            sys.executable,
            str(HERMES_INTERFACE),
            str(PROMPT_FILE),
            str(HERMES_RESULT),
        ]
    )

    if rc != 0:
        return fail_pipeline(
            "2. RUN HERMES: FAIL"
        )

    print()
    print(
        "2. RUN HERMES: PASS"
    )

    # ========================================================
    # STEP 3
    # ========================================================

    title(
        "3. EXTRACT TARGETED SCENARIOS"
    )

    rc = run_command(
        [
            sys.executable,
            str(TARGETED_EXTRACTOR),
            str(HERMES_RESULT),
            str(TARGETED_CANDIDATES),
        ]
    )

    if rc != 0:
        return fail_pipeline(
            "3. EXTRACT TARGETED SCENARIOS: FAIL"
        )

    print()
    print(
        "3. EXTRACT TARGETED SCENARIOS: PASS"
    )

    # ========================================================
    # STEP 4
    # ========================================================

    title(
        "4. VALIDATE TARGETED GAPS"
    )

    rc = run_command(
        [
            sys.executable,
            str(TARGET_GAP_VALIDATOR),
            str(DAY13_GAPS),
            str(TARGETED_CANDIDATES),
            str(TARGET_GAP_VALIDATION),
        ]
    )

    if rc != 0:
        return fail_pipeline(
            "4. VALIDATE TARGETED GAPS: FAIL"
        )

    print()
    print(
        "4. VALIDATE TARGETED GAPS: PASS"
    )

    # ========================================================
    # CRITICAL NO-GAPS BRANCH
    # ========================================================

    if state["no_gaps"]:
        title(
            "5. DETERMINISTIC TEST VALIDATION"
        )

        print(
            "SKIPPED"
        )

        print()
        print(
            "Reason:"
        )

        print(
            "Day 13 reported NO_GAPS."
        )

        print(
            "There are no targeted candidate tests "
            "requiring deterministic validation."
        )

        create_no_gap_artifacts()

        print()
        print(
            "Compatibility artifacts created:"
        )

        print(
            " -",
            TARGETED_VALIDATED.relative_to(
                PROJECT_ROOT
            )
        )

        print(
            " -",
            TARGETED_REJECTED.relative_to(
                PROJECT_ROOT
            )
        )

        print(
            " -",
            TARGETED_VALIDATION_REPORT.relative_to(
                PROJECT_ROOT
            )
        )

        print()
        print(
            "5. DETERMINISTIC TEST VALIDATION: "
            "SKIPPED / PASS"
        )

        separator()

        print(
            "DAY 14 HERMES FEEDBACK PIPELINE: PASS"
        )

        print(
            "Mode: NO_GAPS"
        )

        print(
            "No targeted regeneration was required."
        )

        separator()

        return 0

    # ========================================================
    # GAPS-FOUND BRANCH
    # ========================================================

    if not state["gaps_found"]:
        return fail_pipeline(
            "ERROR: Could not determine a valid "
            "Day-13 gap state."
        )

    # ========================================================
    # STEP 5
    # ========================================================

    title(
        "5. DETERMINISTIC TEST VALIDATION"
    )

    rc = run_command(
        [
            sys.executable,
            str(TEST_VALIDATOR),

            str(TARGETED_CANDIDATES),

            str(DAY6_KNOWLEDGE),

            str(DAY7_OBJECTIVES),

            str(TARGETED_VALIDATED),

            str(TARGETED_REJECTED),

            str(TARGETED_VALIDATION_REPORT),
        ]
    )

    if rc != 0:
        return fail_pipeline(
            "5. DETERMINISTIC TEST VALIDATION: FAIL"
        )

    print()
    print(
        "5. DETERMINISTIC TEST VALIDATION: PASS"
    )

    # ========================================================
    # VERIFY AT LEAST ONE VALIDATED TARGETED TEST
    # ========================================================

    try:
        validation = load_json(
            TARGETED_VALIDATED
        )

        validated_tests = (
            validation.get(
                "validated_tests"
            )
            or validation.get(
                "scenarios"
            )
            or []
        )

    except (
        FileNotFoundError,
        json.JSONDecodeError
    ) as error:
        return fail_pipeline(
            f"ERROR: {error}"
        )

    if not validated_tests:
        return fail_pipeline(
            "ERROR: Day 13 reported gaps, but no "
            "targeted candidate tests passed validation."
        )

    # ========================================================
    # FINAL PASS
    # ========================================================

    separator()

    print(
        "DAY 14 HERMES FEEDBACK PIPELINE: PASS"
    )

    print(
        "Mode: TARGETED_GENERATION"
    )

    print(
        "Validated targeted tests:",
        len(validated_tests)
    )

    separator()

    return 0


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    sys.exit(
        main()
    )
