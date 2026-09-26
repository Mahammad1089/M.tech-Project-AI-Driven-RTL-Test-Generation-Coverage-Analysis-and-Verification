#!/usr/bin/env python3

"""
Day 22 - Graph 3
================

FIFO Coverage Distribution Across Day-21 Random-Seed Experiments

Project:
AI-Driven RTL Test Generation,
Coverage Analysis and Verification

Primary input:
    results/fifo/day22/day22_graph_data.json

Fallback input:
    results/fifo/day22/graph_data.json

Current schema:
    coverage_distribution
    day21_runs

Old schema fallback:
    random_runs

Outputs:
    graphs/day22_graph3_coverage_distribution.png
    results/fifo/day22/graph3_coverage_distribution.png
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
    / "day22_graph3_coverage_distribution.png"
)

RESULT_OUTPUT = (
    DAY22_DIR
    / "graph3_coverage_distribution.png"
)


# ============================================================
# LOAD JSON
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
            "Day 22 graph data must be a JSON object."
        )

    return data


# ============================================================
# SELECT INPUT
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
# BUILD DISTRIBUTION FROM RUNS
# ============================================================

def distribution_from_runs(runs):

    if not isinstance(
        runs,
        list
    ):

        raise ValueError(
            "Run data must be a list."
        )

    if not runs:

        raise ValueError(
            "Run data is empty."
        )


    counts = {}


    for index, run in enumerate(
        runs,
        start=1
    ):

        if not isinstance(
            run,
            dict
        ):

            continue


        coverage = safe_float(
            run.get(
                "coverage_percent",
                0.0
            )
        )


        if not (
            0.0
            <= coverage
            <= 100.0
        ):

            raise ValueError(
                f"Run {index} has invalid "
                f"coverage value {coverage}%."
            )


        coverage = round(
            coverage,
            2
        )


        counts[
            coverage
        ] = (
            counts.get(
                coverage,
                0
            )
            + 1
        )


    rows = []


    for coverage in sorted(
        counts.keys()
    ):

        rows.append(
            {
                "coverage_percent":
                    coverage,

                "run_count":
                    counts[
                        coverage
                    ],
            }
        )


    return rows


# ============================================================
# EXTRACT COVERAGE DISTRIBUTION
# ============================================================

def extract_distribution(data):

    # --------------------------------------------------------
    # BEST / CURRENT SOURCE
    #
    # day22_data_builder.py already generated:
    #
    # coverage_distribution
    # --------------------------------------------------------

    distribution = data.get(
        "coverage_distribution"
    )


    if isinstance(
        distribution,
        list
    ) and distribution:

        normalized = []


        for row in distribution:

            if not isinstance(
                row,
                dict
            ):

                continue


            coverage = safe_float(
                row.get(
                    "coverage_percent",
                    0.0
                )
            )


            run_count = safe_int(
                row.get(
                    "run_count",
                    0
                )
            )


            if not (
                0.0
                <= coverage
                <= 100.0
            ):

                raise ValueError(
                    f"Invalid coverage percentage "
                    f"in distribution: {coverage}%."
                )


            if run_count < 0:

                raise ValueError(
                    "Run count cannot be negative."
                )


            normalized.append(
                {
                    "coverage_percent":
                        round(
                            coverage,
                            2
                        ),

                    "run_count":
                        run_count,
                }
            )


        if normalized:

            normalized.sort(
                key=lambda row:
                    row[
                        "coverage_percent"
                    ]
            )

            return normalized


    # --------------------------------------------------------
    # CURRENT RUN SCHEMA FALLBACK
    # --------------------------------------------------------

    runs = data.get(
        "day21_runs"
    )


    # --------------------------------------------------------
    # OLD SCHEMA FALLBACK
    # --------------------------------------------------------

    if runs is None:

        runs = data.get(
            "random_runs"
        )


    if runs is None:

        raise ValueError(
            "Coverage distribution could not be found. "
            "Expected 'coverage_distribution' or "
            "'day21_runs'."
        )


    return distribution_from_runs(
        runs
    )


# ============================================================
# EXTRACT RUN COUNT
# ============================================================

def get_total_runs(
    data,
    distribution
):

    # --------------------------------------------------------
    # Prefer current Day-21 run list.
    # --------------------------------------------------------

    runs = data.get(
        "day21_runs"
    )


    if isinstance(
        runs,
        list
    ) and runs:

        return len(
            runs
        )


    # --------------------------------------------------------
    # Old fallback.
    # --------------------------------------------------------

    runs = data.get(
        "random_runs"
    )


    if isinstance(
        runs,
        list
    ) and runs:

        return len(
            runs
        )


    # --------------------------------------------------------
    # Derive from distribution.
    # --------------------------------------------------------

    return sum(
        row[
            "run_count"
        ]
        for row in distribution
    )


# ============================================================
# CALCULATE SUMMARY
# ============================================================

def calculate_summary(
    distribution
):

    total_runs = sum(
        row[
            "run_count"
        ]
        for row in distribution
    )


    if total_runs <= 0:

        raise ValueError(
            "Coverage distribution contains zero runs."
        )


    weighted_total = sum(
        row[
            "coverage_percent"
        ]
        * row[
            "run_count"
        ]
        for row in distribution
    )


    average_coverage = (
        weighted_total
        / total_runs
    )


    minimum_coverage = min(
        row[
            "coverage_percent"
        ]
        for row in distribution
        if row[
            "run_count"
        ] > 0
    )


    maximum_coverage = max(
        row[
            "coverage_percent"
        ]
        for row in distribution
        if row[
            "run_count"
        ] > 0
    )


    runs_at_100 = sum(
        row[
            "run_count"
        ]
        for row in distribution
        if abs(
            row[
                "coverage_percent"
            ]
            - 100.0
        )
        < 0.0001
    )


    return {
        "total_runs":
            total_runs,

        "average_coverage":
            round(
                average_coverage,
                2
            ),

        "minimum_coverage":
            round(
                minimum_coverage,
                2
            ),

        "maximum_coverage":
            round(
                maximum_coverage,
                2
            ),

        "runs_at_100":
            runs_at_100,
    }


# ============================================================
# GENERATE GRAPH
# ============================================================

def generate_graph(
    distribution,
    summary
):

    coverage_values = [
        row[
            "coverage_percent"
        ]
        for row in distribution
    ]


    run_counts = [
        row[
            "run_count"
        ]
        for row in distribution
    ]


    labels = [
        (
            f"{coverage:.0f}%"
            if float(
                coverage
            ).is_integer()
            else f"{coverage:.2f}%"
        )

        for coverage
        in coverage_values
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


    bars = ax.bar(
        labels,
        run_counts,
        width=0.60
    )


    # --------------------------------------------------------
    # Title / axis labels
    # --------------------------------------------------------

    ax.set_title(
        "Distribution of FIFO Functional Coverage Across Random Seeds",
        fontsize=15,
        pad=15
    )


    ax.set_xlabel(
        "Functional Coverage",
        fontsize=12
    )


    ax.set_ylabel(
        "Number of Experiment Runs",
        fontsize=12
    )


    # --------------------------------------------------------
    # Integer Y-axis
    # --------------------------------------------------------

    maximum_count = max(
        run_counts
    )


    ax.set_ylim(
        0,
        maximum_count
        + 1.5
    )


    ax.set_yticks(
        range(
            0,
            maximum_count
            + 2
        )
    )


    # --------------------------------------------------------
    # Grid
    # --------------------------------------------------------

    ax.grid(
        axis="y",
        linestyle="--",
        alpha=0.35
    )


    # --------------------------------------------------------
    # Value labels
    # --------------------------------------------------------

    for bar, count in zip(
        bars,
        run_counts
    ):

        ax.text(
            bar.get_x()
            + bar.get_width()
            / 2.0,

            bar.get_height()
            + 0.08,

            str(
                count
            ),

            ha="center",
            va="bottom",
            fontsize=11
        )


    # --------------------------------------------------------
    # Summary footer
    # --------------------------------------------------------

    fig.text(
        0.5,
        0.01,
        (
            f"{summary['total_runs']} deterministic random-seed runs | "
            f"Mean coverage={summary['average_coverage']:.1f}% | "
            f"Range={summary['minimum_coverage']:.1f}%"
            f"–{summary['maximum_coverage']:.1f}%"
        ),
        ha="center",
        fontsize=9
    )


    fig.tight_layout(
        rect=(
            0,
            0.04,
            1,
            1
        )
    )


    # --------------------------------------------------------
    # Output directories
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
    # Save report-quality graph
    # --------------------------------------------------------

    fig.savefig(
        GRAPH_OUTPUT,
        dpi=300,
        bbox_inches="tight"
    )


    plt.close(
        fig
    )


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


        distribution = (
            extract_distribution(
                data
            )
        )


        summary = (
            calculate_summary(
                distribution
            )
        )


        expected_total_runs = (
            get_total_runs(
                data,
                distribution
            )
        )


        if (
            summary[
                "total_runs"
            ]
            != expected_total_runs
        ):

            raise ValueError(
                "Coverage-distribution run count mismatch: "
                f"distribution={summary['total_runs']}, "
                f"run records={expected_total_runs}."
            )


        generate_graph(
            distribution,
            summary
        )


        # ====================================================
        # PRINT RESULTS
        # ====================================================

        print(
            "=" * 72
        )


        print(
            "DAY 22 - GRAPH 3"
        )


        print(
            "=" * 72
        )


        print(
            "Graph                       : Coverage Distribution"
        )


        print(
            "Source                      :",
            input_file.relative_to(
                ROOT
            )
        )


        print(
            "Experiment runs             :",
            summary[
                "total_runs"
            ]
        )


        print(
            "Coverage levels             :",
            len(
                distribution
            )
        )


        print(
            "Average coverage            :",
            f"{summary['average_coverage']:.2f}%"
        )


        print(
            "Minimum coverage            :",
            f"{summary['minimum_coverage']:.2f}%"
        )


        print(
            "Maximum coverage            :",
            f"{summary['maximum_coverage']:.2f}%"
        )


        print(
            "Runs at 100% coverage       :",
            summary[
                "runs_at_100"
            ]
        )


        print(
            "-" * 72
        )


        print(
            "Coverage distribution:"
        )


        for row in distribution:

            print(
                f"  {row['coverage_percent']:6.2f}% "
                f": {row['run_count']} run(s)"
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
            "GRAPH 3 STATUS              : PASS"
        )


        print(
            "=" * 72
        )


        print(
            "GRAPH 3 GENERATION: PASS"
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
            "GRAPH 3 GENERATION: FAIL"
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
