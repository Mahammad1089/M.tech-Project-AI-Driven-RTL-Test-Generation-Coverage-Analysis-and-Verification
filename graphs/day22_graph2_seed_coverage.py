#!/usr/bin/env python3

"""
Day 22 - Graph 2
================

FIFO Functional Coverage Across Day-21 Random Seeds

Project:
AI-Driven RTL Test Generation,
Coverage Analysis and Verification

Primary input:
    results/fifo/day22/day22_graph_data.json

Fallback:
    results/fifo/day22/graph_data.json

Current schema:
    day21_runs

Old-schema fallback:
    random_runs

Outputs:
    graphs/day22_graph2_seed_coverage.png
    results/fifo/day22/graph2_seed_coverage.png
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
    / "day22_graph2_seed_coverage.png"
)

RESULT_OUTPUT = (
    DAY22_DIR
    / "graph2_seed_coverage.png"
)


# ============================================================
# JSON LOADER
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
# EXTRACT DAY 21 RUNS
# ============================================================

def extract_runs(data):

    # --------------------------------------------------------
    # CURRENT SCHEMA
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


    # --------------------------------------------------------
    # GRAPH-SPEC FALLBACK
    #
    # day22_data_builder.py also creates:
    # graph_04_day21_seed_coverage
    # --------------------------------------------------------

    if runs is None:

        graph_specs = data.get(
            "graph_specs",
            {}
        )

        if isinstance(
            graph_specs,
            dict
        ):

            graph_spec = graph_specs.get(
                "graph_04_day21_seed_coverage",
                {}
            )

            x_values = graph_spec.get(
                "x",
                []
            )

            y_values = graph_spec.get(
                "y",
                []
            )

            if (
                isinstance(
                    x_values,
                    list
                )
                and isinstance(
                    y_values,
                    list
                )
                and len(
                    x_values
                )
                == len(
                    y_values
                )
                and len(
                    x_values
                )
                > 0
            ):

                generated_runs = []

                for index, (
                    x_value,
                    y_value
                ) in enumerate(
                    zip(
                        x_values,
                        y_values
                    ),
                    start=1
                ):

                    generated_runs.append(
                        {
                            "run":
                                safe_int(
                                    x_value,
                                    index
                                ),

                            "seed":
                                0,

                            "coverage_percent":
                                safe_float(
                                    y_value
                                ),

                            "status":
                                "MEASURED",
                        }
                    )

                return generated_runs


    if not isinstance(
        runs,
        list
    ):

        raise ValueError(
            "Random-seed run data not found. "
            "Expected field 'day21_runs'."
        )


    if not runs:

        raise ValueError(
            "Day 21 run list is empty."
        )


    normalized = []


    for index, run in enumerate(
        runs,
        start=1
    ):

        if not isinstance(
            run,
            dict
        ):

            continue


        run_number = safe_int(
            run.get(
                "run",
                run.get(
                    "run_index",
                    index
                )
            ),
            index
        )


        seed = safe_int(
            run.get(
                "seed",
                0
            )
        )


        coverage = safe_float(
            run.get(
                "coverage_percent",
                0.0
            )
        )


        status = str(
            run.get(
                "status",
                run.get(
                    "simulation_status",
                    "UNKNOWN"
                )
            )
        ).strip().upper()


        failed_checks = safe_int(
            run.get(
                "failed_checks",
                0
            )
        )


        normalized.append(
            {
                "run":
                    run_number,

                "seed":
                    seed,

                "coverage_percent":
                    coverage,

                "status":
                    status,

                "failed_checks":
                    failed_checks,
            }
        )


    if not normalized:

        raise ValueError(
            "No usable Day 21 run records were found."
        )


    normalized.sort(
        key=lambda item: item[
            "run"
        ]
    )


    return normalized


# ============================================================
# VALIDATE RUNS
# ============================================================

def validate_runs(runs):

    for run in runs:

        coverage = run[
            "coverage_percent"
        ]


        if not (
            0.0
            <= coverage
            <= 100.0
        ):

            raise ValueError(
                f"Run {run['run']} has invalid "
                f"coverage {coverage}%."
            )


        status = run[
            "status"
        ]


        # MEASURED is allowed for graph-spec fallback.
        if status not in (
            "PASS",
            "MEASURED",
            "UNKNOWN"
        ):

            raise ValueError(
                f"Run {run['run']} status is "
                f"{status}, expected PASS."
            )


        if run[
            "failed_checks"
        ] != 0:

            raise ValueError(
                f"Run {run['run']} has "
                f"{run['failed_checks']} failed checks."
            )


# ============================================================
# CALCULATE SUMMARY
# ============================================================

def calculate_summary(runs):

    coverage_values = [
        run[
            "coverage_percent"
        ]
        for run in runs
    ]


    average_coverage = (
        sum(
            coverage_values
        )
        / len(
            coverage_values
        )
    )


    minimum_coverage = min(
        coverage_values
    )


    maximum_coverage = max(
        coverage_values
    )


    runs_at_100 = sum(
        1
        for value in coverage_values
        if abs(
            value
            - 100.0
        )
        < 0.0001
    )


    return {
        "average":
            round(
                average_coverage,
                2
            ),

        "minimum":
            round(
                minimum_coverage,
                2
            ),

        "maximum":
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
    runs,
    summary
):

    run_numbers = [
        run[
            "run"
        ]
        for run in runs
    ]


    coverage_values = [
        run[
            "coverage_percent"
        ]
        for run in runs
    ]


    # --------------------------------------------------------
    # Main figure
    # --------------------------------------------------------

    fig, ax = plt.subplots(
        figsize=(
            11,
            6
        )
    )


    # --------------------------------------------------------
    # Coverage line
    # --------------------------------------------------------

    ax.plot(
        run_numbers,
        coverage_values,
        marker="o",
        linewidth=2
    )


    # --------------------------------------------------------
    # Average coverage reference line
    # --------------------------------------------------------

    ax.axhline(
        y=summary[
            "average"
        ],
        linestyle="--",
        linewidth=1.5,
        label=(
            "Average coverage "
            f"({summary['average']:.1f}%)"
        )
    )


    # --------------------------------------------------------
    # Axis labels and title
    # --------------------------------------------------------

    ax.set_title(
        "Day 21 FIFO Functional Coverage Across Random Seeds",
        fontsize=15,
        pad=15
    )


    ax.set_xlabel(
        "Multi-Seed Experiment Run",
        fontsize=12
    )


    ax.set_ylabel(
        "Functional Coverage (%)",
        fontsize=12
    )


    # --------------------------------------------------------
    # Run ticks
    # --------------------------------------------------------

    ax.set_xticks(
        run_numbers
    )


    # --------------------------------------------------------
    # Coverage range
    # --------------------------------------------------------

    ax.set_ylim(
        0,
        105
    )


    # --------------------------------------------------------
    # Grid
    # --------------------------------------------------------

    ax.grid(
        axis="both",
        linestyle="--",
        alpha=0.35
    )


    # --------------------------------------------------------
    # Value labels
    # --------------------------------------------------------

    for run_number, coverage in zip(
        run_numbers,
        coverage_values
    ):

        ax.text(
            run_number,
            coverage + 1.5,
            f"{coverage:.0f}%",
            ha="center",
            va="bottom",
            fontsize=9
        )


    # --------------------------------------------------------
    # Legend
    # --------------------------------------------------------

    ax.legend(
        loc="lower right"
    )


    # --------------------------------------------------------
    # Footer with measured summary
    # --------------------------------------------------------

    fig.text(
        0.5,
        0.01,
        (
            f"Measured across {len(runs)} deterministic random-seed runs | "
            f"Mean={summary['average']:.1f}% | "
            f"Min={summary['minimum']:.1f}% | "
            f"Max={summary['maximum']:.1f}%"
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
    # Save PNG
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
    # Create result copy
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


        runs = extract_runs(
            data
        )


        validate_runs(
            runs
        )


        summary = calculate_summary(
            runs
        )


        generate_graph(
            runs,
            summary
        )


        print(
            "=" * 72
        )

        print(
            "DAY 22 - GRAPH 2"
        )

        print(
            "=" * 72
        )


        print(
            "Graph                       : Random Seed Coverage"
        )


        print(
            "Source                      :",
            input_file.relative_to(
                ROOT
            )
        )


        print(
            "Experiment runs             :",
            len(
                runs
            )
        )


        print(
            "Average coverage            :",
            f"{summary['average']:.2f}%"
        )


        print(
            "Minimum coverage            :",
            f"{summary['minimum']:.2f}%"
        )


        print(
            "Maximum coverage            :",
            f"{summary['maximum']:.2f}%"
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


        for run in runs:

            seed_text = (
                str(
                    run[
                        "seed"
                    ]
                )
                if run[
                    "seed"
                ]
                != 0
                else "N/A"
            )


            print(
                f"Run {run['run']:02d} | "
                f"Seed {seed_text:>8s} | "
                f"Coverage {run['coverage_percent']:6.2f}%"
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
            "GRAPH 2 STATUS              : PASS"
        )


        print(
            "=" * 72
        )


        print(
            "GRAPH 2 GENERATION: PASS"
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
            "GRAPH 2 GENERATION: FAIL"
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
