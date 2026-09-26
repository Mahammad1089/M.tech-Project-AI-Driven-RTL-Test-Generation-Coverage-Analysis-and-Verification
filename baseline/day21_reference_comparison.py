#!/usr/bin/env python3

"""
Day 21 - Reference Comparison
=============================

Project:
AI-Driven RTL Test Generation,
Coverage Analysis and Verification

Purpose:
- Compare the Day-21 repeated random experiments against
  the Day-20 random baseline reference.
- Use the CURRENT Day-21 JSON schema.
- Remain compatible with older field names such as run_count.
- Report measured differences without claiming that one
  strategy is inherently superior.

Inputs:
    results/fifo/day20/strategy_comparison.json
    results/fifo/day21/day21_experiment_summary.json

Optional:
    results/fifo/day21/day21_statistics.json
    results/fifo/day21/aggregate_statistics.json

Output:
    results/fifo/day21/reference_comparison.json
"""

import json
import statistics
import sys
from pathlib import Path


# ============================================================
# PROJECT PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

DAY20_COMPARISON = (
    ROOT
    / "results"
    / "fifo"
    / "day20"
    / "strategy_comparison.json"
)

DAY21_DIR = (
    ROOT
    / "results"
    / "fifo"
    / "day21"
)

DAY21_SUMMARY = (
    DAY21_DIR
    / "day21_experiment_summary.json"
)

DAY21_SUMMARY_FALLBACK = (
    DAY21_DIR
    / "multi_seed_results.json"
)

DAY21_STATISTICS = (
    DAY21_DIR
    / "day21_statistics.json"
)

DAY21_STATISTICS_FALLBACK = (
    DAY21_DIR
    / "aggregate_statistics.json"
)

OUTPUT_FILE = (
    DAY21_DIR
    / "reference_comparison.json"
)


# ============================================================
# JSON HELPERS
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
        ) as f:
            data = json.load(f)

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
# SELECT DAY 21 SUMMARY
# ============================================================

def select_day21_summary():

    if DAY21_SUMMARY.exists():
        return DAY21_SUMMARY

    if DAY21_SUMMARY_FALLBACK.exists():
        return DAY21_SUMMARY_FALLBACK

    raise FileNotFoundError(
        "Day 21 summary not found. Expected either "
        "day21_experiment_summary.json or "
        "multi_seed_results.json."
    )


# ============================================================
# OPTIONAL STATISTICS FILE
# ============================================================

def select_statistics_file():

    if DAY21_STATISTICS.exists():
        return DAY21_STATISTICS

    if DAY21_STATISTICS_FALLBACK.exists():
        return DAY21_STATISTICS_FALLBACK

    return None


# ============================================================
# FIND DAY 20 RANDOM BASELINE
# ============================================================

def find_random_reference(day20):

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

    for strategy in strategies:

        if not isinstance(
            strategy,
            dict
        ):
            continue

        name = str(
            strategy.get(
                "strategy",
                ""
            )
        ).strip().lower()

        if name == "random":
            return strategy

    raise ValueError(
        "Random strategy was not found in "
        "Day 20 strategy_comparison.json."
    )


# ============================================================
# CALCULATE DAY 21 VALUES DIRECTLY FROM RUNS
# ============================================================

def calculate_day21_values(summary):

    runs = summary.get(
        "runs",
        []
    )

    if not isinstance(
        runs,
        list
    ):
        raise ValueError(
            "'runs' must be a JSON list."
        )

    if not runs:
        raise ValueError(
            "No Day 21 runs were found."
        )


    # --------------------------------------------------------
    # CURRENT FIELD:
    # number_of_runs
    #
    # OLD FALLBACK:
    # run_count
    # --------------------------------------------------------

    number_of_runs = safe_int(
        summary.get(
            "number_of_runs",
            summary.get(
                "run_count",
                summary.get(
                    "total_runs",
                    len(runs)
                )
            )
        ),
        len(runs)
    )


    transactions_per_run = safe_int(
        summary.get(
            "transactions_per_run",
            summary.get(
                "cycles_per_run",
                summary.get(
                    "random_cycles",
                    0
                )
            )
        )
    )


    passed_runs = safe_int(
        summary.get(
            "passed_runs",
            0
        )
    )


    failed_runs = safe_int(
        summary.get(
            "failed_runs",
            0
        )
    )


    coverage_values = []

    redundancy_values = []

    unique_values = []

    redundant_cycle_values = []

    runtime_values = []

    transaction_values = []

    failed_check_values = []


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


        redundancy_values.append(
            safe_float(
                run.get(
                    "redundancy_percent",
                    0.0
                )
            )
        )


        unique_values.append(
            safe_int(
                run.get(
                    "unique_behavior_signatures",
                    0
                )
            )
        )


        redundant_cycle_values.append(
            safe_int(
                run.get(
                    "redundant_cycles",
                    0
                )
            )
        )


        runtime_values.append(
            safe_float(
                run.get(
                    "runtime_seconds",
                    0.0
                )
            )
        )


        transaction_values.append(
            safe_int(
                run.get(
                    "transactions",
                    transactions_per_run
                )
            )
        )


        failed_check_values.append(
            safe_int(
                run.get(
                    "failed_checks",
                    0
                )
            )
        )


    average_coverage = round(
        statistics.mean(
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


    median_coverage = round(
        statistics.median(
            coverage_values
        ),
        2
    )


    average_redundancy = round(
        statistics.mean(
            redundancy_values
        ),
        2
    )


    average_unique = round(
        statistics.mean(
            unique_values
        ),
        2
    )


    average_redundant_cycles = round(
        statistics.mean(
            redundant_cycle_values
        ),
        2
    )


    average_runtime = round(
        statistics.mean(
            runtime_values
        ),
        6
    )


    total_transactions = sum(
        transaction_values
    )


    total_failed_checks = sum(
        failed_check_values
    )


    runs_at_100 = sum(
        1
        for value in coverage_values
        if abs(
            value - 100.0
        ) < 0.0001
    )


    return {

        # Current canonical field
        "number_of_runs":
            number_of_runs,

        # Compatibility alias so old downstream
        # scripts do not fail with KeyError.
        "run_count":
            number_of_runs,

        "transactions_per_run":
            transactions_per_run,

        "total_transactions":
            total_transactions,

        "passed_runs":
            passed_runs,

        "failed_runs":
            failed_runs,

        "total_failed_checks":
            total_failed_checks,

        "average_coverage_percent":
            average_coverage,

        "minimum_coverage_percent":
            minimum_coverage,

        "maximum_coverage_percent":
            maximum_coverage,

        "median_coverage_percent":
            median_coverage,

        "runs_at_100_percent":
            runs_at_100,

        "average_redundancy_percent":
            average_redundancy,

        "average_unique_behavior_signatures":
            average_unique,

        "average_redundant_cycles":
            average_redundant_cycles,

        "average_runtime_seconds":
            average_runtime,

        "coverage_values":
            coverage_values,

        "redundancy_values":
            redundancy_values,
    }


# ============================================================
# MAIN
# ============================================================

def main():

    try:

        # ====================================================
        # LOAD DAY 20 REFERENCE
        # ====================================================

        day20 = load_json(
            DAY20_COMPARISON
        )

        random_reference = (
            find_random_reference(
                day20
            )
        )


        # ====================================================
        # LOAD DAY 21 RESULTS
        # ====================================================

        summary_file = (
            select_day21_summary()
        )

        day21 = load_json(
            summary_file
        )


        day21_values = (
            calculate_day21_values(
                day21
            )
        )


        # ====================================================
        # OPTIONAL DAY 21 STATISTICS FILE
        # ====================================================

        statistics_file = (
            select_statistics_file()
        )

        statistics_present = (
            statistics_file
            is not None
        )


        # ====================================================
        # DAY 20 RANDOM REFERENCE VALUES
        # ====================================================

        reference_coverage = safe_float(
            random_reference.get(
                "coverage_percent",
                0.0
            )
        )


        reference_cycles = safe_int(
            random_reference.get(
                "stimulus_cycles",
                0
            )
        )


        reference_unique = safe_int(
            random_reference.get(
                "unique_behavior_signatures",
                0
            )
        )


        reference_redundant = safe_int(
            random_reference.get(
                "redundant_cycles",
                0
            )
        )


        reference_redundancy = safe_float(
            random_reference.get(
                "redundancy_percent",
                0.0
            )
        )


        # ====================================================
        # DAY 21 VALUES
        # ====================================================

        day21_average_coverage = (
            day21_values[
                "average_coverage_percent"
            ]
        )


        day21_average_redundancy = (
            day21_values[
                "average_redundancy_percent"
            ]
        )


        day21_average_unique = (
            day21_values[
                "average_unique_behavior_signatures"
            ]
        )


        day21_transactions_per_run = (
            day21_values[
                "transactions_per_run"
            ]
        )


        # ====================================================
        # DIFFERENCES
        #
        # Positive means Day21 measured value is numerically
        # higher than the Day20 random reference.
        #
        # Negative means numerically lower.
        #
        # This is descriptive only.
        # ====================================================

        coverage_difference = round(
            day21_average_coverage
            - reference_coverage,
            2
        )


        redundancy_difference = round(
            day21_average_redundancy
            - reference_redundancy,
            2
        )


        unique_difference = round(
            day21_average_unique
            - reference_unique,
            2
        )


        cycle_difference = (
            day21_transactions_per_run
            - reference_cycles
        )


        # ====================================================
        # COMPARISON OUTPUT
        # ====================================================

        result = {

            "day":
                21,

            "dut":
                "fifo",

            "comparison_type":
                "day20_random_reference_vs_day21_multi_seed",

            "coverage_model":
                day20.get(
                    "coverage_model",
                    "same_fifo_functional_coverage_model"
                ),

            "day20_random_reference": {

                "strategy":
                    "random",

                "coverage_percent":
                    reference_coverage,

                "stimulus_cycles":
                    reference_cycles,

                "unique_behavior_signatures":
                    reference_unique,

                "redundant_cycles":
                    reference_redundant,

                "redundancy_percent":
                    reference_redundancy,
            },

            "day21_multi_seed_measurement": {

                "number_of_runs":
                    day21_values[
                        "number_of_runs"
                    ],

                # Compatibility field
                "run_count":
                    day21_values[
                        "number_of_runs"
                    ],

                "transactions_per_run":
                    day21_transactions_per_run,

                "total_transactions":
                    day21_values[
                        "total_transactions"
                    ],

                "passed_runs":
                    day21_values[
                        "passed_runs"
                    ],

                "failed_runs":
                    day21_values[
                        "failed_runs"
                    ],

                "average_coverage_percent":
                    day21_average_coverage,

                "minimum_coverage_percent":
                    day21_values[
                        "minimum_coverage_percent"
                    ],

                "maximum_coverage_percent":
                    day21_values[
                        "maximum_coverage_percent"
                    ],

                "median_coverage_percent":
                    day21_values[
                        "median_coverage_percent"
                    ],

                "runs_at_100_percent":
                    day21_values[
                        "runs_at_100_percent"
                    ],

                "average_redundancy_percent":
                    day21_average_redundancy,

                "average_unique_behavior_signatures":
                    day21_average_unique,

                "average_redundant_cycles":
                    day21_values[
                        "average_redundant_cycles"
                    ],

                "average_runtime_seconds":
                    day21_values[
                        "average_runtime_seconds"
                    ],

                "total_failed_checks":
                    day21_values[
                        "total_failed_checks"
                    ],
            },

            "measured_differences": {

                "coverage_percentage_point_difference":
                    coverage_difference,

                "redundancy_percentage_point_difference":
                    redundancy_difference,

                "unique_behavior_signature_difference":
                    unique_difference,

                "stimulus_or_transaction_count_difference_per_run":
                    cycle_difference,
            },

            "interpretation": {

                "coverage":
                    (
                        "Day 21 reports the mean coverage "
                        "across repeated random seeds; Day 20 "
                        "is a single random baseline run."
                    ),

                "redundancy":
                    (
                        "Redundancy values are reported as "
                        "measured and are not used alone to "
                        "declare one method superior."
                    ),

                "experimental_note":
                    (
                        "The Day 20 and Day 21 measurements "
                        "use different random experiment sizes, "
                        "so differences should be reported "
                        "together with the number of stimulus "
                        "cycles/transactions."
                    ),

                "decision_rule":
                    (
                        "Report measured values without "
                        "assuming a strategy is superior."
                    ),
            },

            "source_files": {

                "day20_reference":
                    DAY20_COMPARISON.relative_to(
                        ROOT
                    ).as_posix(),

                "day21_summary":
                    summary_file.relative_to(
                        ROOT
                    ).as_posix(),

                "day21_statistics":
                    (
                        statistics_file.relative_to(
                            ROOT
                        ).as_posix()
                        if statistics_file
                        is not None
                        else None
                    ),
            },

            "statistics_file_present":
                statistics_present,

            "rtl_modified":
                False,

            "comparison_complete":
                True,
        }


        # ====================================================
        # SAVE OUTPUT
        # ====================================================

        save_json(
            OUTPUT_FILE,
            result
        )


        # ====================================================
        # PRINT RESULTS
        # ====================================================

        print(
            "=" * 72
        )

        print(
            "DAY 21 REFERENCE COMPARISON"
        )

        print(
            "=" * 72
        )

        print(
            "DUT                         : FIFO"
        )

        print(
            "Day 20 reference strategy   : random"
        )

        print(
            "Day 21 experiment strategy  : random_multi_seed"
        )

        print(
            "-" * 72
        )

        print(
            "Day 20 coverage             :",
            f"{reference_coverage:.2f}%"
        )

        print(
            "Day 21 average coverage     :",
            f"{day21_average_coverage:.2f}%"
        )

        print(
            "Coverage difference         :",
            f"{coverage_difference:+.2f} percentage points"
        )

        print(
            "-" * 72
        )

        print(
            "Day 20 stimulus cycles      :",
            reference_cycles
        )

        print(
            "Day 21 transactions/run     :",
            day21_transactions_per_run
        )

        print(
            "Day 21 number of runs       :",
            day21_values[
                "number_of_runs"
            ]
        )

        print(
            "Day 21 total transactions   :",
            day21_values[
                "total_transactions"
            ]
        )

        print(
            "-" * 72
        )

        print(
            "Day 20 redundancy           :",
            f"{reference_redundancy:.2f}%"
        )

        print(
            "Day 21 average redundancy   :",
            f"{day21_average_redundancy:.2f}%"
        )

        print(
            "Redundancy difference       :",
            f"{redundancy_difference:+.2f} percentage points"
        )

        print(
            "-" * 72
        )

        print(
            "Day 20 unique signatures    :",
            reference_unique
        )

        print(
            "Day 21 avg unique signatures:",
            f"{day21_average_unique:.2f}"
        )

        print(
            "-" * 72
        )

        print(
            "Day 21 passed runs          :",
            day21_values[
                "passed_runs"
            ]
        )

        print(
            "Day 21 failed runs          :",
            day21_values[
                "failed_runs"
            ]
        )

        print(
            "Day 21 total failed checks  :",
            day21_values[
                "total_failed_checks"
            ]
        )

        print(
            "-" * 72
        )

        print(
            "Output                      :",
            OUTPUT_FILE.relative_to(
                ROOT
            )
        )

        print(
            "=" * 72
        )

        print(
            "DAY 21 REFERENCE COMPARISON: PASS"
        )


        return 0


    except (
        FileNotFoundError,
        ValueError,
        KeyError,
        TypeError,
        OSError,
        statistics.StatisticsError
    ) as exc:

        print(
            "DAY 21 REFERENCE COMPARISON: FAIL"
        )

        print(
            f"ERROR: {exc}"
        )

        return 1


# ============================================================
# PROGRAM ENTRY
# ============================================================

if __name__ == "__main__":

    sys.exit(
        main()
    )
