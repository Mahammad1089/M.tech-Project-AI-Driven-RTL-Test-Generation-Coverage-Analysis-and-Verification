#!/usr/bin/env python3

"""
Day 22 - Graph 5
================

FIFO Random-Seed Redundancy Across Day-21 Experiments

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

Preferred graph specification:
    graph_specs["graph_05_day21_seed_redundancy"]

Outputs:
    graphs/day22_graph5_random_redundancy.png
    results/fifo/day22/graph5_random_redundancy.png
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
    / "day22_graph5_random_redundancy.png"
)

RESULT_OUTPUT = (
    DAY22_DIR
    / "graph5_random_redundancy.png"
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
            "Day 22 graph data must contain a JSON object."
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
# EXTRACT FROM GRAPH SPEC
# ============================================================

def extract_from_graph_spec(data):

    graph_specs = data.get(
        "graph_specs",
        {}
    )


    if not isinstance(
        graph_specs,
        dict
    ):

        return None


    spec = graph_specs.get(
        "graph_05_day21_seed_redundancy"
    )


    if not isinstance(
        spec,
        dict
    ):

        return None


    x_values = spec.get(
        "x",
        []
    )

    y_values = spec.get(
        "y",
        []
    )


    if not (
        isinstance(
            x_values,
            list
        )
        and isinstance(
            y_values,
            list
        )
    ):

        return None


    if (
        len(
            x_values
        )
        == 0
        or len(
            x_values
        )
        != len(
            y_values
        )
    ):

        return None


    rows = []


    for index, (
        run_value,
        redundancy_value
    ) in enumerate(
        zip(
            x_values,
            y_values
        ),
        start=1
    ):

        rows.append(
            {
                "run":
                    safe_int(
                        run_value,
                        index
                    ),

                "seed":
                    0,

                "redundant_cycles":
                    0,

                "redundancy_percent":
                    safe_float(
                        redundancy_value
                    ),

                "status":
                    "MEASURED",

                "failed_checks":
                    0,
            }
        )


    return rows


# ============================================================
# EXTRACT RUN DATA
# ============================================================

def extract_runs(data):

    # --------------------------------------------------------
    # Preferred source:
    # graph_05_day21_seed_redundancy
    # --------------------------------------------------------

    graph_spec_rows = (
        extract_from_graph_spec(
            data
        )
    )


    # --------------------------------------------------------
    # We prefer the full run records where available because
    # they include seed and redundant-cycle information.
    # --------------------------------------------------------

    runs = data.get(
        "day21_runs"
    )


    # --------------------------------------------------------
    # Old schema fallback
    # --------------------------------------------------------

    if runs is None:

        runs = data.get(
            "random_runs"
        )


    if isinstance(
        runs,
        list
    ) and runs:

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


            redundant_cycles = safe_int(
                run.get(
                    "redundant_cycles",
                    0
                )
            )


            redundancy_percent = safe_float(
                run.get(
                    "redundancy_percent",
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

                    "redundant_cycles":
                        redundant_cycles,

                    "redundancy_percent":
                        redundancy_percent,

                    "status":
                        status,

                    "failed_checks":
                        failed_checks,
                }
            )


        if normalized:

            normalized.sort(
                key=lambda row:
                    row[
                        "run"
                    ]
            )

            return normalized


    # --------------------------------------------------------
    # Fall back to graph-spec data.
    # --------------------------------------------------------

    if graph_spec_rows:

        return graph_spec_rows


    raise ValueError(
        "Random redundancy data not found. "
        "Expected 'day21_runs' or "
        "'graph_05_day21_seed_redundancy'."
    )


# ============================================================
# VALIDATE RUNS
# ============================================================

def validate_runs(runs):

    if not runs:

        raise ValueError(
            "No random-seed redundancy records found."
        )


    for run in runs:

        redundancy = run[
            "redundancy_percent"
        ]


        if not (
            0.0
            <= redundancy
            <= 100.0
        ):

            raise ValueError(
                f"Run {run['run']} has invalid "
                f"redundancy_percent={redundancy}."
            )


        if (
            run[
                "failed_checks"
            ]
            != 0
        ):

            raise ValueError(
                f"Run {run['run']} has "
                f"{run['failed_checks']} failed checks."
            )


        status = run[
            "status"
        ]


        if status not in (
            "PASS",
            "MEASURED",
            "UNKNOWN"
        ):

            raise ValueError(
                f"Run {run['run']} has "
                f"status={status!r}."
            )


# ============================================================
# SUMMARY
# ============================================================

def calculate_summary(runs):

    values = [
        run[
            "redundancy_percent"
        ]
        for run in runs
    ]


    average = (
        sum(
            values
        )
        / len(
            values
        )
    )


    minimum = min(
        values
    )


    maximum = max(
        values
    )


    redundant_cycle_values = [
        run[
            "redundant_cycles"
        ]
        for run in runs
    ]


    average_redundant_cycles = (
        sum(
            redundant_cycle_values
        )
        / len(
            redundant_cycle_values
        )
    )


    return {
        "average":
            round(
                average,
                2
            ),

        "minimum":
            round(
                minimum,
                2
            ),

        "maximum":
            round(
                maximum,
                2
            ),

        "average_redundant_cycles":
            round(
                average_redundant_cycles,
                2
            ),
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


    redundancy_values = [
        run[
            "redundancy_percent"
        ]
        for run in runs
    ]


    # --------------------------------------------------------
    # Create figure
    # --------------------------------------------------------

    fig, ax = plt.subplots(
        figsize=(
            11,
            6
        )
    )


    # --------------------------------------------------------
    # Plot measured redundancy
    # --------------------------------------------------------

    ax.plot(
        run_numbers,
        redundancy_values,
        marker="o",
        linewidth=2
    )


    # --------------------------------------------------------
    # Average reference line
    # --------------------------------------------------------

    ax.axhline(
        y=summary[
            "average"
        ],
        linestyle="--",
        linewidth=1.5,
        label=(
            "Average redundancy "
            f"({summary['average']:.1f}%)"
        )
    )


    # --------------------------------------------------------
    # Title / labels
    # --------------------------------------------------------

    ax.set_title(
        "Day 21 FIFO Random-Test Redundancy Across Seeds",
        fontsize=15,
        pad=15
    )


    ax.set_xlabel(
        "Multi-Seed Experiment Run",
        fontsize=12
    )


    ax.set_ylabel(
        "Redundancy (%)",
        fontsize=12
    )


    ax.set_xticks(
        run_numbers
    )


    ax.set_ylim(
        0,
        105
    )


    ax.grid(
        linestyle="--",
        alpha=0.35
    )


    # --------------------------------------------------------
    # Value labels
    # --------------------------------------------------------

    for run_number, redundancy in zip(
        run_numbers,
        redundancy_values
    ):

        ax.text(
            run_number,
            redundancy + 1.5,
            f"{redundancy:.1f}%",
            ha="center",
            va="bottom",
            fontsize=9
        )


    ax.legend(
        loc="best"
    )


    # --------------------------------------------------------
    # Footer
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
    # Save
    # --------------------------------------------------------

    GRAPH_OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True
    )


    RESULT_OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True
    )


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
            "DAY 22 - GRAPH 5"
        )

        print(
            "=" * 72
        )

        print(
            "Graph                       : Random-Test Redundancy"
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
            "Average redundancy          :",
            f"{summary['average']:.2f}%"
        )

        print(
            "Minimum redundancy          :",
            f"{summary['minimum']:.2f}%"
        )

        print(
            "Maximum redundancy          :",
            f"{summary['maximum']:.2f}%"
        )

        print(
            "Average redundant cycles    :",
            f"{summary['average_redundant_cycles']:.2f}"
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
                ] != 0

                else "N/A"
            )


            print(
                f"Run {run['run']:02d} | "
                f"Seed {seed_text:>8s} | "
                f"Redundant cycles "
                f"{run['redundant_cycles']:2d} | "
                f"Redundancy "
                f"{run['redundancy_percent']:6.2f}%"
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
            "GRAPH 5 STATUS              : PASS"
        )

        print(
            "=" * 72
        )

        print(
            "GRAPH 5 GENERATION: PASS"
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
            "GRAPH 5 GENERATION: FAIL"
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
