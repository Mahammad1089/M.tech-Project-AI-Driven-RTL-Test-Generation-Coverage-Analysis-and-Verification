#!/usr/bin/env python3

"""
Day 17 - FSM Coverage Gap Analyzer

Project:
AI-Driven RTL Test Generation, Coverage Analysis and Verification

Purpose:
1. Read Day-17 FSM baseline transition coverage.
2. Identify uncovered FSM transitions.
3. Generate a machine-readable gap report.
4. Prepare coverage gaps for targeted test generation.

Input:
results/fsm/day17/fsm_baseline_coverage.json

Output:
results/fsm/day17/fsm_gap_report.json
"""

import argparse
import json
import sys
from pathlib import Path


# ============================================================
# PROJECT PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

DEFAULT_INPUT = (
    ROOT
    / "results"
    / "fsm"
    / "day17"
    / "fsm_baseline_coverage.json"
)

DEFAULT_OUTPUT = (
    ROOT
    / "results"
    / "fsm"
    / "day17"
    / "fsm_gap_report.json"
)


# ============================================================
# JSON LOAD FUNCTION
# ============================================================

def load_json(path):
    """
    Load JSON file and return Python dictionary.
    """

    if not path.exists():
        raise FileNotFoundError(
            f"Input file not found: {path}"
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

    if not isinstance(
        data,
        dict
    ):

        raise ValueError(
            f"Expected JSON object in {path}, "
            f"but found {type(data).__name__}"
        )

    return data


# ============================================================
# JSON SAVE FUNCTION
# ============================================================

def save_json(
    path,
    data
):
    """
    Save dictionary as formatted JSON.
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
# FIND TRANSITION COVERAGE SECTION
# ============================================================

def get_transition_coverage(
    data
):
    """
    Support two possible coverage JSON structures.

    Structure 1:

    {
        "transition_coverage": {
            ...
        }
    }

    Structure 2:

    {
        "total_transitions": 8,
        "covered_transitions": 6,
        ...
    }
    """

    transition_section = data.get(
        "transition_coverage"
    )

    if isinstance(
        transition_section,
        dict
    ):

        return transition_section


    expected_keys = {
        "total_transitions",
        "covered_transitions",
        "coverage_percent",
        "covered_transition_ids",
        "missing_transition_ids",
        "transition_hits",
    }


    if any(
        key in data
        for key in expected_keys
    ):

        return data


    raise KeyError(
        "Transition coverage information "
        "not found in baseline coverage JSON."
    )


# ============================================================
# CLEAN UNIQUE LIST
# ============================================================

def unique_list(
    values
):
    """
    Remove duplicate transition IDs while
    preserving original order.
    """

    result = []

    seen = set()


    for value in values:

        text = str(
            value
        ).strip()


        if not text:

            continue


        if text in seen:

            continue


        seen.add(
            text
        )

        result.append(
            text
        )


    return result


# ============================================================
# NORMALIZE TRANSITION HIT COUNTS
# ============================================================

def normalize_transition_hits(
    section
):
    """
    Convert transition hit counts into:

    {
        "TR_001": 5,
        "TR_002": 3,
        ...
    }
    """

    raw_hits = section.get(
        "transition_hits",
        {}
    )


    if not isinstance(
        raw_hits,
        dict
    ):

        return {}


    hits = {}


    for (
        transition_id,
        value
    ) in raw_hits.items():

        try:

            count = int(
                value
            )

        except (
            TypeError,
            ValueError
        ):

            count = 0


        if count < 0:

            count = 0


        hits[
            str(
                transition_id
            )
        ] = count


    return hits


# ============================================================
# GET MISSING TRANSITIONS
# ============================================================

def get_missing_transition_ids(
    section,
    transition_hits
):
    """
    Read explicitly missing transitions.

    If unavailable, derive them from
    transition hit count == 0.
    """

    raw_missing = section.get(
        "missing_transition_ids"
    )


    if isinstance(
        raw_missing,
        list
    ):

        missing = unique_list(
            raw_missing
        )


        if missing:

            return missing


    missing = []


    for (
        transition_id,
        hit_count
    ) in transition_hits.items():

        if hit_count == 0:

            missing.append(
                transition_id
            )


    return missing


# ============================================================
# GET COVERED TRANSITIONS
# ============================================================

def get_covered_transition_ids(
    section,
    transition_hits
):
    """
    Read explicitly covered transition IDs.

    If unavailable, derive them from
    transition hit count > 0.
    """

    raw_covered = section.get(
        "covered_transition_ids"
    )


    if isinstance(
        raw_covered,
        list
    ):

        covered = unique_list(
            raw_covered
        )


        if covered:

            return covered


    covered = []


    for (
        transition_id,
        hit_count
    ) in transition_hits.items():

        if hit_count > 0:

            covered.append(
                transition_id
            )


    return covered


# ============================================================
# SAFE INTEGER CONVERSION
# ============================================================

def to_int(
    value,
    default
):

    try:

        return int(
            value
        )

    except (
        TypeError,
        ValueError
    ):

        return default


# ============================================================
# SAFE FLOAT CONVERSION
# ============================================================

def to_float(
    value,
    default
):

    try:

        return float(
            value
        )

    except (
        TypeError,
        ValueError
    ):

        return default


# ============================================================
# BUILD COVERAGE GAP REPORT
# ============================================================

def build_gap_report(
    coverage_data
):

    transition_section = get_transition_coverage(
        coverage_data
    )


    transition_hits = normalize_transition_hits(
        transition_section
    )


    missing_ids = get_missing_transition_ids(
        transition_section,
        transition_hits
    )


    covered_ids = get_covered_transition_ids(
        transition_section,
        transition_hits
    )


    # --------------------------------------------------------
    # Determine total number of transitions
    # --------------------------------------------------------

    all_transition_ids = set(
        transition_hits.keys()
    )

    all_transition_ids.update(
        missing_ids
    )

    all_transition_ids.update(
        covered_ids
    )


    total_transitions = to_int(
        transition_section.get(
            "total_transitions"
        ),
        len(
            all_transition_ids
        )
    )


    # --------------------------------------------------------
    # Determine number of covered transitions
    # --------------------------------------------------------

    covered_transitions = to_int(
        transition_section.get(
            "covered_transitions"
        ),
        len(
            covered_ids
        )
    )


    # --------------------------------------------------------
    # Calculate coverage percentage
    # --------------------------------------------------------

    if total_transitions > 0:

        calculated_percent = round(
            (
                covered_transitions
                / total_transitions
            )
            * 100.0,
            2
        )

    else:

        calculated_percent = 0.0


    coverage_percent = to_float(
        transition_section.get(
            "coverage_percent"
        ),
        calculated_percent
    )


    # --------------------------------------------------------
    # Build gap objects
    # --------------------------------------------------------

    gaps = []


    for transition_id in missing_ids:

        hit_count = transition_hits.get(
            transition_id,
            0
        )


        gap = {

            "gap_id":
                f"GAP_{transition_id}",

            "coverage_type":
                "fsm_transition",

            "transition_id":
                transition_id,

            "hit_count":
                hit_count,

            "status":
                "uncovered",

            "priority":
                "high",

            "objective":
                (
                    "Generate a targeted FSM test "
                    "that exercises transition "
                    f"{transition_id}."
                ),
        }


        gaps.append(
            gap
        )


    # --------------------------------------------------------
    # Coverage completion status
    # --------------------------------------------------------

    coverage_complete = (
        len(
            missing_ids
        )
        == 0
    )


    # --------------------------------------------------------
    # Final report
    # --------------------------------------------------------

    gap_report = {

        "stage":
            "day17_fsm_gap_analysis",

        "source_file":
            "fsm_baseline_coverage.json",

        "baseline_summary": {

            "total_transitions":
                total_transitions,

            "covered_transitions":
                covered_transitions,

            "missing_transitions":
                len(
                    missing_ids
                ),

            "coverage_percent":
                coverage_percent,

            "coverage_complete":
                coverage_complete,
        },

        "covered_transition_ids":
            covered_ids,

        "missing_transition_ids":
            missing_ids,

        "transition_hits":
            transition_hits,

        "gap_count":
            len(
                gaps
            ),

        "gaps":
            gaps,

        "next_action":
            (
                "Generate targeted tests for the "
                "uncovered FSM transitions and "
                "re-run simulation."
                if gaps
                else
                "No FSM transition coverage "
                "gaps remain."
            ),
    }


    return gap_report


# ============================================================
# PRINT GAP REPORT
# ============================================================

def print_report(
    report
):

    summary = report[
        "baseline_summary"
    ]


    print(
        "=" * 60
    )

    print(
        "DAY 17 FSM COVERAGE GAP ANALYSIS"
    )

    print(
        "=" * 60
    )


    print(
        "Total transitions   : "
        f"{summary['total_transitions']}"
    )


    print(
        "Covered transitions : "
        f"{summary['covered_transitions']}"
    )


    print(
        "Missing transitions : "
        f"{summary['missing_transitions']}"
    )


    print(
        "Coverage percent    : "
        f"{summary['coverage_percent']:.2f}%"
    )


    print(
        "-" * 60
    )


    missing_ids = report[
        "missing_transition_ids"
    ]


    if missing_ids:

        print(
            "Missing transition IDs:"
        )


        for transition_id in missing_ids:

            print(
                f"  - {transition_id}"
            )


    else:

        print(
            "Missing transition IDs: none"
        )


    print(
        "-" * 60
    )


    print(
        "Gap count           : "
        f"{report['gap_count']}"
    )


    print(
        "Next action         : "
        f"{report['next_action']}"
    )


    print(
        "=" * 60
    )


# ============================================================
# ARGUMENT PARSER
# ============================================================

def parse_arguments():

    parser = argparse.ArgumentParser(

        description=(
            "Analyze Day 17 FSM baseline "
            "transition coverage and "
            "generate a gap report."
        )
    )


    parser.add_argument(

        "--input",

        type=Path,

        default=DEFAULT_INPUT,

        help=(
            "Input FSM baseline coverage JSON."
        )
    )


    parser.add_argument(

        "--output",

        type=Path,

        default=DEFAULT_OUTPUT,

        help=(
            "Output FSM gap report JSON."
        )
    )


    return parser.parse_args()


# ============================================================
# MAIN
# ============================================================

def main():

    args = parse_arguments()


    input_path = args.input

    output_path = args.output


    # --------------------------------------------------------
    # Resolve relative paths
    # --------------------------------------------------------

    if not input_path.is_absolute():

        input_path = (
            ROOT
            / input_path
        )


    if not output_path.is_absolute():

        output_path = (
            ROOT
            / output_path
        )


    # --------------------------------------------------------
    # Run gap analysis
    # --------------------------------------------------------

    try:

        coverage_data = load_json(
            input_path
        )


        gap_report = build_gap_report(
            coverage_data
        )


        save_json(
            output_path,
            gap_report
        )


    except (
        FileNotFoundError,
        ValueError,
        KeyError,
        OSError
    ) as exc:

        print(
            f"ERROR: {exc}",
            file=sys.stderr
        )

        return 1


    # --------------------------------------------------------
    # Print result
    # --------------------------------------------------------

    print_report(
        gap_report
    )


    try:

        displayed_output = (
            output_path.relative_to(
                ROOT
            )
        )

    except ValueError:

        displayed_output = (
            output_path
        )


    print(
        "Gap report written to: "
        f"{displayed_output}"
    )


    return 0


# ============================================================
# PROGRAM ENTRY
# ============================================================

if __name__ == "__main__":

    sys.exit(
        main()
    )
