#!/usr/bin/env python3

"""
Day 22 - Graph 4
================

Verification Effort vs Functional Coverage

Project:
AI-Driven RTL Test Generation,
Coverage Analysis and Verification

Purpose
-------
Compare the measured verification effort of the Day-20
verification strategies using:

    X-axis : Stimulus cycles
    Y-axis : Functional coverage (%)

Strategies:
    - Manual Directed
    - Random
    - Feedback Driven

Primary input:
    results/fifo/day22/day22_graph_data.json

Fallback:
    results/fifo/day22/graph_data.json

Current schema:
    day20_strategy_comparison

Old-schema fallback:
    strategy_comparison

Outputs:
    graphs/day22_graph4_verification_effort.png
    results/fifo/day22/graph4_verification_effort.png
"""

import json
import shutil
import sys
from pathlib import Path

import matplotlib.pyplot as plt


# ============================================================
# PROJECT PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

DAY22_DIR = (
    ROOT
    / "results"
    / "fifo"
    / "day22"
)

PRIMARY_INPUT = (
    DAY22_DIR
    / "day22_graph_data.json"
)

FALLBACK_INPUT = (
    DAY22_DIR
    / "graph_data.json"
)

GRAPH_OUTPUT = (
    ROOT
    / "graphs"
    / "day22_graph4_verification_effort.png"
)

RESULT_OUTPUT = (
    DAY22_DIR
    / "graph4_verification_effort.png"
)


# ============================================================
# JSON LOADING
# ============================================================

def load_json(path):

    if not path.exists():

        raise FileNotFoundError(
            f"Required graph-data file not found: {path}"
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
            "Day 22 graph data must contain a JSON object."
        )

    return data


# ============================================================
# INPUT SELECTION
# ============================================================

def select_input():

    if PRIMARY_INPUT.exists():

        return PRIMARY_INPUT

    if FALLBACK_INPUT.exists():

        return FALLBACK_INPUT

    raise FileNotFoundError(
        "Neither day22_graph_data.json "
        "nor graph_data.json exists."
    )


# ============================================================
# SAFE CONVERSIONS
# ============================================================

def safe_int(
    value,
    default=0
):

    try:

        return int(value)

    except (
        TypeError,
        ValueError
    ):

        return default


def safe_float(
    value,
    default=0.0
):

    try:

        return float(value)

    except (
        TypeError,
        ValueError
    ):

        return default


# ============================================================
# FRIENDLY STRATEGY NAME
# ============================================================

def friendly_name(name):

    normalized = str(
        name
    ).strip().lower()


    names = {

        "manual_directed":
            "Manual Directed",

        "manual":
            "Manual Directed",

        "random":
            "Random",

        "feedback_driven":
            "Feedback Driven",

        "ai":
            "Feedback Driven",

        "ai_feedback":
            "Feedback Driven",

        "proposed":
            "Feedback Driven",
    }


    return names.get(
        normalized,
        str(name).replace(
            "_",
            " "
        ).title()
    )


# ============================================================
# EXTRACT STRATEGY DATA
# ============================================================

def extract_strategy_data(data):

    # --------------------------------------------------------
    # CURRENT DAY-22 SCHEMA
    # --------------------------------------------------------

    strategies = data.get(
        "day20_strategy_comparison"
    )


    # --------------------------------------------------------
    # OLD SCHEMA FALLBACK
    # --------------------------------------------------------

    if strategies is None:

        strategies = data.get(
            "strategy_comparison"
        )


    # --------------------------------------------------------
    # GRAPH SPEC FALLBACK
    #
    # day22_data_builder.py creates:
    #
    # graph_02_tests_vs_coverage
    # --------------------------------------------------------

    if strategies is None:

        graph_specs = data.get(
            "graph_specs",
            {}
        )

        if isinstance(
            graph_specs,
            dict
        ):

            graph2 = graph_specs.get(
                "graph_02_tests_vs_coverage",
                {}
            )

            points = graph2.get(
                "points",
                []
            )

            if isinstance(
                points,
                list
            ) and points:

                generated = []

                for point in points:

                    if not isinstance(
                        point,
                        dict
                    ):

                        continue


                    generated.append(
                        {
                            "strategy":
                                point.get(
                                    "strategy",
                                    "unknown"
                                ),

                            "stimulus_cycles":
                                safe_int(
                                    point.get(
                                        "stimulus_cycles",
                                        0
                                    )
                                ),

                            "coverage_percent":
                                safe_float(
                                    point.get(
                                        "coverage_percent",
                                        0.0
                                    )
                                ),

                            "unique_behavior_signatures":
                                0,

                            "redundant_cycles":
                                0,

                            "redundancy_percent":
                                0.0,
                        }
                    )


                if generated:

                    return generated


    if not isinstance(
        strategies,
        list
    ):

        raise ValueError(
            "Verification strategy data not found. "
            "Expected 'day20_strategy_comparison'."
        )


    if not strategies:

        raise ValueError(
            "Strategy comparison data is empty."
        )


    normalized = []


    for strategy in strategies:

        if not isinstance(
            strategy,
            dict
        ):

            continue


        strategy_name = strategy.get(
            "strategy"
        )


        if strategy_name is None:

            continue


        stimulus_cycles = safe_int(
            strategy.get(
                "stimulus_cycles",
                strategy.get(
                    "transactions",
                    0
                )
            )
        )


        coverage_percent = safe_float(
            strategy.get(
                "coverage_percent",
                0.0
            )
        )


        unique_signatures = safe_int(
            strategy.get(
                "unique_behavior_signatures",
                0
            )
        )


        redundant_cycles = safe_int(
            strategy.get(
                "redundant_cycles",
                0
            )
        )


        redundancy_percent = safe_float(
            strategy.get(
                "redundancy_percent",
                0.0
            )
        )


        coverage_efficiency = safe_float(
            strategy.get(
                "coverage_percent_per_stimulus_cycle",
                (
                    coverage_percent
                    / stimulus_cycles
                    if stimulus_cycles > 0
                    else 0.0
                )
            )
        )


        normalized.append(
            {
                "strategy":
                    strategy_name,

                "stimulus_cycles":
                    stimulus_cycles,

                "coverage_percent":
                    coverage_percent,

                "unique_behavior_signatures":
                    unique_signatures,

                "redundant_cycles":
                    redundant_cycles,

                "redundancy_percent":
                    redundancy_percent,

                "coverage_efficiency":
                    coverage_efficiency,
            }
        )


    if not normalized:

        raise ValueError(
            "No usable strategy records were found."
        )


    return normalized


# ============================================================
# VALIDATE STRATEGY DATA
# ============================================================

def validate_strategy_data(strategies):

    for row in strategies:

        name = row[
            "strategy"
        ]


        cycles = row[
            "stimulus_cycles"
        ]


        coverage = row[
            "coverage_percent"
        ]


        if cycles <= 0:

            raise ValueError(
                f"Strategy {name!r} has invalid "
                f"stimulus_cycles={cycles}."
            )


        if not (
            0.0
            <= coverage
            <= 100.0
        ):

            raise ValueError(
                f"Strategy {name!r} has invalid "
                f"coverage_percent={coverage}."
            )


# ============================================================
# GENERATE GRAPH
# ============================================================

def generate_graph(strategies):

    stimulus_cycles = [
        row[
            "stimulus_cycles"
        ]
        for row in strategies
    ]


    coverage_values = [
        row[
            "coverage_percent"
        ]
        for row in strategies
    ]


    labels = [
        friendly_name(
            row[
                "strategy"
            ]
        )
        for row in strategies
    ]


    # --------------------------------------------------------
    # Figure
    # --------------------------------------------------------

    fig, ax = plt.subplots(
        figsize=(
            10,
            6
        )
    )


    # --------------------------------------------------------
    # Scatter points
    # --------------------------------------------------------

    ax.scatter(
        stimulus_cycles,
        coverage_values,
        s=140
    )


    # --------------------------------------------------------
    # Strategy labels
    # --------------------------------------------------------

    for x_value, y_value, label in zip(
        stimulus_cycles,
        coverage_values,
        labels
    ):

        ax.annotate(
            label,
            (
                x_value,
                y_value
            ),
            xytext=(
                7,
                8
            ),
            textcoords="offset points",
            fontsize=10
        )


    # --------------------------------------------------------
    # Title
    # --------------------------------------------------------

    ax.set_title(
        "FIFO Verification Effort vs Functional Coverage",
        fontsize=15,
        pad=15
    )


    # --------------------------------------------------------
    # Axis labels
    # --------------------------------------------------------

    ax.set_xlabel(
        "Stimulus Cycles",
        fontsize=12
    )


    ax.set_ylabel(
        "Functional Coverage (%)",
        fontsize=12
    )


    # --------------------------------------------------------
    # Axis limits
    # --------------------------------------------------------

    maximum_cycles = max(
        stimulus_cycles
    )


    ax.set_xlim(
        0,
        maximum_cycles
        + max(
            5,
            int(
                maximum_cycles
                * 0.15
            )
        )
    )


    ax.set_ylim(
        0,
        105
    )


    # --------------------------------------------------------
    # Grid
    # --------------------------------------------------------

    ax.grid(
        linestyle="--",
        alpha=0.35
    )


    # --------------------------------------------------------
    # Additional detail text
    # --------------------------------------------------------

    detail_lines = []


    for row in strategies:

        detail_lines.append(
            (
                f"{friendly_name(row['strategy'])}: "
                f"{row['stimulus_cycles']} cycles, "
                f"{row['coverage_percent']:.1f}% coverage, "
                f"{row['redundancy_percent']:.1f}% redundancy"
            )
        )


    detail_text = "\n".join(
        detail_lines
    )


    fig.text(
        0.5,
        0.01,
        detail_text,
        ha="center",
        fontsize=8
    )


    fig.tight_layout(
        rect=(
            0,
            0.10,
            1,
            1
        )
    )


    # --------------------------------------------------------
    # Output paths
    # --------------------------------------------------------

    GRAPH_OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True
    )


    RESULT_OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True
    )


    # --------------------------------------------------------
    # Save graph
    # --------------------------------------------------------

    fig.savefig(
        GRAPH_OUTPUT,
        dpi=300,
        bbox_inches="tight"
    )


    plt.close(
        fig
    )


    # --------------------------------------------------------
    # Result copy
    # --------------------------------------------------------

    shutil.copy2(
        GRAPH_OUTPUT,
        RESULT_OUTPUT
    )


# ============================================================
# MAIN
# ============================================================

def main():

    try:

        input_file = (
            select_input()
        )


        data = load_json(
            input_file
        )


        strategies = (
            extract_strategy_data(
                data
            )
        )


        validate_strategy_data(
            strategies
        )


        generate_graph(
            strategies
        )


        # ====================================================
        # PRINT RESULTS
        # ====================================================

        print(
            "=" * 72
        )


        print(
            "DAY 22 - GRAPH 4"
        )


        print(
            "=" * 72
        )


        print(
            "Graph                       : Verification Effort vs Coverage"
        )


        print(
            "Source                      :",
            input_file.relative_to(
                ROOT
            )
        )


        print(
            "Strategies                  :",
            len(
                strategies
            )
        )


        print(
            "-" * 72
        )


        for row in strategies:

            print(
                f"{friendly_name(row['strategy']):28s}: "
                f"cycles={row['stimulus_cycles']:3d}, "
                f"coverage={row['coverage_percent']:6.2f}%, "
                f"unique={row['unique_behavior_signatures']:2d}, "
                f"redundancy={row['redundancy_percent']:6.2f}%"
            )


        print(
            "-" * 72
        )


        print(
            "Graph output                :",
            GRAPH_OUTPUT.relative_to(
                ROOT
            )
        )


        print(
            "Result copy                 :",
            RESULT_OUTPUT.relative_to(
                ROOT
            )
        )


        print(
            "GRAPH 4 STATUS              : PASS"
        )


        print(
            "=" * 72
        )


        print(
            "GRAPH 4 GENERATION: PASS"
        )


        return 0


    except (
        FileNotFoundError,
        ValueError,
        KeyError,
        TypeError,
        OSError
    ) as exc:

        print(
            "GRAPH 4 GENERATION: FAIL"
        )

        print(
            f"ERROR: {exc}"
        )

        return 1


# ============================================================
# ENTRY
# ============================================================

if __name__ == "__main__":

    sys.exit(
        main()
    )
