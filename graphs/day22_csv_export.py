#!/usr/bin/env python3

"""
Day 22 - CSV Export
===================

Project:
AI-Driven RTL Test Generation,
Coverage Analysis and Verification

Purpose
-------
Export report-ready CSV files from the CURRENT Day-22 graph-data
JSON schema.

Primary input:
    results/fifo/day22/day22_graph_data.json

Fallback input:
    results/fifo/day22/graph_data.json

Current schema:
    day20_strategy_comparison
    day21_multi_seed_summary
    day21_runs
    coverage_distribution
    graph_specs

Outputs:
    results/fifo/day22/strategy_comparison.csv
    results/fifo/day22/day21_multi_seed.csv
    results/fifo/day22/coverage_distribution.csv
    results/fifo/day22/graph_points.csv
    results/fifo/day22/day22_summary.csv

Compatibility copies:
    graphs/day22_strategy_comparison.csv
    graphs/day22_multi_seed.csv
    graphs/day22_coverage_distribution.csv
    graphs/day22_graph_points.csv
"""

import csv
import json
import shutil
import sys
from pathlib import Path


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

GRAPHS_DIR = (
    ROOT
    / "graphs"
)


PRIMARY_INPUT = (
    DAY22_DIR
    / "day22_graph_data.json"
)

FALLBACK_INPUT = (
    DAY22_DIR
    / "graph_data.json"
)


STRATEGY_CSV = (
    DAY22_DIR
    / "strategy_comparison.csv"
)

MULTISEED_CSV = (
    DAY22_DIR
    / "day21_multi_seed.csv"
)

COVERAGE_DISTRIBUTION_CSV = (
    DAY22_DIR
    / "coverage_distribution.csv"
)

GRAPH_POINTS_CSV = (
    DAY22_DIR
    / "graph_points.csv"
)

SUMMARY_CSV = (
    DAY22_DIR
    / "day22_summary.csv"
)


# ============================================================
# LOAD JSON
# ============================================================

def load_json(path):

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


    if not isinstance(
        data,
        dict
    ):

        raise ValueError(
            "Day 22 graph data must be a JSON object."
        )


    return data


# ============================================================
# SELECT INPUT FILE
# ============================================================

def select_input():

    if PRIMARY_INPUT.exists():

        return PRIMARY_INPUT


    if FALLBACK_INPUT.exists():

        return FALLBACK_INPUT


    raise FileNotFoundError(
        "Neither day22_graph_data.json nor graph_data.json "
        "was found."
    )


# ============================================================
# SAFE VALUES
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
# CSV WRITER
# ============================================================

def write_csv(
    path,
    fieldnames,
    rows
):

    path.parent.mkdir(
        parents=True,
        exist_ok=True
    )


    with path.open(
        "w",
        encoding="utf-8",
        newline=""
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
            extrasaction="ignore"
        )

        writer.writeheader()

        for row in rows:

            writer.writerow(
                row
            )


# ============================================================
# COPY FILE
# ============================================================

def copy_file(
    source,
    destination
):

    destination.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    shutil.copy2(
        source,
        destination
    )


# ============================================================
# DAY 20 STRATEGY EXPORT
# ============================================================

def export_strategy_comparison(data):

    # --------------------------------------------------------
    # CURRENT FIELD
    #
    # Old scripts may have expected:
    #     strategies
    #
    # Current Day-22 graph JSON contains:
    #     day20_strategy_comparison
    # --------------------------------------------------------

    rows = data.get(
        "day20_strategy_comparison",
        []
    )


    if not isinstance(
        rows,
        list
    ):

        raise ValueError(
            "'day20_strategy_comparison' must be a list."
        )


    if not rows:

        raise ValueError(
            "No Day 20 strategy-comparison records found."
        )


    normalized = []


    for row in rows:

        if not isinstance(
            row,
            dict
        ):

            continue


        normalized.append(
            {
                "strategy":
                    str(
                        row.get(
                            "strategy",
                            "unknown"
                        )
                    ),

                "status":
                    str(
                        row.get(
                            "status",
                            "MEASURED"
                        )
                    ),

                "coverage_percent":
                    round(
                        safe_float(
                            row.get(
                                "coverage_percent"
                            )
                        ),
                        2
                    ),

                "covered_points":
                    safe_int(
                        row.get(
                            "covered_points"
                        )
                    ),

                "total_points":
                    safe_int(
                        row.get(
                            "total_points"
                        )
                    ),

                "missing_points":
                    row.get(
                        "missing_points",
                        ""
                    ),

                "stimulus_cycles":
                    safe_int(
                        row.get(
                            "stimulus_cycles"
                        )
                    ),

                "unique_behavior_signatures":
                    safe_int(
                        row.get(
                            "unique_behavior_signatures"
                        )
                    ),

                "redundant_cycles":
                    safe_int(
                        row.get(
                            "redundant_cycles"
                        )
                    ),

                "redundancy_percent":
                    round(
                        safe_float(
                            row.get(
                                "redundancy_percent"
                            )
                        ),
                        2
                    ),

                "coverage_percent_per_stimulus_cycle":
                    round(
                        safe_float(
                            row.get(
                                "coverage_percent_per_stimulus_cycle"
                            )
                        ),
                        4
                    ),
            }
        )


    write_csv(
        STRATEGY_CSV,

        [
            "strategy",
            "status",
            "coverage_percent",
            "covered_points",
            "total_points",
            "missing_points",
            "stimulus_cycles",
            "unique_behavior_signatures",
            "redundant_cycles",
            "redundancy_percent",
            "coverage_percent_per_stimulus_cycle",
        ],

        normalized
    )


    return normalized


# ============================================================
# DAY 21 MULTI-SEED EXPORT
# ============================================================

def export_day21_runs(data):

    # --------------------------------------------------------
    # IMPORTANT FIX
    #
    # OLD FIELD:
    #     random_runs
    #
    # CURRENT FIELD:
    #     day21_runs
    # --------------------------------------------------------

    rows = data.get(
        "day21_runs",
        []
    )


    if not isinstance(
        rows,
        list
    ):

        raise ValueError(
            "'day21_runs' must be a list."
        )


    if not rows:

        raise ValueError(
            "No Day 21 run records found."
        )


    normalized = []


    for index, row in enumerate(
        rows,
        start=1
    ):

        if not isinstance(
            row,
            dict
        ):

            continue


        normalized.append(
            {
                "run":
                    safe_int(
                        row.get(
                            "run",
                            index
                        ),
                        index
                    ),

                "seed":
                    safe_int(
                        row.get(
                            "seed"
                        )
                    ),

                "transactions":
                    safe_int(
                        row.get(
                            "transactions"
                        )
                    ),

                "status":
                    str(
                        row.get(
                            "status",
                            "UNKNOWN"
                        )
                    ),

                "total_checks":
                    safe_int(
                        row.get(
                            "total_checks"
                        )
                    ),

                "passed_checks":
                    safe_int(
                        row.get(
                            "passed_checks"
                        )
                    ),

                "failed_checks":
                    safe_int(
                        row.get(
                            "failed_checks"
                        )
                    ),

                "coverage_percent":
                    round(
                        safe_float(
                            row.get(
                                "coverage_percent"
                            )
                        ),
                        2
                    ),

                "unique_behavior_signatures":
                    safe_int(
                        row.get(
                            "unique_behavior_signatures"
                        )
                    ),

                "redundant_cycles":
                    safe_int(
                        row.get(
                            "redundant_cycles"
                        )
                    ),

                "redundancy_percent":
                    round(
                        safe_float(
                            row.get(
                                "redundancy_percent"
                            )
                        ),
                        2
                    ),

                "runtime_seconds":
                    round(
                        safe_float(
                            row.get(
                                "runtime_seconds"
                            )
                        ),
                        6
                    ),
            }
        )


    write_csv(
        MULTISEED_CSV,

        [
            "run",
            "seed",
            "transactions",
            "status",
            "total_checks",
            "passed_checks",
            "failed_checks",
            "coverage_percent",
            "unique_behavior_signatures",
            "redundant_cycles",
            "redundancy_percent",
            "runtime_seconds",
        ],

        normalized
    )


    return normalized


# ============================================================
# COVERAGE DISTRIBUTION EXPORT
# ============================================================

def export_coverage_distribution(data):

    rows = data.get(
        "coverage_distribution",
        []
    )


    if not isinstance(
        rows,
        list
    ):

        raise ValueError(
            "'coverage_distribution' must be a list."
        )


    normalized = []


    for row in rows:

        if not isinstance(
            row,
            dict
        ):

            continue


        normalized.append(
            {
                "coverage_percent":
                    round(
                        safe_float(
                            row.get(
                                "coverage_percent"
                            )
                        ),
                        2
                    ),

                "run_count":
                    safe_int(
                        row.get(
                            "run_count"
                        )
                    ),
            }
        )


    write_csv(
        COVERAGE_DISTRIBUTION_CSV,

        [
            "coverage_percent",
            "run_count",
        ],

        normalized
    )


    return normalized


# ============================================================
# GRAPH POINT EXPORT
# ============================================================

def export_graph_points(data):

    graph_specs = data.get(
        "graph_specs",
        {}
    )


    if not isinstance(
        graph_specs,
        dict
    ):

        raise ValueError(
            "'graph_specs' must be a JSON object."
        )


    rows = []


    for graph_id, spec in graph_specs.items():

        if not isinstance(
            spec,
            dict
        ):

            continue


        title = str(
            spec.get(
                "title",
                graph_id
            )
        )


        x_label = str(
            spec.get(
                "x_label",
                ""
            )
        )


        y_label = str(
            spec.get(
                "y_label",
                ""
            )
        )


        # ----------------------------------------------------
        # Case 1:
        # Separate x/y arrays
        # ----------------------------------------------------

        x_values = spec.get(
            "x"
        )

        y_values = spec.get(
            "y"
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

            count = min(
                len(
                    x_values
                ),
                len(
                    y_values
                )
            )


            for index in range(
                count
            ):

                rows.append(
                    {
                        "graph_id":
                            graph_id,

                        "title":
                            title,

                        "x_label":
                            x_label,

                        "y_label":
                            y_label,

                        "series":
                            "",

                        "point_index":
                            index + 1,

                        "x_value":
                            x_values[
                                index
                            ],

                        "y_value":
                            y_values[
                                index
                            ],
                    }
                )


        # ----------------------------------------------------
        # Case 2:
        # Point dictionaries
        # ----------------------------------------------------

        points = spec.get(
            "points"
        )


        if isinstance(
            points,
            list
        ):

            for index, point in enumerate(
                points,
                start=1
            ):

                if not isinstance(
                    point,
                    dict
                ):

                    continue


                strategy = str(
                    point.get(
                        "strategy",
                        point.get(
                            "series",
                            ""
                        )
                    )
                )


                if (
                    "stimulus_cycles"
                    in point
                ):

                    x_value = point.get(
                        "stimulus_cycles"
                    )

                elif (
                    "x"
                    in point
                ):

                    x_value = point.get(
                        "x"
                    )

                else:

                    x_value = index


                if (
                    "coverage_percent"
                    in point
                ):

                    y_value = point.get(
                        "coverage_percent"
                    )

                elif (
                    "y"
                    in point
                ):

                    y_value = point.get(
                        "y"
                    )

                else:

                    y_value = ""


                rows.append(
                    {
                        "graph_id":
                            graph_id,

                        "title":
                            title,

                        "x_label":
                            x_label,

                        "y_label":
                            y_label,

                        "series":
                            strategy,

                        "point_index":
                            index,

                        "x_value":
                            x_value,

                        "y_value":
                            y_value,
                    }
                )


    write_csv(
        GRAPH_POINTS_CSV,

        [
            "graph_id",
            "title",
            "x_label",
            "y_label",
            "series",
            "point_index",
            "x_value",
            "y_value",
        ],

        rows
    )


    return rows


# ============================================================
# DAY 22 SUMMARY EXPORT
# ============================================================

def export_summary(
    data,
    strategy_rows,
    run_rows,
    graph_rows
):

    summary = data.get(
        "day21_multi_seed_summary",
        {}
    )


    if not isinstance(
        summary,
        dict
    ):

        summary = {}


    rows = [
        {
            "metric":
                "dut",

            "value":
                data.get(
                    "dut",
                    "fifo"
                ),
        },

        {
            "metric":
                "day22_status",

            "value":
                data.get(
                    "status",
                    "PASS"
                ),
        },

        {
            "metric":
                "day20_strategy_count",

            "value":
                len(
                    strategy_rows
                ),
        },

        {
            "metric":
                "day21_run_count",

            "value":
                len(
                    run_rows
                ),
        },

        {
            "metric":
                "day21_passed_runs",

            "value":
                summary.get(
                    "passed_runs",
                    ""
                ),
        },

        {
            "metric":
                "day21_failed_runs",

            "value":
                summary.get(
                    "failed_runs",
                    ""
                ),
        },

        {
            "metric":
                "day21_average_coverage_percent",

            "value":
                summary.get(
                    "average_coverage_percent",
                    ""
                ),
        },

        {
            "metric":
                "day21_minimum_coverage_percent",

            "value":
                summary.get(
                    "minimum_coverage_percent",
                    ""
                ),
        },

        {
            "metric":
                "day21_maximum_coverage_percent",

            "value":
                summary.get(
                    "maximum_coverage_percent",
                    ""
                ),
        },

        {
            "metric":
                "day21_average_redundancy_percent",

            "value":
                summary.get(
                    "average_redundancy_percent",
                    ""
                ),
        },

        {
            "metric":
                "graph_specification_count",

            "value":
                len(
                    data.get(
                        "graph_specs",
                        {}
                    )
                ),
        },

        {
            "metric":
                "exported_graph_points",

            "value":
                len(
                    graph_rows
                ),
        },
    ]


    write_csv(
        SUMMARY_CSV,

        [
            "metric",
            "value",
        ],

        rows
    )


    return rows


# ============================================================
# MAIN
# ============================================================

def main():

    try:

        DAY22_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

        GRAPHS_DIR.mkdir(
            parents=True,
            exist_ok=True
        )


        input_file = (
            select_input()
        )


        data = load_json(
            input_file
        )


        # ====================================================
        # VALIDATE DAY 22 STATUS
        # ====================================================

        day22_status = str(
            data.get(
                "status",
                "PASS"
            )
        ).strip().upper()


        if day22_status != "PASS":

            raise ValueError(
                f"Day 22 graph-data status is "
                f"{day22_status}, expected PASS."
            )


        # ====================================================
        # EXPORT ALL TABLES
        # ====================================================

        strategy_rows = (
            export_strategy_comparison(
                data
            )
        )


        run_rows = (
            export_day21_runs(
                data
            )
        )


        coverage_rows = (
            export_coverage_distribution(
                data
            )
        )


        graph_rows = (
            export_graph_points(
                data
            )
        )


        summary_rows = (
            export_summary(
                data,
                strategy_rows,
                run_rows,
                graph_rows
            )
        )


        # ====================================================
        # BASIC VALIDATION
        # ====================================================

        if len(
            strategy_rows
        ) != 3:

            print(
                "WARNING: Expected 3 Day-20 strategies, "
                f"found {len(strategy_rows)}."
            )


        if len(
            run_rows
        ) != 10:

            print(
                "WARNING: Expected 10 Day-21 runs, "
                f"found {len(run_rows)}."
            )


        failed_runs = sum(
            1
            for row in run_rows
            if (
                row[
                    "status"
                ].upper()
                != "PASS"
                or row[
                    "failed_checks"
                ] != 0
            )
        )


        if failed_runs != 0:

            raise ValueError(
                f"{failed_runs} Day-21 runs "
                "contain failed verification results."
            )


        # ====================================================
        # COMPATIBILITY COPIES TO graphs/
        # ====================================================

        copy_file(
            STRATEGY_CSV,
            GRAPHS_DIR
            / "day22_strategy_comparison.csv"
        )


        copy_file(
            MULTISEED_CSV,
            GRAPHS_DIR
            / "day22_multi_seed.csv"
        )


        copy_file(
            COVERAGE_DISTRIBUTION_CSV,
            GRAPHS_DIR
            / "day22_coverage_distribution.csv"
        )


        copy_file(
            GRAPH_POINTS_CSV,
            GRAPHS_DIR
            / "day22_graph_points.csv"
        )


        # ====================================================
        # PRINT SUMMARY
        # ====================================================

        print(
            "=" * 72
        )

        print(
            "DAY 22 CSV EXPORT"
        )

        print(
            "=" * 72
        )


        print(
            "Source                      :",
            input_file.relative_to(
                ROOT
            )
        )


        print(
            "Strategy rows exported      :",
            len(
                strategy_rows
            )
        )


        print(
            "Day 21 runs exported        :",
            len(
                run_rows
            )
        )


        print(
            "Coverage distribution rows  :",
            len(
                coverage_rows
            )
        )


        print(
            "Graph points exported       :",
            len(
                graph_rows
            )
        )


        print(
            "Summary rows exported       :",
            len(
                summary_rows
            )
        )


        print(
            "-" * 72
        )


        print(
            "Strategy CSV                :",
            STRATEGY_CSV.relative_to(
                ROOT
            )
        )


        print(
            "Multi-seed CSV              :",
            MULTISEED_CSV.relative_to(
                ROOT
            )
        )


        print(
            "Coverage distribution CSV   :",
            COVERAGE_DISTRIBUTION_CSV.relative_to(
                ROOT
            )
        )


        print(
            "Graph points CSV            :",
            GRAPH_POINTS_CSV.relative_to(
                ROOT
            )
        )


        print(
            "Summary CSV                 :",
            SUMMARY_CSV.relative_to(
                ROOT
            )
        )


        print(
            "-" * 72
        )


        print(
            "DAY 22 CSV EXPORT STATUS    : PASS"
        )


        print(
            "=" * 72
        )


        print(
            "DAY 22 CSV EXPORT: PASS"
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
            "DAY 22 CSV EXPORT: FAIL"
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
