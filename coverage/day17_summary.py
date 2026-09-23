#!/usr/bin/env python3

"""
Day 17 - FSM Coverage Closure Summary

Project:
AI-Driven RTL Test Generation,
Coverage Analysis and Verification

Purpose:
1. Read Day-17 baseline FSM coverage.
2. Read baseline coverage gaps.
3. Read targeted sequence generation results.
4. Read final/closed FSM coverage.
5. Read remaining gaps after targeted closure.
6. Confirm that coverage improved from baseline to closure.
7. Generate a final Day-17 summary JSON.

Expected Day-17 files:

results/fsm/day17/
    fsm_baseline_coverage.json
    fsm_baseline_gaps.json
    fsm_targeted_sequences.json
    fsm_closed_coverage.json
    fsm_remaining_gaps.json
    fsm_targeted.log

Output:

results/fsm/day17/day17_summary.json
"""

import json
import sys
from pathlib import Path


# ============================================================
# PROJECT PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

DAY17_DIR = (
    ROOT
    / "results"
    / "fsm"
    / "day17"
)

BASELINE_COVERAGE_FILE = (
    DAY17_DIR
    / "fsm_baseline_coverage.json"
)

BASELINE_GAPS_FILE = (
    DAY17_DIR
    / "fsm_baseline_gaps.json"
)

TARGETED_SEQUENCES_FILE = (
    DAY17_DIR
    / "fsm_targeted_sequences.json"
)

CLOSED_COVERAGE_FILE = (
    DAY17_DIR
    / "fsm_closed_coverage.json"
)

REMAINING_GAPS_FILE = (
    DAY17_DIR
    / "fsm_remaining_gaps.json"
)

TARGETED_LOG_FILE = (
    DAY17_DIR
    / "fsm_targeted.log"
)

OUTPUT_FILE = (
    DAY17_DIR
    / "day17_summary.json"
)


# ============================================================
# JSON HELPERS
# ============================================================

def load_json(path):
    """
    Load and validate a JSON object.
    """

    if not path.exists():
        raise FileNotFoundError(
            f"Required file not found: {path}"
        )

    try:

        with path.open(
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

    except json.JSONDecodeError as exc:

        raise ValueError(
            f"Invalid JSON in {path}: "
            f"line {exc.lineno}, "
            f"column {exc.colno}: "
            f"{exc.msg}"
        ) from exc

    if not isinstance(data, dict):

        raise ValueError(
            f"Expected JSON object in {path}"
        )

    return data


def save_json(path, data):
    """
    Save formatted JSON.
    """

    path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with path.open(
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            indent=2
        )

        file.write("\n")


# ============================================================
# SAFE NUMBER CONVERSION
# ============================================================

def safe_int(value, default=0):

    try:
        return int(value)

    except (
        TypeError,
        ValueError
    ):
        return default


def safe_float(value, default=0.0):

    try:
        return float(value)

    except (
        TypeError,
        ValueError
    ):
        return default


# ============================================================
# TRANSITION COVERAGE EXTRACTION
# ============================================================

def get_transition_section(data):
    """
    Support both:

    {
        "transition_coverage": {...}
    }

    and flat transition coverage JSON.
    """

    section = data.get(
        "transition_coverage"
    )

    if isinstance(section, dict):
        return section

    transition_keys = {
        "total_transitions",
        "covered_transitions",
        "coverage_percent",
        "covered_transition_ids",
        "missing_transition_ids",
        "transition_hits",
    }

    if any(
        key in data
        for key in transition_keys
    ):
        return data

    return {}


def extract_transition_coverage(data):
    """
    Return normalized transition coverage information.
    """

    section = get_transition_section(
        data
    )

    covered_ids = section.get(
        "covered_transition_ids",
        []
    )

    missing_ids = section.get(
        "missing_transition_ids",
        []
    )

    hits = section.get(
        "transition_hits",
        {}
    )

    if not isinstance(covered_ids, list):
        covered_ids = []

    if not isinstance(missing_ids, list):
        missing_ids = []

    if not isinstance(hits, dict):
        hits = {}

    # --------------------------------------------------------
    # Total transitions
    # --------------------------------------------------------

    derived_ids = set(
        str(item)
        for item in covered_ids
    )

    derived_ids.update(
        str(item)
        for item in missing_ids
    )

    derived_ids.update(
        str(item)
        for item in hits.keys()
    )

    total = safe_int(
        section.get(
            "total_transitions"
        ),
        len(derived_ids)
    )

    # --------------------------------------------------------
    # Covered transitions
    # --------------------------------------------------------

    if "covered_transitions" in section:

        covered = safe_int(
            section.get(
                "covered_transitions"
            ),
            0
        )

    elif covered_ids:

        covered = len(
            covered_ids
        )

    else:

        covered = sum(
            1
            for value in hits.values()
            if safe_int(value, 0) > 0
        )

    # --------------------------------------------------------
    # Missing transitions
    # --------------------------------------------------------

    if missing_ids:

        missing = len(
            missing_ids
        )

    elif total >= covered:

        missing = (
            total
            - covered
        )

    else:

        missing = 0

    # --------------------------------------------------------
    # Coverage percentage
    # --------------------------------------------------------

    if "coverage_percent" in section:

        percent = safe_float(
            section.get(
                "coverage_percent"
            ),
            0.0
        )

    elif total > 0:

        percent = round(
            (
                covered
                / total
            )
            * 100.0,
            2
        )

    else:

        percent = 0.0

    coverage_complete = data.get(
        "coverage_complete"
    )

    if coverage_complete is None:

        coverage_complete = section.get(
            "coverage_complete"
        )

    if coverage_complete is None:

        coverage_complete = (
            total > 0
            and covered == total
            and missing == 0
        )

    return {

        "total_transitions":
            total,

        "covered_transitions":
            covered,

        "missing_transitions":
            missing,

        "coverage_percent":
            percent,

        "covered_transition_ids":
            covered_ids,

        "missing_transition_ids":
            missing_ids,

        "coverage_complete":
            bool(
                coverage_complete
            ),
    }


# ============================================================
# OPTIONAL STATE COVERAGE EXTRACTION
# ============================================================

def extract_state_coverage(data):
    """
    State coverage is optional.

    Day 17 closure is primarily evaluated using
    transition coverage. This function does NOT require
    state_gap_count or any legacy state-gap field.
    """

    section = data.get(
        "state_coverage"
    )

    if not isinstance(
        section,
        dict
    ):

        return None

    total_states = safe_int(
        section.get(
            "total_states"
        ),
        0
    )

    covered_states = safe_int(
        section.get(
            "covered_states"
        ),
        0
    )

    missing_ids = section.get(
        "missing_state_ids",
        []
    )

    if not isinstance(
        missing_ids,
        list
    ):
        missing_ids = []

    if "coverage_percent" in section:

        coverage_percent = safe_float(
            section.get(
                "coverage_percent"
            ),
            0.0
        )

    elif total_states > 0:

        coverage_percent = round(
            (
                covered_states
                / total_states
            )
            * 100.0,
            2
        )

    else:

        coverage_percent = 0.0

    return {

        "total_states":
            total_states,

        "covered_states":
            covered_states,

        "missing_states":
            len(
                missing_ids
            ),

        "missing_state_ids":
            missing_ids,

        "coverage_percent":
            coverage_percent,
    }


# ============================================================
# GAP REPORT EXTRACTION
# ============================================================

def extract_gap_information(data):
    """
    Support the current gap-analyzer format.

    Does not require legacy fields such as:
        state_gap_count
        transition_gap_count
    """

    missing_transition_ids = (
        data.get(
            "missing_transition_ids",
            []
        )
    )

    if not isinstance(
        missing_transition_ids,
        list
    ):

        missing_transition_ids = []

    gaps = data.get(
        "gaps",
        []
    )

    if not isinstance(
        gaps,
        list
    ):

        gaps = []

    if "gap_count" in data:

        gap_count = safe_int(
            data.get(
                "gap_count"
            ),
            len(gaps)
        )

    elif gaps:

        gap_count = len(
            gaps
        )

    else:

        gap_count = len(
            missing_transition_ids
        )

    baseline_summary = data.get(
        "baseline_summary",
        {}
    )

    if not isinstance(
        baseline_summary,
        dict
    ):

        baseline_summary = {}

    return {

        "gap_count":
            gap_count,

        "missing_transition_ids":
            missing_transition_ids,

        "coverage_percent":
            safe_float(
                baseline_summary.get(
                    "coverage_percent"
                ),
                0.0
            ),

        "coverage_complete":
            bool(
                baseline_summary.get(
                    "coverage_complete",
                    gap_count == 0
                )
            ),
    }


# ============================================================
# TARGETED SEQUENCE EXTRACTION
# ============================================================

def extract_targeted_sequences(data):

    targets = data.get(
        "targets",
        []
    )

    if not isinstance(
        targets,
        list
    ):

        targets = []

    generated_targets = [

        target
        for target in targets

        if (
            isinstance(
                target,
                dict
            )
            and target.get(
                "status"
            )
            == "generated"
        )
    ]

    unresolved_targets = [

        target
        for target in targets

        if (
            isinstance(
                target,
                dict
            )
            and target.get(
                "status"
            )
            != "generated"
        )
    ]

    target_count = safe_int(
        data.get(
            "target_count"
        ),
        len(
            generated_targets
        )
    )

    unresolved_count = safe_int(
        data.get(
            "unresolved_target_count"
        ),
        len(
            unresolved_targets
        )
    )

    transition_ids = []

    for target in generated_targets:

        transition_id = target.get(
            "transition_id"
        )

        if transition_id is not None:

            transition_ids.append(
                str(
                    transition_id
                )
            )

    return {

        "target_count":
            target_count,

        "generated_transition_ids":
            transition_ids,

        "unresolved_target_count":
            unresolved_count,

        "generation_method":
            data.get(
                "generation_method"
            ),

        "source_gap_status":
            data.get(
                "source_gap_status"
            ),
    }


# ============================================================
# TARGETED SIMULATION LOG
# ============================================================

def read_targeted_log_status(path):
    """
    Read FSM closure PASS/FAIL from targeted log.

    This file is optional for summary generation,
    but if present its status is recorded.
    """

    if not path.exists():

        return {

            "log_present":
                False,

            "closure_pass":
                None,

            "tr_005_covered":
                None,

            "tr_007_covered":
                None,
        }

    text = path.read_text(
        encoding="utf-8",
        errors="replace"
    )

    return {

        "log_present":
            True,

        "closure_pass":
            (
                "FSM_DAY17_CLOSURE: PASS"
                in text
            ),

        "tr_005_covered":
            (
                "TR_005_STATUS = COVERED"
                in text
            ),

        "tr_007_covered":
            (
                "TR_007_STATUS = COVERED"
                in text
            ),
    }


# ============================================================
# BUILD DAY 17 SUMMARY
# ============================================================

def build_summary(
    baseline_coverage_data,
    baseline_gaps_data,
    targeted_sequences_data,
    closed_coverage_data,
    remaining_gaps_data,
    targeted_log_status
):

    baseline = (
        extract_transition_coverage(
            baseline_coverage_data
        )
    )

    closed = (
        extract_transition_coverage(
            closed_coverage_data
        )
    )

    baseline_states = (
        extract_state_coverage(
            baseline_coverage_data
        )
    )

    closed_states = (
        extract_state_coverage(
            closed_coverage_data
        )
    )

    baseline_gaps = (
        extract_gap_information(
            baseline_gaps_data
        )
    )

    remaining_gaps = (
        extract_gap_information(
            remaining_gaps_data
        )
    )

    targeted = (
        extract_targeted_sequences(
            targeted_sequences_data
        )
    )

    coverage_gain = round(
        (
            closed[
                "coverage_percent"
            ]
            -
            baseline[
                "coverage_percent"
            ]
        ),
        2
    )

    baseline_has_gaps = (
        baseline_gaps[
            "gap_count"
        ]
        > 0
    )

    targets_generated = (
        targeted[
            "target_count"
        ]
        > 0
        and targeted[
            "unresolved_target_count"
        ]
        == 0
    )

    no_remaining_gaps = (
        remaining_gaps[
            "gap_count"
        ]
        == 0
        and len(
            remaining_gaps[
                "missing_transition_ids"
            ]
        )
        == 0
    )

    final_coverage_complete = (
        closed[
            "coverage_complete"
        ]
        and closed[
            "missing_transitions"
        ]
        == 0
        and closed[
            "covered_transitions"
        ]
        == closed[
            "total_transitions"
        ]
    )

    final_coverage_100 = (
        abs(
            closed[
                "coverage_percent"
            ]
            - 100.0
        )
        < 0.0001
    )

    coverage_improved = (
        closed[
            "coverage_percent"
        ]
        >
        baseline[
            "coverage_percent"
        ]
    )

    # --------------------------------------------------------
    # Log is supporting evidence.
    #
    # If it exists, require PASS.
    # If it does not exist, JSON coverage results are enough.
    # --------------------------------------------------------

    log_ok = (

        targeted_log_status[
            "closure_pass"
        ]
        is not False
    )

    day17_pass = all(
        [
            baseline_has_gaps,
            targets_generated,
            no_remaining_gaps,
            final_coverage_complete,
            final_coverage_100,
            coverage_improved,
            log_ok,
        ]
    )

    return {

        "day":
            17,

        "benchmark":
            "fsm_1011",

        "objective":
            (
                "Demonstrate coverage-guided FSM "
                "transition-gap identification, "
                "targeted sequence generation and "
                "coverage closure."
            ),

        "baseline": {

            "transition_coverage":
                baseline,

            "state_coverage":
                baseline_states,

            "gap_count":
                baseline_gaps[
                    "gap_count"
                ],

            "missing_transition_ids":
                baseline_gaps[
                    "missing_transition_ids"
                ],
        },

        "targeted_generation": {

            "target_count":
                targeted[
                    "target_count"
                ],

            "generated_transition_ids":
                targeted[
                    "generated_transition_ids"
                ],

            "unresolved_target_count":
                targeted[
                    "unresolved_target_count"
                ],

            "generation_method":
                targeted[
                    "generation_method"
                ],

            "source_gap_status":
                targeted[
                    "source_gap_status"
                ],
        },

        "targeted_simulation": {
            **targeted_log_status
        },

        "closed": {

            "transition_coverage":
                closed,

            "state_coverage":
                closed_states,

            "remaining_gap_count":
                remaining_gaps[
                    "gap_count"
                ],

            "remaining_transition_ids":
                remaining_gaps[
                    "missing_transition_ids"
                ],
        },

        "coverage_gain_percent":
            coverage_gain,

        "checks": {

            "baseline_gap_detected":
                baseline_has_gaps,

            "targeted_sequences_generated":
                targets_generated,

            "coverage_improved":
                coverage_improved,

            "final_transition_coverage_100":
                final_coverage_100,

            "final_coverage_complete":
                final_coverage_complete,

            "no_remaining_gaps":
                no_remaining_gaps,

            "targeted_log_consistent":
                log_ok,
        },

        "day17_complete":
            day17_pass,

        "status":
            (
                "PASS"
                if day17_pass
                else "FAIL"
            ),
    }


# ============================================================
# PRINT SUMMARY
# ============================================================

def print_summary(summary):

    baseline = (
        summary[
            "baseline"
        ][
            "transition_coverage"
        ]
    )

    targeted = (
        summary[
            "targeted_generation"
        ]
    )

    closed = (
        summary[
            "closed"
        ][
            "transition_coverage"
        ]
    )

    print(
        "=" * 64
    )

    print(
        "DAY 17 FSM COVERAGE CLOSURE SUMMARY"
    )

    print(
        "=" * 64
    )

    print(
        "Baseline transition coverage : "
        f"{baseline['coverage_percent']:.2f}%"
    )

    print(
        "Baseline covered transitions : "
        f"{baseline['covered_transitions']}"
        f"/{baseline['total_transitions']}"
    )

    print(
        "Baseline gap count            : "
        f"{summary['baseline']['gap_count']}"
    )

    print(
        "Baseline missing transitions  : "
        f"{summary['baseline']['missing_transition_ids']}"
    )

    print(
        "-" * 64
    )

    print(
        "Targeted sequences generated  : "
        f"{targeted['target_count']}"
    )

    print(
        "Targeted transition IDs       : "
        f"{targeted['generated_transition_ids']}"
    )

    print(
        "Unresolved targets            : "
        f"{targeted['unresolved_target_count']}"
    )

    print(
        "-" * 64
    )

    print(
        "Closed transition coverage   : "
        f"{closed['coverage_percent']:.2f}%"
    )

    print(
        "Closed covered transitions   : "
        f"{closed['covered_transitions']}"
        f"/{closed['total_transitions']}"
    )

    print(
        "Remaining gap count          : "
        f"{summary['closed']['remaining_gap_count']}"
    )

    print(
        "Remaining transitions        : "
        f"{summary['closed']['remaining_transition_ids']}"
    )

    print(
        "Coverage gain                : "
        f"{summary['coverage_gain_percent']:.2f}%"
    )

    print(
        "-" * 64
    )

    print(
        "DAY 17 COMPLETE              : "
        f"{summary['day17_complete']}"
    )

    print(
        "DAY 17 STATUS                : "
        f"{summary['status']}"
    )

    print(
        "=" * 64
    )


# ============================================================
# MAIN
# ============================================================

def main():

    try:

        baseline_coverage_data = load_json(
            BASELINE_COVERAGE_FILE
        )

        baseline_gaps_data = load_json(
            BASELINE_GAPS_FILE
        )

        targeted_sequences_data = load_json(
            TARGETED_SEQUENCES_FILE
        )

        closed_coverage_data = load_json(
            CLOSED_COVERAGE_FILE
        )

        remaining_gaps_data = load_json(
            REMAINING_GAPS_FILE
        )

        targeted_log_status = (
            read_targeted_log_status(
                TARGETED_LOG_FILE
            )
        )

        summary = build_summary(
            baseline_coverage_data,
            baseline_gaps_data,
            targeted_sequences_data,
            closed_coverage_data,
            remaining_gaps_data,
            targeted_log_status,
        )

        save_json(
            OUTPUT_FILE,
            summary
        )

    except (
        FileNotFoundError,
        ValueError,
        KeyError,
        TypeError,
        OSError
    ) as exc:

        print(
            "DAY 17 SUMMARY: FAIL"
        )

        print(
            f"ERROR: {exc}"
        )

        return 1

    print_summary(
        summary
    )

    print(
        "Summary written to: "
        "results/fsm/day17/day17_summary.json"
    )

    if summary[
        "day17_complete"
    ]:

        print(
            "DAY 17 SUMMARY: PASS"
        )

        return 0

    print(
        "DAY 17 SUMMARY: FAIL"
    )

    return 1


# ============================================================
# PROGRAM ENTRY
# ============================================================

if __name__ == "__main__":

    sys.exit(
        main()
    )
