#!/usr/bin/env python3

"""
Day 21 - Final FIFO Experiment Summary
======================================

Reads the validated Day-21 multi-seed experiment results
and generates a clean final summary.

Current schema supported:
    run
    seed
    transactions
    simulation_status
    total_checks
    passed_checks
    failed_checks
    coverage_percent
    unique_behavior_signatures
    redundant_cycles
    redundancy_percent
    runtime_seconds

Older field names are also accepted where possible.
"""

import json
import statistics
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

DAY21_DIR = ROOT / "results" / "fifo" / "day21"

PRIMARY_INPUT = (
    DAY21_DIR
    / "day21_experiment_summary.json"
)

FALLBACK_INPUT = (
    DAY21_DIR
    / "multi_seed_results.json"
)

OUTPUT_FILE = (
    DAY21_DIR
    / "day21_final_summary.json"
)


def load_json(path):
    if not path.exists():
        raise FileNotFoundError(
            f"Required file not found: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8"
    ) as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError(
            "Day 21 input must contain a JSON object."
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


def safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def select_input():
    if PRIMARY_INPUT.exists():
        return PRIMARY_INPUT

    if FALLBACK_INPUT.exists():
        return FALLBACK_INPUT

    raise FileNotFoundError(
        "Neither day21_experiment_summary.json "
        "nor multi_seed_results.json exists."
    )


def main():
    try:
        input_file = select_input()

        data = load_json(
            input_file
        )

        runs = data.get(
            "runs",
            []
        )

        if not isinstance(runs, list):
            raise ValueError(
                "'runs' must be a JSON list."
            )

        if not runs:
            raise ValueError(
                "No Day 21 runs were found."
            )


        number_of_runs = safe_int(
            data.get(
                "number_of_runs",
                data.get(
                    "run_count",
                    len(runs)
                )
            ),
            len(runs)
        )


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


        passed_runs = 0
        failed_runs = 0

        total_checks_all = 0
        passed_checks_all = 0
        failed_checks_all = 0

        coverage_values = []
        redundancy_values = []
        runtime_values = []
        unique_values = []
        redundant_cycle_values = []

        seeds = []

        run_summaries = []


        for index, run in enumerate(
            runs,
            start=1
        ):
            if not isinstance(run, dict):
                raise ValueError(
                    f"Run {index} is not a JSON object."
                )


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


            transactions = safe_int(
                run.get(
                    "transactions",
                    transactions_per_run
                ),
                transactions_per_run
            )


            # ================================================
            # IMPORTANT FIX
            #
            # Current schema:
            #     simulation_status
            #
            # Old schema fallback:
            #     status
            # ================================================

            simulation_status = str(
                run.get(
                    "simulation_status",
                    run.get(
                        "status",
                        "UNKNOWN"
                    )
                )
            ).strip().upper()


            total_checks = safe_int(
                run.get(
                    "total_checks",
                    0
                )
            )


            passed_checks = safe_int(
                run.get(
                    "passed_checks",
                    0
                )
            )


            failed_checks = safe_int(
                run.get(
                    "failed_checks",
                    0
                )
            )


            coverage = safe_float(
                run.get(
                    "coverage_percent",
                    0.0
                )
            )


            redundancy = safe_float(
                run.get(
                    "redundancy_percent",
                    0.0
                )
            )


            runtime = safe_float(
                run.get(
                    "runtime_seconds",
                    0.0
                )
            )


            unique_signatures = safe_int(
                run.get(
                    "unique_behavior_signatures",
                    0
                )
            )


            redundant_cycles = safe_int(
                run.get(
                    "redundant_cycles",
                    0
                )
            )


            run_pass = (
                simulation_status == "PASS"
                and failed_checks == 0
                and total_checks >= 0
                and passed_checks == total_checks
            )


            if run_pass:
                passed_runs += 1
                normalized_status = "PASS"

            else:
                failed_runs += 1
                normalized_status = "FAIL"


            seeds.append(
                seed
            )

            total_checks_all += total_checks
            passed_checks_all += passed_checks
            failed_checks_all += failed_checks

            coverage_values.append(
                coverage
            )

            redundancy_values.append(
                redundancy
            )

            runtime_values.append(
                runtime
            )

            unique_values.append(
                unique_signatures
            )

            redundant_cycle_values.append(
                redundant_cycles
            )


            run_summaries.append(
                {
                    "run": run_number,
                    "seed": seed,
                    "transactions": transactions,
                    "status": normalized_status,
                    "simulation_status":
                        simulation_status,
                    "total_checks": total_checks,
                    "passed_checks": passed_checks,
                    "failed_checks": failed_checks,
                    "coverage_percent":
                        round(coverage, 2),
                    "unique_behavior_signatures":
                        unique_signatures,
                    "redundant_cycles":
                        redundant_cycles,
                    "redundancy_percent":
                        round(redundancy, 2),
                    "runtime_seconds":
                        round(runtime, 6),
                }
            )


        if len(runs) != number_of_runs:
            raise ValueError(
                "Run count mismatch: "
                f"summary says {number_of_runs}, "
                f"actual runs={len(runs)}."
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


        average_runtime = round(
            statistics.mean(
                runtime_values
            ),
            6
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


        total_transactions = sum(
            run["transactions"]
            for run in run_summaries
        )


        all_runs_passed = (
            passed_runs == number_of_runs
            and failed_runs == 0
        )


        overall_status = (
            "PASS"
            if all_runs_passed
            else "FAIL"
        )


        final_summary = {
            "day": 21,

            "dut": "fifo",

            "experiment":
                "multi_seed_random_verification",

            "status":
                overall_status,

            "number_of_runs":
                number_of_runs,

            "transactions_per_run":
                transactions_per_run,

            "total_transactions":
                total_transactions,

            "seeds":
                seeds,

            "passed_runs":
                passed_runs,

            "failed_runs":
                failed_runs,

            "all_runs_passed":
                all_runs_passed,

            "verification_totals": {
                "total_checks":
                    total_checks_all,

                "passed_checks":
                    passed_checks_all,

                "failed_checks":
                    failed_checks_all,
            },

            "coverage": {
                "average_percent":
                    average_coverage,

                "minimum_percent":
                    minimum_coverage,

                "maximum_percent":
                    maximum_coverage,

                "median_percent":
                    median_coverage,
            },

            "redundancy": {
                "average_percent":
                    average_redundancy,

                "average_redundant_cycles":
                    average_redundant_cycles,
            },

            "runtime": {
                "average_seconds":
                    average_runtime,
            },

            "behavior": {
                "average_unique_signatures":
                    average_unique,
            },

            "source_file":
                input_file.relative_to(
                    ROOT
                ).as_posix(),

            "rtl_modified":
                False,

            "runs":
                run_summaries,
        }


        save_json(
            OUTPUT_FILE,
            final_summary
        )


        print("=" * 70)
        print("DAY 21 FINAL SUMMARY")
        print("=" * 70)

        print(
            "DUT                         : FIFO"
        )

        print(
            "Number of runs              :",
            number_of_runs
        )

        print(
            "Transactions per run        :",
            transactions_per_run
        )

        print(
            "Total transactions          :",
            total_transactions
        )

        print(
            "Passed runs                 :",
            passed_runs
        )

        print(
            "Failed runs                 :",
            failed_runs
        )

        print(
            "Total verification checks   :",
            total_checks_all
        )

        print(
            "Passed verification checks  :",
            passed_checks_all
        )

        print(
            "Failed verification checks  :",
            failed_checks_all
        )

        print("-" * 70)

        print(
            "Average coverage            :",
            f"{average_coverage:.2f}%"
        )

        print(
            "Minimum coverage            :",
            f"{minimum_coverage:.2f}%"
        )

        print(
            "Maximum coverage            :",
            f"{maximum_coverage:.2f}%"
        )

        print(
            "Median coverage             :",
            f"{median_coverage:.2f}%"
        )

        print(
            "Average redundancy          :",
            f"{average_redundancy:.2f}%"
        )

        print(
            "Average unique signatures   :",
            f"{average_unique:.2f}"
        )

        print(
            "Average runtime             :",
            f"{average_runtime:.6f} s"
        )

        print("-" * 70)

        print(
            "Output                      :",
            OUTPUT_FILE.relative_to(
                ROOT
            )
        )

        print(
            "DAY 21 STATUS               :",
            overall_status
        )

        print("=" * 70)


        if all_runs_passed:
            print(
                "DAY 21 SUMMARY: PASS"
            )

            return 0


        print(
            "DAY 21 SUMMARY: FAIL"
        )

        return 1


    except (
        FileNotFoundError,
        ValueError,
        KeyError,
        TypeError,
        OSError,
        statistics.StatisticsError
    ) as exc:

        print(
            "DAY 21 SUMMARY: FAIL"
        )

        print(
            f"ERROR: {exc}"
        )

        return 1


if __name__ == "__main__":
    sys.exit(
        main()
    )
