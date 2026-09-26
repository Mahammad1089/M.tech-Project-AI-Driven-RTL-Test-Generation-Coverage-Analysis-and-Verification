#!/usr/bin/env python3

"""
Day 21 - Multi-Seed FIFO Experiment Statistics
===============================================

Project:
AI-Driven RTL Test Generation,
Coverage Analysis and Verification

Purpose:
- Read the validated Day-21 multi-seed experiment results.
- Calculate descriptive statistics across all runs.
- Use the CURRENT Day-21 JSON schema.
- Avoid obsolete keys such as "cycles_per_run".
- Save a report-friendly statistics JSON file.

Input:
    results/fifo/day21/day21_experiment_summary.json

Fallback input:
    results/fifo/day21/multi_seed_results.json

Output:
    results/fifo/day21/day21_statistics.json
"""

import json
import math
import statistics
import sys
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

DAY21_DIR = (
    ROOT
    / "results"
    / "fifo"
    / "day21"
)

PRIMARY_SUMMARY = (
    DAY21_DIR
    / "day21_experiment_summary.json"
)

FALLBACK_SUMMARY = (
    DAY21_DIR
    / "multi_seed_results.json"
)

OUTPUT_FILE = (
    DAY21_DIR
    / "day21_statistics.json"
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
            "Experiment summary must contain a JSON object."
        )

    return data


def save_json(
    path,
    data
):

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
# SAFE CONVERSION
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
# SUMMARY FILE SELECTION
# ============================================================

def select_summary_file():

    if PRIMARY_SUMMARY.exists():

        return PRIMARY_SUMMARY


    if FALLBACK_SUMMARY.exists():

        return FALLBACK_SUMMARY


    raise FileNotFoundError(
        "Neither day21_experiment_summary.json "
        "nor multi_seed_results.json was found."
    )


# ============================================================
# BASIC STATISTICS
# ============================================================

def calculate_numeric_statistics(values):

    if not values:

        return {
            "count": 0,
            "mean": 0.0,
            "minimum": 0.0,
            "maximum": 0.0,
            "median": 0.0,
            "population_stddev": 0.0,
        }


    numeric_values = [
        float(value)
        for value in values
    ]


    if len(numeric_values) > 1:

        population_stddev = (
            statistics.pstdev(
                numeric_values
            )
        )

    else:

        population_stddev = 0.0


    return {

        "count":
            len(
                numeric_values
            ),

        "mean":
            round(
                statistics.mean(
                    numeric_values
                ),
                4
            ),

        "minimum":
            round(
                min(
                    numeric_values
                ),
                4
            ),

        "maximum":
            round(
                max(
                    numeric_values
                ),
                4
            ),

        "median":
            round(
                statistics.median(
                    numeric_values
                ),
                4
            ),

        "population_stddev":
            round(
                population_stddev,
                4
            ),
    }


# ============================================================
# MAIN
# ============================================================

def main():

    try:

        summary_file = (
            select_summary_file()
        )

        data = load_json(
            summary_file
        )


        # ----------------------------------------------------
        # Current Day-21 schema
        # ----------------------------------------------------

        number_of_runs = safe_int(
            data.get(
                "number_of_runs",
                data.get(
                    "total_runs",
                    0
                )
            )
        )


        # IMPORTANT:
        # Current field is transactions_per_run.
        #
        # cycles_per_run is kept only as a fallback for
        # compatibility with an older schema.
        # ----------------------------------------------------

        transactions_per_run = safe_int(
            data.get(
                "transactions_per_run",
                data.get(
                    "cycles_per_run",
                    data.get(
                        "random_cycles",
                        0
                    )
                )
            )
        )


        base_seed = data.get(
            "base_seed"
        )


        passed_runs = safe_int(
            data.get(
                "passed_runs",
                0
            )
        )


        failed_runs = safe_int(
            data.get(
                "failed_runs",
                0
            )
        )


        all_simulations_passed = data.get(
            "all_simulations_passed"
        )


        runs = data.get(
            "runs",
            []
        )


        if not isinstance(
            runs,
            list
        ):

            raise ValueError(
                "'runs' must be a list."
            )


        if not runs:

            raise ValueError(
                "No Day 21 run records were found."
            )


        if number_of_runs == 0:

            number_of_runs = len(
                runs
            )


        # ====================================================
        # COLLECT VALUES FROM ALL RUNS
        # ====================================================

        coverage_values = []

        redundancy_values = []

        runtime_values = []

        total_check_values = []

        unique_signature_values = []

        redundant_cycle_values = []

        transaction_values = []

        seeds = []

        measured_passed_runs = 0

        measured_failed_runs = 0


        for run in runs:

            if not isinstance(
                run,
                dict
            ):

                continue


            # ------------------------------------------------
            # Seed
            # ------------------------------------------------

            seed = run.get(
                "seed"
            )

            if seed is not None:

                seeds.append(
                    safe_int(
                        seed
                    )
                )


            # ------------------------------------------------
            # Transactions
            # ------------------------------------------------

            transactions = safe_int(
                run.get(
                    "transactions",
                    transactions_per_run
                )
            )

            transaction_values.append(
                transactions
            )


            # ------------------------------------------------
            # Coverage
            # ------------------------------------------------

            coverage = safe_float(
                run.get(
                    "coverage_percent",
                    0.0
                )
            )

            coverage_values.append(
                coverage
            )


            # ------------------------------------------------
            # Redundancy
            # ------------------------------------------------

            redundancy = safe_float(
                run.get(
                    "redundancy_percent",
                    0.0
                )
            )

            redundancy_values.append(
                redundancy
            )


            # ------------------------------------------------
            # Runtime
            # ------------------------------------------------

            runtime = safe_float(
                run.get(
                    "runtime_seconds",
                    0.0
                )
            )

            runtime_values.append(
                runtime
            )


            # ------------------------------------------------
            # Total checks
            # ------------------------------------------------

            total_checks = safe_int(
                run.get(
                    "total_checks",
                    0
                )
            )

            total_check_values.append(
                total_checks
            )


            # ------------------------------------------------
            # Unique signatures
            # ------------------------------------------------

            unique_signatures = safe_int(
                run.get(
                    "unique_behavior_signatures",
                    0
                )
            )

            unique_signature_values.append(
                unique_signatures
            )


            # ------------------------------------------------
            # Redundant cycles
            # ------------------------------------------------

            redundant_cycles = safe_int(
                run.get(
                    "redundant_cycles",
                    0
                )
            )

            redundant_cycle_values.append(
                redundant_cycles
            )


            # ------------------------------------------------
            # PASS / FAIL
            # ------------------------------------------------

            simulation_status = str(
                run.get(
                    "simulation_status",
                    ""
                )
            ).strip().upper()


            failed_checks = safe_int(
                run.get(
                    "failed_checks",
                    -1
                ),
                -1
            )


            if (
                simulation_status == "PASS"
                and failed_checks == 0
            ):

                measured_passed_runs += 1

            else:

                measured_failed_runs += 1


        # ====================================================
        # STATISTICS
        # ====================================================

        coverage_statistics = (
            calculate_numeric_statistics(
                coverage_values
            )
        )


        redundancy_statistics = (
            calculate_numeric_statistics(
                redundancy_values
            )
        )


        runtime_statistics = (
            calculate_numeric_statistics(
                runtime_values
            )
        )


        check_statistics = (
            calculate_numeric_statistics(
                total_check_values
            )
        )


        unique_signature_statistics = (
            calculate_numeric_statistics(
                unique_signature_values
            )
        )


        redundant_cycle_statistics = (
            calculate_numeric_statistics(
                redundant_cycle_values
            )
        )


        transaction_statistics = (
            calculate_numeric_statistics(
                transaction_values
            )
        )


        # ====================================================
        # PASS RATE
        # ====================================================

        if number_of_runs > 0:

            pass_rate_percent = round(
                (
                    measured_passed_runs
                    / number_of_runs
                )
                * 100.0,
                2
            )

        else:

            pass_rate_percent = 0.0


        # ====================================================
        # COVERAGE DISTRIBUTION
        # ====================================================

        runs_at_100 = sum(
            1
            for value in coverage_values
            if abs(
                value
                - 100.0
            ) < 0.0001
        )


        runs_at_or_above_90 = sum(
            1
            for value in coverage_values
            if value >= 90.0
        )


        runs_below_90 = sum(
            1
            for value in coverage_values
            if value < 90.0
        )


        # ====================================================
        # TOTAL EXPERIMENT COUNTERS
        # ====================================================

        total_transactions = sum(
            transaction_values
        )


        total_checks = sum(
            total_check_values
        )


        total_redundant_cycles = sum(
            redundant_cycle_values
        )


        # ====================================================
        # RESULT OBJECT
        # ====================================================

        statistics_data = {

            "day":
                21,

            "dut":
                data.get(
                    "dut",
                    "fifo"
                ),

            "strategy":
                data.get(
                    "strategy",
                    "random_multi_seed"
                ),

            "source_summary":
                summary_file.relative_to(
                    ROOT
                ).as_posix(),

            "experiment_configuration": {

                "number_of_runs":
                    number_of_runs,

                "transactions_per_run":
                    transactions_per_run,

                "base_seed":
                    base_seed,

                "seeds":
                    seeds,
            },

            "run_status": {

                "passed_runs":
                    measured_passed_runs,

                "failed_runs":
                    measured_failed_runs,

                "pass_rate_percent":
                    pass_rate_percent,

                "all_simulations_passed":
                    (
                        measured_failed_runs
                        == 0
                        and measured_passed_runs
                        == number_of_runs
                    ),
            },

            "coverage_statistics":
                coverage_statistics,

            "coverage_distribution": {

                "runs_at_100_percent":
                    runs_at_100,

                "runs_at_or_above_90_percent":
                    runs_at_or_above_90,

                "runs_below_90_percent":
                    runs_below_90,
            },

            "redundancy_statistics":
                redundancy_statistics,

            "runtime_statistics_seconds":
                runtime_statistics,

            "verification_check_statistics":
                check_statistics,

            "unique_behavior_signature_statistics":
                unique_signature_statistics,

            "redundant_cycle_statistics":
                redundant_cycle_statistics,

            "transaction_statistics":
                transaction_statistics,

            "totals": {

                "total_transactions":
                    total_transactions,

                "total_verification_checks":
                    total_checks,

                "total_redundant_cycles":
                    total_redundant_cycles,
            },

            "measured_values": {

                "coverage_percent_by_run":
                    coverage_values,

                "redundancy_percent_by_run":
                    redundancy_values,

                "runtime_seconds_by_run":
                    runtime_values,

                "total_checks_by_run":
                    total_check_values,

                "unique_behavior_signatures_by_run":
                    unique_signature_values,

                "redundant_cycles_by_run":
                    redundant_cycle_values,
            },

            "rtl_modified":
                False,

            "statistics_complete":
                True,
        }


        # ====================================================
        # SAVE RESULT
        # ====================================================

        save_json(
            OUTPUT_FILE,
            statistics_data
        )


        # ====================================================
        # PRINT RESULTS
        # ====================================================

        print(
            "=" * 70
        )

        print(
            "DAY 21 FIFO MULTI-SEED STATISTICS"
        )

        print(
            "=" * 70
        )

        print(
            "Number of runs               :",
            number_of_runs
        )

        print(
            "Transactions per run         :",
            transactions_per_run
        )

        print(
            "Total transactions           :",
            total_transactions
        )

        print(
            "Passed runs                  :",
            measured_passed_runs
        )

        print(
            "Failed runs                  :",
            measured_failed_runs
        )

        print(
            "Pass rate                    :",
            f"{pass_rate_percent:.2f}%"
        )

        print(
            "-" * 70
        )

        print(
            "Average coverage             :",
            f"{coverage_statistics['mean']:.2f}%"
        )

        print(
            "Minimum coverage             :",
            f"{coverage_statistics['minimum']:.2f}%"
        )

        print(
            "Maximum coverage             :",
            f"{coverage_statistics['maximum']:.2f}%"
        )

        print(
            "Median coverage              :",
            f"{coverage_statistics['median']:.2f}%"
        )

        print(
            "Coverage standard deviation  :",
            f"{coverage_statistics['population_stddev']:.2f}%"
        )

        print(
            "-" * 70
        )

        print(
            "Runs with 100% coverage      :",
            runs_at_100
        )

        print(
            "Runs with >=90% coverage     :",
            runs_at_or_above_90
        )

        print(
            "Runs with <90% coverage      :",
            runs_below_90
        )

        print(
            "-" * 70
        )

        print(
            "Average redundancy           :",
            f"{redundancy_statistics['mean']:.2f}%"
        )

        print(
            "Minimum redundancy           :",
            f"{redundancy_statistics['minimum']:.2f}%"
        )

        print(
            "Maximum redundancy           :",
            f"{redundancy_statistics['maximum']:.2f}%"
        )

        print(
            "Redundancy std. deviation    :",
            f"{redundancy_statistics['population_stddev']:.2f}%"
        )

        print(
            "-" * 70
        )

        print(
            "Average runtime              :",
            f"{runtime_statistics['mean']:.6f} s"
        )

        print(
            "Average unique signatures    :",
            f"{unique_signature_statistics['mean']:.2f}"
        )

        print(
            "Average verification checks  :",
            f"{check_statistics['mean']:.2f}"
        )

        print(
            "-" * 70
        )

        print(
            "Statistics output            :",
            OUTPUT_FILE.relative_to(
                ROOT
            )
        )

        print(
            "=" * 70
        )

        print(
            "DAY 21 STATISTICS: PASS"
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
            "DAY 21 STATISTICS: FAIL"
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
