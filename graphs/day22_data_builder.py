#!/usr/bin/env python3

"""
Day 22 - Graph Data Builder
===========================

Project:
AI-Driven RTL Test Generation,
Coverage Analysis and Verification

Purpose
-------
Build clean graph/table input data from the actual Day-20 and
Day-21 FIFO experiment results.

Supported current files
-----------------------
Day 20:
    results/fifo/day20/strategy_comparison.json

Day 21:
    results/fifo/day21/day21_final_summary.json
or:
    results/fifo/day21/day21_experiment_summary.json

Optional:
    results/fifo/day21/day21_statistics.json
    results/fifo/day21/reference_comparison.json

Generated outputs
-----------------
results/fifo/day22/day22_graph_data.json
results/fifo/day22/strategy_comparison.csv
results/fifo/day22/day21_multi_seed.csv
results/fifo/day22/coverage_distribution.csv

Compatibility copies
--------------------
graphs/day22_graph_data.json
graphs/day22_strategy_comparison.csv
graphs/day22_multi_seed.csv

Important
---------
This script reports measured values. It does not invent coverage,
runtime, status, or superiority claims.
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

DAY20_DIR = (
    ROOT
    / "results"
    / "fifo"
    / "day20"
)

DAY21_DIR = (
    ROOT
    / "results"
    / "fifo"
    / "day21"
)

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


DAY20_STRATEGY_FILE = (
    DAY20_DIR
    / "strategy_comparison.json"
)

DAY21_FINAL_SUMMARY = (
    DAY21_DIR
    / "day21_final_summary.json"
)

DAY21_EXPERIMENT_SUMMARY = (
    DAY21_DIR
    / "day21_experiment_summary.json"
)

DAY21_LEGACY_SUMMARY = (
    DAY21_DIR
    / "multi_seed_results.json"
)

DAY21_STATISTICS = (
    DAY21_DIR
    / "day21_statistics.json"
)

DAY21_REFERENCE = (
    DAY21_DIR
    / "reference_comparison.json"
)


OUTPUT_JSON = (
    DAY22_DIR
    / "day22_graph_data.json"
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


# ============================================================
# JSON HELPERS
# ============================================================

def load_json(path, required=True):

    if not path.exists():

        if required:
            raise FileNotFoundError(
                f"Required file not found: {path}"
            )

        return None

    try:

        with path.open(
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

    except json.JSONDecodeError as exc:

        raise ValueError(
            f"Invalid JSON in {path}: "
            f"line {exc.lineno}, "
            f"column {exc.colno}: "
            f"{exc.msg}"
        ) from exc

    return data


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

        f.write("\n")


# ============================================================
# SAFE CONVERSIONS
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
# STATUS NORMALIZATION
# ============================================================

def normalize_status(record):

    """
    Current project files do not all use the same status field.

    Supported:
        status
        simulation_status
        all_runs_passed
        failed_checks

    If this is only a measurement record and no execution status
    exists, return MEASURED instead of raising KeyError.
    """

    if not isinstance(record, dict):
        return "UNKNOWN"


    value = record.get(
        "status"
    )

    if value is not None:

        return str(
            value
        ).strip().upper()


    value = record.get(
        "simulation_status"
    )

    if value is not None:

        return str(
            value
        ).strip().upper()


    if (
        "all_runs_passed"
        in record
    ):

        return (
            "PASS"
            if bool(
                record[
                    "all_runs_passed"
                ]
            )
            else "FAIL"
        )


    if (
        "failed_checks"
        in record
    ):

        failed_checks = safe_int(
            record.get(
                "failed_checks"
            ),
            -1
        )

        if failed_checks == 0:
            return "PASS"

        if failed_checks > 0:
            return "FAIL"


    return "MEASURED"


# ============================================================
# SELECT DAY 21 SUMMARY
# ============================================================

def select_day21_summary():

    candidates = [
        DAY21_FINAL_SUMMARY,
        DAY21_EXPERIMENT_SUMMARY,
        DAY21_LEGACY_SUMMARY,
    ]

    for candidate in candidates:

        if candidate.exists():

            return candidate


    raise FileNotFoundError(
        "No Day 21 summary was found. Expected one of:\n"
        "  results/fifo/day21/day21_final_summary.json\n"
        "  results/fifo/day21/day21_experiment_summary.json\n"
        "  results/fifo/day21/multi_seed_results.json"
    )


# ============================================================
# WRITE CSV
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
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames
        )

        writer.writeheader()

        writer.writerows(
            rows
        )


# ============================================================
# DAY 20 STRATEGY DATA
# ============================================================

def build_day20_strategy_data(day20):

    strategies = day20.get(
        "strategies",
        []
    )

    if not isinstance(
        strategies,
        list
    ):

        raise ValueError(
            "Day 20 'strategies' field must be a list."
        )


    if not strategies:

        raise ValueError(
            "No Day 20 strategies were found."
        )


    rows = []


    for strategy in strategies:

        if not isinstance(
            strategy,
            dict
        ):
            continue


        name = str(
            strategy.get(
                "strategy",
                "unknown"
            )
        )


        coverage_percent = safe_float(
            strategy.get(
                "coverage_percent",
                0.0
            )
        )


        covered_points = safe_int(
            strategy.get(
                "covered_points",
                0
            )
        )


        total_points = safe_int(
            strategy.get(
                "total_points",
                0
            )
        )


        stimulus_cycles = safe_int(
            strategy.get(
                "stimulus_cycles",
                strategy.get(
                    "transactions",
                    0
                )
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


        missing_points = strategy.get(
            "missing_points",
            []
        )


        if isinstance(
            missing_points,
            list
        ):

            missing_points_text = ";".join(
                str(item)
                for item in missing_points
            )

        else:

            missing_points_text = str(
                missing_points
            )


        rows.append(
            {
                "strategy":
                    name,

                "status":
                    normalize_status(
                        strategy
                    ),

                "coverage_percent":
                    round(
                        coverage_percent,
                        2
                    ),

                "covered_points":
                    covered_points,

                "total_points":
                    total_points,

                "missing_points":
                    missing_points_text,

                "stimulus_cycles":
                    stimulus_cycles,

                "unique_behavior_signatures":
                    unique_signatures,

                "redundant_cycles":
                    redundant_cycles,

                "redundancy_percent":
                    round(
                        redundancy_percent,
                        2
                    ),

                "coverage_percent_per_stimulus_cycle":
                    round(
                        coverage_efficiency,
                        4
                    ),
            }
        )


    return rows


# ============================================================
# EXTRACT DAY 21 RUN LIST
# ============================================================

def get_day21_runs(day21):

    runs = day21.get(
        "runs",
        []
    )

    if not isinstance(
        runs,
        list
    ):

        raise ValueError(
            "Day 21 'runs' field must be a list."
        )


    if not runs:

        raise ValueError(
            "Day 21 summary contains no runs."
        )


    return runs


# ============================================================
# DAY 21 RUN DATA
# ============================================================

def build_day21_run_data(day21):

    runs = get_day21_runs(
        day21
    )

    rows = []


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


        status = normalize_status(
            run
        )


        rows.append(
            {
                "run":
                    run_number,

                "seed":
                    safe_int(
                        run.get(
                            "seed",
                            0
                        )
                    ),

                "transactions":
                    safe_int(
                        run.get(
                            "transactions",
                            day21.get(
                                "transactions_per_run",
                                0
                            )
                        )
                    ),

                "status":
                    status,

                "total_checks":
                    safe_int(
                        run.get(
                            "total_checks",
                            0
                        )
                    ),

                "passed_checks":
                    safe_int(
                        run.get(
                            "passed_checks",
                            0
                        )
                    ),

                "failed_checks":
                    safe_int(
                        run.get(
                            "failed_checks",
                            0
                        )
                    ),

                "coverage_percent":
                    round(
                        safe_float(
                            run.get(
                                "coverage_percent",
                                0.0
                            )
                        ),
                        2
                    ),

                "unique_behavior_signatures":
                    safe_int(
                        run.get(
                            "unique_behavior_signatures",
                            0
                        )
                    ),

                "redundant_cycles":
                    safe_int(
                        run.get(
                            "redundant_cycles",
                            0
                        )
                    ),

                "redundancy_percent":
                    round(
                        safe_float(
                            run.get(
                                "redundancy_percent",
                                0.0
                            )
                        ),
                        2
                    ),

                "runtime_seconds":
                    round(
                        safe_float(
                            run.get(
                                "runtime_seconds",
                                0.0
                            )
                        ),
                        6
                    ),
            }
        )


    return rows


# ============================================================
# DAY 21 SUMMARY VALUES
# ============================================================

def build_day21_summary_data(
    day21,
    run_rows
):

    coverage_values = [
        row[
            "coverage_percent"
        ]
        for row in run_rows
    ]


    redundancy_values = [
        row[
            "redundancy_percent"
        ]
        for row in run_rows
    ]


    runtime_values = [
        row[
            "runtime_seconds"
        ]
        for row in run_rows
    ]


    unique_values = [
        row[
            "unique_behavior_signatures"
        ]
        for row in run_rows
    ]


    passed_runs = sum(
        1
        for row in run_rows
        if row[
            "status"
        ] == "PASS"
    )


    failed_runs = (
        len(
            run_rows
        )
        - passed_runs
    )


    if coverage_values:

        average_coverage = round(
            sum(
                coverage_values
            )
            / len(
                coverage_values
            ),
            2
        )

        minimum_coverage = round(
            min(
                coverage_values
            ),
            2
        )

        maximum_coverage = round(
            max(
                coverage_values
            ),
            2
        )

    else:

        average_coverage = 0.0
        minimum_coverage = 0.0
        maximum_coverage = 0.0


    if redundancy_values:

        average_redundancy = round(
            sum(
                redundancy_values
            )
            / len(
                redundancy_values
            ),
            2
        )

    else:

        average_redundancy = 0.0


    if runtime_values:

        average_runtime = round(
            sum(
                runtime_values
            )
            / len(
                runtime_values
            ),
            6
        )

    else:

        average_runtime = 0.0


    if unique_values:

        average_unique = round(
            sum(
                unique_values
            )
            / len(
                unique_values
            ),
            2
        )

    else:

        average_unique = 0.0


    return {
        "status":
            normalize_status(
                day21
            ),

        "number_of_runs":
            len(
                run_rows
            ),

        "transactions_per_run":
            safe_int(
                day21.get(
                    "transactions_per_run",
                    (
                        run_rows[0][
                            "transactions"
                        ]
                        if run_rows
                        else 0
                    )
                )
            ),

        "total_transactions":
            sum(
                row[
                    "transactions"
                ]
                for row in run_rows
            ),

        "passed_runs":
            passed_runs,

        "failed_runs":
            failed_runs,

        "average_coverage_percent":
            average_coverage,

        "minimum_coverage_percent":
            minimum_coverage,

        "maximum_coverage_percent":
            maximum_coverage,

        "average_redundancy_percent":
            average_redundancy,

        "average_runtime_seconds":
            average_runtime,

        "average_unique_behavior_signatures":
            average_unique,

        "total_verification_checks":
            sum(
                row[
                    "total_checks"
                ]
                for row in run_rows
            ),

        "total_passed_checks":
            sum(
                row[
                    "passed_checks"
                ]
                for row in run_rows
            ),

        "total_failed_checks":
            sum(
                row[
                    "failed_checks"
                ]
                for row in run_rows
            ),
    }


# ============================================================
# COVERAGE DISTRIBUTION TABLE
# ============================================================

def build_coverage_distribution(
    run_rows
):

    distribution = {}


    for row in run_rows:

        coverage = row[
            "coverage_percent"
        ]

        key = (
            f"{coverage:.2f}"
        )

        distribution[
            key
        ] = (
            distribution.get(
                key,
                0
            )
            + 1
        )


    rows = []


    for coverage_text in sorted(
        distribution.keys(),
        key=lambda value: float(
            value
        )
    ):

        count = distribution[
            coverage_text
        ]

        rows.append(
            {
                "coverage_percent":
                    float(
                        coverage_text
                    ),

                "run_count":
                    count,
            }
        )


    return rows


# ============================================================
# GRAPH-SPEC DATA
# ============================================================

def build_graph_specs(
    strategy_rows,
    run_rows,
    day21_summary
):

    return {

        "graph_01_strategy_coverage": {
            "title":
                "FIFO Functional Coverage by Verification Strategy",

            "x_label":
                "Verification Strategy",

            "y_label":
                "Functional Coverage (%)",

            "x":
                [
                    row[
                        "strategy"
                    ]
                    for row
                    in strategy_rows
                ],

            "y":
                [
                    row[
                        "coverage_percent"
                    ]
                    for row
                    in strategy_rows
                ],
        },


        "graph_02_tests_vs_coverage": {
            "title":
                "FIFO Stimulus Count vs Functional Coverage",

            "x_label":
                "Stimulus Cycles",

            "y_label":
                "Functional Coverage (%)",

            "points":
                [
                    {
                        "strategy":
                            row[
                                "strategy"
                            ],

                        "stimulus_cycles":
                            row[
                                "stimulus_cycles"
                            ],

                        "coverage_percent":
                            row[
                                "coverage_percent"
                            ],
                    }

                    for row
                    in strategy_rows
                ],
        },


        "graph_03_redundancy": {
            "title":
                "FIFO Verification Strategy Redundancy",

            "x_label":
                "Verification Strategy",

            "y_label":
                "Redundancy (%)",

            "x":
                [
                    row[
                        "strategy"
                    ]
                    for row
                    in strategy_rows
                ],

            "y":
                [
                    row[
                        "redundancy_percent"
                    ]
                    for row
                    in strategy_rows
                ],
        },


        "graph_04_day21_seed_coverage": {
            "title":
                "Day 21 FIFO Coverage Across Random Seeds",

            "x_label":
                "Experiment Run",

            "y_label":
                "Functional Coverage (%)",

            "x":
                [
                    row[
                        "run"
                    ]
                    for row
                    in run_rows
                ],

            "y":
                [
                    row[
                        "coverage_percent"
                    ]
                    for row
                    in run_rows
                ],
        },


        "graph_05_day21_seed_redundancy": {
            "title":
                "Day 21 FIFO Redundancy Across Random Seeds",

            "x_label":
                "Experiment Run",

            "y_label":
                "Redundancy (%)",

            "x":
                [
                    row[
                        "run"
                    ]
                    for row
                    in run_rows
                ],

            "y":
                [
                    row[
                        "redundancy_percent"
                    ]
                    for row
                    in run_rows
                ],
        },


        "graph_06_day20_vs_day21_random": {
            "title":
                "Single-Run and Multi-Seed Random FIFO Coverage",

            "x_label":
                "Measurement",

            "y_label":
                "Functional Coverage (%)",

            "x": [
                "Day20 Random",
                "Day21 Random Mean",
                "Day21 Random Min",
                "Day21 Random Max",
            ],

            "y": [
                next(
                    (
                        row[
                            "coverage_percent"
                        ]

                        for row
                        in strategy_rows

                        if row[
                            "strategy"
                        ].lower()
                        == "random"
                    ),
                    0.0
                ),

                day21_summary[
                    "average_coverage_percent"
                ],

                day21_summary[
                    "minimum_coverage_percent"
                ],

                day21_summary[
                    "maximum_coverage_percent"
                ],
            ],
        },
    }


# ============================================================
# COPY COMPATIBILITY OUTPUT
# ============================================================

def copy_if_exists(
    source,
    destination
):

    if source.exists():

        destination.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        shutil.copy2(
            source,
            destination
        )


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


        # ====================================================
        # LOAD DAY 20
        # ====================================================

        day20 = load_json(
            DAY20_STRATEGY_FILE
        )


        # ====================================================
        # LOAD DAY 21
        # ====================================================

        day21_summary_file = (
            select_day21_summary()
        )

        day21 = load_json(
            day21_summary_file
        )


        # ====================================================
        # OPTIONAL DATA
        # ====================================================

        day21_statistics = load_json(
            DAY21_STATISTICS,
            required=False
        )

        day21_reference = load_json(
            DAY21_REFERENCE,
            required=False
        )


        # ====================================================
        # BUILD DATA
        # ====================================================

        strategy_rows = (
            build_day20_strategy_data(
                day20
            )
        )


        run_rows = (
            build_day21_run_data(
                day21
            )
        )


        day21_summary = (
            build_day21_summary_data(
                day21,
                run_rows
            )
        )


        coverage_distribution = (
            build_coverage_distribution(
                run_rows
            )
        )


        graph_specs = (
            build_graph_specs(
                strategy_rows,
                run_rows,
                day21_summary
            )
        )


        # ====================================================
        # WRITE STRATEGY CSV
        # ====================================================

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

            strategy_rows
        )


        # ====================================================
        # WRITE MULTI-SEED CSV
        # ====================================================

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

            run_rows
        )


        # ====================================================
        # COVERAGE DISTRIBUTION CSV
        # ====================================================

        write_csv(
            COVERAGE_DISTRIBUTION_CSV,

            [
                "coverage_percent",
                "run_count",
            ],

            coverage_distribution
        )


        # ====================================================
        # MAIN JSON OUTPUT
        # ====================================================

        graph_data = {

            "day":
                22,

            "dut":
                "fifo",

            "build_type":
                "graph_and_table_data",

            "status":
                "PASS",

            "source_files": {

                "day20_strategy_comparison":
                    DAY20_STRATEGY_FILE.relative_to(
                        ROOT
                    ).as_posix(),

                "day21_summary":
                    day21_summary_file.relative_to(
                        ROOT
                    ).as_posix(),

                "day21_statistics":
                    (
                        DAY21_STATISTICS.relative_to(
                            ROOT
                        ).as_posix()
                        if DAY21_STATISTICS.exists()
                        else None
                    ),

                "day21_reference_comparison":
                    (
                        DAY21_REFERENCE.relative_to(
                            ROOT
                        ).as_posix()
                        if DAY21_REFERENCE.exists()
                        else None
                    ),
            },

            "day20_strategy_comparison":
                strategy_rows,

            "day21_multi_seed_summary":
                day21_summary,

            "day21_runs":
                run_rows,

            "coverage_distribution":
                coverage_distribution,

            "graph_specs":
                graph_specs,

            "day21_statistics_available":
                day21_statistics
                is not None,

            "day21_reference_comparison_available":
                day21_reference
                is not None,

            "interpretation_rule":
                day20.get(
                    "interpretation_rule",
                    (
                        "Report measured values without "
                        "assuming a strategy is superior."
                    )
                ),

            "rtl_modified":
                False,

            "graph_data_complete":
                True,
        }


        save_json(
            OUTPUT_JSON,
            graph_data
        )


        # ====================================================
        # COMPATIBILITY COPIES
        # ====================================================

        copy_if_exists(
            OUTPUT_JSON,
            GRAPHS_DIR
            / "day22_graph_data.json"
        )

        copy_if_exists(
            STRATEGY_CSV,
            GRAPHS_DIR
            / "day22_strategy_comparison.csv"
        )

        copy_if_exists(
            MULTISEED_CSV,
            GRAPHS_DIR
            / "day22_multi_seed.csv"
        )


        # ====================================================
        # VALIDATE CURRENT MEASURED VALUES
        # ====================================================

        if not run_rows:

            raise ValueError(
                "No Day 21 graph records were generated."
            )


        if (
            day21_summary[
                "failed_runs"
            ]
            != 0
        ):

            raise ValueError(
                "Day 21 contains failed experiment runs."
            )


        # ====================================================
        # PRINT SUMMARY
        # ====================================================

        print(
            "=" * 72
        )

        print(
            "DAY 22 GRAPH DATA BUILD"
        )

        print(
            "=" * 72
        )

        print(
            "DUT                         : FIFO"
        )

        print(
            "Day 20 strategies           :",
            len(
                strategy_rows
            )
        )

        print(
            "Day 21 experiment runs      :",
            len(
                run_rows
            )
        )

        print(
            "Day 21 passed runs          :",
            day21_summary[
                "passed_runs"
            ]
        )

        print(
            "Day 21 failed runs          :",
            day21_summary[
                "failed_runs"
            ]
        )

        print(
            "Day 21 average coverage     :",
            f"{day21_summary['average_coverage_percent']:.2f}%"
        )

        print(
            "Day 21 min coverage         :",
            f"{day21_summary['minimum_coverage_percent']:.2f}%"
        )

        print(
            "Day 21 max coverage         :",
            f"{day21_summary['maximum_coverage_percent']:.2f}%"
        )

        print(
            "Day 21 avg redundancy       :",
            f"{day21_summary['average_redundancy_percent']:.2f}%"
        )

        print(
            "-" * 72
        )

        print(
            "Graph data JSON             :",
            OUTPUT_JSON.relative_to(
                ROOT
            )
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
            "-" * 72
        )

        print(
            "Graph specifications built  :",
            len(
                graph_specs
            )
        )

        print(
            "DAY 22 STATUS               : PASS"
        )

        print(
            "=" * 72
        )

        print(
            "DAY 22 GRAPH DATA BUILD: PASS"
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
            "DAY 22 GRAPH DATA BUILD: FAIL"
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
