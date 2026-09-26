#!/usr/bin/env python3

"""
Day 22 - Graph 6
================

Day 20 Random Baseline vs Day 21 Multi-Seed Random Coverage Range

Project:
AI-Driven RTL Test Generation,
Coverage Analysis and Verification

Purpose
-------
Visualize:

1. Day 20 single random-baseline functional coverage.
2. Day 21 mean random coverage across multiple seeds.
3. Day 21 measured minimum-to-maximum coverage range.

Primary input:
    results/fifo/day22/day22_graph_data.json

Fallback:
    results/fifo/day22/graph_data.json

Current schema:
    day20_strategy_comparison
    day21_multi_seed_summary

Also supported:
    graph_specs["graph_06_day20_vs_day21_random"]

Outputs:
    graphs/day22_graph6_random_range.png
    results/fifo/day22/graph6_random_range.png
"""

import json
import shutil
import sys
from pathlib import Path

import matplotlib.pyplot as plt


# ============================================================
# PATHS
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
    / "day22_graph6_random_range.png"
)

RESULT_OUTPUT = (
    DAY22_DIR
    / "graph6_random_range.png"
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
# SAFE FLOAT
# ============================================================

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
# FIND DAY 20 RANDOM REFERENCE
# ============================================================

def extract_day20_random(data):

    strategies = data.get(
        "day20_strategy_comparison"
    )


    # Old-schema fallback
    if strategies is None:

        strategies = data.get(
            "strategy_comparison"
        )


    if isinstance(
        strategies,
        list
    ):

        for row in strategies:

            if not isinstance(
                row,
                dict
            ):

                continue


            strategy_name = str(
                row.get(
                    "strategy",
                    ""
                )
            ).strip().lower()


            if strategy_name == "random":

                return safe_float(
                    row.get(
                        "coverage_percent",
                        0.0
                    )
                )


    # ========================================================
    # GRAPH-SPEC FALLBACK
    # ========================================================

    graph_specs = data.get(
        "graph_specs",
        {}
    )


    if isinstance(
        graph_specs,
        dict
    ):

        spec = graph_specs.get(
            "graph_06_day20_vs_day21_random",
            {}
        )


        if isinstance(
            spec,
            dict
        ):

            x_values = spec.get(
                "x",
                []
            )

            y_values = spec.get(
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
            ):

                for label, value in zip(
                    x_values,
                    y_values
                ):

                    if (
                        str(
                            label
                        ).strip().lower()
                        == "day20 random"
                    ):

                        return safe_float(
                            value
                        )


    raise ValueError(
        "Day 20 random coverage could not be found."
    )


# ============================================================
# DAY 21 MULTI-SEED SUMMARY
# ============================================================

def extract_day21_summary(data):

    # --------------------------------------------------------
    # CURRENT SCHEMA
    # --------------------------------------------------------

    summary = data.get(
        "day21_multi_seed_summary"
    )


    if isinstance(
        summary,
        dict
    ):

        average = safe_float(
            summary.get(
                "average_coverage_percent",
                0.0
            )
        )

        minimum = safe_float(
            summary.get(
                "minimum_coverage_percent",
                average
            )
        )

        maximum = safe_float(
            summary.get(
                "maximum_coverage_percent",
                average
            )
        )


        return {
            "average":
                average,

            "minimum":
                minimum,

            "maximum":
                maximum,
        }


    # ========================================================
    # GRAPH-SPEC FALLBACK
    # ========================================================

    graph_specs = data.get(
        "graph_specs",
        {}
    )


    if isinstance(
        graph_specs,
        dict
    ):

        spec = graph_specs.get(
            "graph_06_day20_vs_day21_random",
            {}
        )


        if isinstance(
            spec,
            dict
        ):

            x_values = spec.get(
                "x",
                []
            )

            y_values = spec.get(
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
            ):

                values = {}


                for label, value in zip(
                    x_values,
                    y_values
                ):

                    normalized = str(
                        label
                    ).strip().lower()


                    if (
                        "day21"
                        in normalized
                        and "mean"
                        in normalized
                    ):

                        values[
                            "average"
                        ] = safe_float(
                            value
                        )


                    elif (
                        "day21"
                        in normalized
                        and "min"
                        in normalized
                    ):

                        values[
                            "minimum"
                        ] = safe_float(
                            value
                        )


                    elif (
                        "day21"
                        in normalized
                        and "max"
                        in normalized
                    ):

                        values[
                            "maximum"
                        ] = safe_float(
                            value
                        )


                if all(
                    key in values
                    for key in (
                        "average",
                        "minimum",
                        "maximum"
                    )
                ):

                    return values


    # ========================================================
    # RUN DATA FALLBACK
    # ========================================================

    runs = data.get(
        "day21_runs"
    )


    if isinstance(
        runs,
        list
    ) and runs:

        coverage_values = []


        for run in runs:

            if not isinstance(
                run,
                dict
            ):

                continue


            coverage_values.append(
                safe_float(
                    run.get(
                        "coverage_percent",
                        0.0
                    )
                )
            )


        if coverage_values:

            return {
                "average":
                    round(
                        sum(
                            coverage_values
                        )
                        / len(
                            coverage_values
                        ),
                        2
                    ),

                "minimum":
                    min(
                        coverage_values
                    ),

                "maximum":
                    max(
                        coverage_values
                    ),
            }


    raise ValueError(
        "Day 21 multi-seed coverage summary could not be found."
    )


# ============================================================
# VALIDATE VALUES
# ============================================================

def validate_values(
    day20_random,
    day21
):

    values = [
        day20_random,
        day21[
            "average"
        ],
        day21[
            "minimum"
        ],
        day21[
            "maximum"
        ],
    ]


    for value in values:

        if not (
            0.0
            <= value
            <= 100.0
        ):

            raise ValueError(
                f"Invalid coverage value: {value}%"
            )


    if (
        day21[
            "minimum"
        ]
        > day21[
            "average"
        ]
    ):

        raise ValueError(
            "Day 21 minimum coverage is greater "
            "than average coverage."
        )


    if (
        day21[
            "average"
        ]
        > day21[
            "maximum"
        ]
    ):

        raise ValueError(
            "Day 21 average coverage is greater "
            "than maximum coverage."
        )


# ============================================================
# GENERATE GRAPH
# ============================================================

def generate_graph(
    day20_random,
    day21
):

    # --------------------------------------------------------
    # Data
    # --------------------------------------------------------

    x_positions = [
        0,
        1
    ]


    means = [
        day20_random,
        day21[
            "average"
        ]
    ]


    # Day 20 is a single recorded run, so its displayed
    # min/max range is zero.
    lower_errors = [
        0.0,
        day21[
            "average"
        ]
        - day21[
            "minimum"
        ]
    ]


    upper_errors = [
        0.0,
        day21[
            "maximum"
        ]
        - day21[
            "average"
        ]
    ]


    # --------------------------------------------------------
    # Create figure
    # --------------------------------------------------------

    fig, ax = plt.subplots(
        figsize=(
            9,
            6
        )
    )


    bars = ax.bar(
        x_positions,
        means,
        width=0.55
    )


    # --------------------------------------------------------
    # Day 21 error/range bar
    # --------------------------------------------------------

    ax.errorbar(
        x_positions,
        means,
        yerr=[
            lower_errors,
            upper_errors
        ],
        fmt="none",
        capsize=8,
        linewidth=2
    )


    # --------------------------------------------------------
    # X labels
    # --------------------------------------------------------

    ax.set_xticks(
        x_positions
    )


    ax.set_xticklabels(
        [
            "Day 20\nSingle Random Run",
            "Day 21\n10-Seed Mean"
        ]
    )


    # --------------------------------------------------------
    # Titles
    # --------------------------------------------------------

    ax.set_title(
        "FIFO Random Verification Coverage: Single Run vs Multi-Seed Range",
        fontsize=14,
        pad=15
    )


    ax.set_ylabel(
        "Functional Coverage (%)",
        fontsize=12
    )


    ax.set_xlabel(
        "Random Verification Measurement",
        fontsize=12
    )


    # --------------------------------------------------------
    # Y scale
    # --------------------------------------------------------

    ax.set_ylim(
        0,
        108
    )


    ax.grid(
        axis="y",
        linestyle="--",
        alpha=0.35
    )


    # --------------------------------------------------------
    # Value labels
    # --------------------------------------------------------

    for bar, value in zip(
        bars,
        means
    ):

        ax.text(
            bar.get_x()
            + bar.get_width()
            / 2.0,

            value + 1.5,

            f"{value:.1f}%",

            ha="center",
            va="bottom",
            fontsize=11
        )


    # --------------------------------------------------------
    # Day 21 range annotation
    # --------------------------------------------------------

    ax.text(
        1,
        day21[
            "minimum"
        ]
        - 4,

        (
            f"Range: "
            f"{day21['minimum']:.0f}%"
            f"–{day21['maximum']:.0f}%"
        ),

        ha="center",
        fontsize=10
    )


    # --------------------------------------------------------
    # Footer
    # --------------------------------------------------------

    fig.text(
        0.5,
        0.01,
        (
            "Day 20 is one recorded 40-cycle random baseline; "
            "Day 21 summarizes 10 independent 20-transaction seeded runs."
        ),
        ha="center",
        fontsize=8.5
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


        day20_random = (
            extract_day20_random(
                data
            )
        )


        day21 = (
            extract_day21_summary(
                data
            )
        )


        validate_values(
            day20_random,
            day21
        )


        generate_graph(
            day20_random,
            day21
        )


        print(
            "=" * 72
        )

        print(
            "DAY 22 - GRAPH 6"
        )

        print(
            "=" * 72
        )


        print(
            "Graph                       : Random Coverage Range"
        )


        print(
            "Source                      :",
            input_file.relative_to(
                ROOT
            )
        )


        print(
            "-" * 72
        )


        print(
            "Day 20 random coverage      :",
            f"{day20_random:.2f}%"
        )


        print(
            "Day 21 average coverage     :",
            f"{day21['average']:.2f}%"
        )


        print(
            "Day 21 minimum coverage     :",
            f"{day21['minimum']:.2f}%"
        )


        print(
            "Day 21 maximum coverage     :",
            f"{day21['maximum']:.2f}%"
        )


        print(
            "Day 21 coverage range       :",
            (
                f"{day21['minimum']:.2f}% "
                f"to {day21['maximum']:.2f}%"
            )
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
            "GRAPH 6 STATUS              : PASS"
        )


        print(
            "=" * 72
        )


        print(
            "GRAPH 6 GENERATION: PASS"
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
            "GRAPH 6 GENERATION: FAIL"
        )

        print(
            f"ERROR: {exc}"
        )

        return 1


if __name__ == "__main__":

    sys.exit(
        main()
    )
