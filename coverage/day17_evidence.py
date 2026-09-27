#!/usr/bin/env python3

"""
Day 17 - FSM Coverage Closure Evidence

Reads:
    results/fsm/day17/day17_summary.json

Purpose:
    Display final evidence for Day 17 FSM coverage-gap
    identification, targeted test generation and closure.
"""

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

SUMMARY_FILE = (
    ROOT
    / "results"
    / "fsm"
    / "day17"
    / "day17_summary.json"
)


def load_json(path):
    if not path.exists():
        raise FileNotFoundError(
            f"Required file not found: {path}"
        )

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError(
            "Day 17 summary must contain a JSON object."
        )

    return data


def get_dict(data, key):
    value = data.get(key, {})

    if isinstance(value, dict):
        return value

    return {}


def format_percent(value):
    if value is None:
        return "N/A"

    try:
        return f"{float(value):.2f}%"
    except (TypeError, ValueError):
        return "N/A"


def format_bool(value):
    if value is True:
        return "YES"

    if value is False:
        return "NO"

    return "N/A"


def main():

    try:
        s = load_json(SUMMARY_FILE)

        # ----------------------------------------------------
        # Main sections
        # ----------------------------------------------------

        baseline = get_dict(
            s,
            "baseline"
        )

        targeted = get_dict(
            s,
            "targeted_generation"
        )

        targeted_simulation = get_dict(
            s,
            "targeted_simulation"
        )

        closed = get_dict(
            s,
            "closed"
        )

        checks = get_dict(
            s,
            "checks"
        )

        baseline_transition = get_dict(
            baseline,
            "transition_coverage"
        )

        closed_transition = get_dict(
            closed,
            "transition_coverage"
        )

        # ----------------------------------------------------
        # DUT / benchmark
        # ----------------------------------------------------

        benchmark = s.get(
            "benchmark",
            "fsm_1011"
        )

        # ----------------------------------------------------
        # Baseline coverage
        # ----------------------------------------------------

        baseline_total = baseline_transition.get(
            "total_transitions",
            0
        )

        baseline_covered = baseline_transition.get(
            "covered_transitions",
            0
        )

        baseline_percent = baseline_transition.get(
            "coverage_percent",
            0.0
        )

        baseline_missing = baseline.get(
            "missing_transition_ids",
            baseline_transition.get(
                "missing_transition_ids",
                []
            )
        )

        if not isinstance(
            baseline_missing,
            list
        ):
            baseline_missing = []

        baseline_gap_count = baseline.get(
            "gap_count",
            len(baseline_missing)
        )

        # ----------------------------------------------------
        # Targeted sequence generation
        # ----------------------------------------------------

        target_count = targeted.get(
            "target_count",
            0
        )

        targeted_ids = targeted.get(
            "generated_transition_ids",
            []
        )

        if not isinstance(
            targeted_ids,
            list
        ):
            targeted_ids = []

        unresolved_count = targeted.get(
            "unresolved_target_count",
            0
        )

        generation_method = targeted.get(
            "generation_method",
            "N/A"
        )

        source_gap_status = targeted.get(
            "source_gap_status",
            "N/A"
        )

        # ----------------------------------------------------
        # Targeted simulation
        # ----------------------------------------------------

        simulation_pass = targeted_simulation.get(
            "closure_pass"
        )

        tr005_status = targeted_simulation.get(
            "tr_005_covered"
        )

        tr007_status = targeted_simulation.get(
            "tr_007_covered"
        )

        # ----------------------------------------------------
        # Final closed coverage
        # ----------------------------------------------------

        final_total = closed_transition.get(
            "total_transitions",
            0
        )

        final_covered = closed_transition.get(
            "covered_transitions",
            0
        )

        final_percent = closed_transition.get(
            "coverage_percent",
            0.0
        )

        final_complete = closed_transition.get(
            "coverage_complete",
            False
        )

        remaining_ids = closed.get(
            "remaining_transition_ids",
            []
        )

        if not isinstance(
            remaining_ids,
            list
        ):
            remaining_ids = []

        remaining_gap_count = closed.get(
            "remaining_gap_count",
            len(remaining_ids)
        )

        # ----------------------------------------------------
        # Coverage gain
        # ----------------------------------------------------

        coverage_gain = s.get(
            "coverage_gain_percent"
        )

        if coverage_gain is None:
            try:
                coverage_gain = (
                    float(final_percent)
                    - float(baseline_percent)
                )
            except (TypeError, ValueError):
                coverage_gain = 0.0

        # ----------------------------------------------------
        # Final status
        # ----------------------------------------------------

        day17_complete = s.get(
            "day17_complete",
            False
        )

        status = s.get(
            "status",
            "UNKNOWN"
        )

        # ====================================================
        # PRINT EVIDENCE
        # ====================================================

        print("=" * 72)
        print("DAY 17 - FSM COVERAGE CLOSURE EVIDENCE")
        print("=" * 72)

        print(
            "DUT / benchmark                 :",
            benchmark
        )

        print(
            "Baseline transition coverage    :",
            format_percent(
                baseline_percent
            )
        )

        print(
            "Baseline covered transitions    :",
            f"{baseline_covered}/{baseline_total}"
        )

        print(
            "Baseline gap count              :",
            baseline_gap_count
        )

        print(
            "Initial transition gaps         :",
            baseline_missing
        )

        print("-" * 72)

        print(
            "Source gap status               :",
            source_gap_status
        )

        print(
            "Targeted sequences generated    :",
            target_count
        )

        print(
            "Targeted transition IDs         :",
            targeted_ids
        )

        print(
            "Unresolved targeted sequences   :",
            unresolved_count
        )

        print(
            "Generation method               :",
            generation_method
        )

        print("-" * 72)

        print(
            "Targeted simulation PASS        :",
            format_bool(
                simulation_pass
            )
        )

        print(
            "TR_005 covered                  :",
            format_bool(
                tr005_status
            )
        )

        print(
            "TR_007 covered                  :",
            format_bool(
                tr007_status
            )
        )

        print("-" * 72)

        print(
            "Final transition coverage       :",
            format_percent(
                final_percent
            )
        )

        print(
            "Final covered transitions       :",
            f"{final_covered}/{final_total}"
        )

        print(
            "Transition coverage delta       :",
            format_percent(
                coverage_gain
            )
        )

        print(
            "Remaining transition gaps       :",
            remaining_ids
        )

        print(
            "Remaining gap count             :",
            remaining_gap_count
        )

        print(
            "Final coverage complete         :",
            format_bool(
                final_complete
            )
        )

        print("-" * 72)

        print(
            "Baseline gap detected           :",
            format_bool(
                checks.get(
                    "baseline_gap_detected"
                )
            )
        )

        print(
            "Targeted sequences generated    :",
            format_bool(
                checks.get(
                    "targeted_sequences_generated"
                )
            )
        )

        print(
            "Coverage improved               :",
            format_bool(
                checks.get(
                    "coverage_improved"
                )
            )
        )

        print(
            "Final transition coverage 100%  :",
            format_bool(
                checks.get(
                    "final_transition_coverage_100"
                )
            )
        )

        print(
            "No remaining gaps               :",
            format_bool(
                checks.get(
                    "no_remaining_gaps"
                )
            )
        )

        print("-" * 72)

        print(
            "DAY 17 COMPLETE                 :",
            format_bool(
                day17_complete
            )
        )

        print(
            "DAY 17 STATUS                   :",
            status
        )

        print("=" * 72)

        if (
            day17_complete is True
            and status == "PASS"
        ):
            print(
                "DAY 17 EVIDENCE: PASS"
            )
            return 0

        print(
            "DAY 17 EVIDENCE: FAIL"
        )

        return 1

    except (
        FileNotFoundError,
        json.JSONDecodeError,
        ValueError,
        TypeError,
        OSError
    ) as exc:

        print(
            "DAY 17 EVIDENCE: FAIL"
        )

        print(
            f"ERROR: {exc}"
        )

        return 1


if __name__ == "__main__":
    sys.exit(main())
