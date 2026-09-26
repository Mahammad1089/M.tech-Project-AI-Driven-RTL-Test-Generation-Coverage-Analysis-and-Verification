#!/usr/bin/env python3

"""
Day 21 - Results to CSV
=======================

Project:
AI-Driven RTL Test Generation,
Coverage Analysis and Verification

Purpose:
- Read the current Day-21 multi-seed experiment summary.
- Convert all measured run results into CSV format.
- Support the CURRENT schema using "run".
- Retain compatibility with older "run_index" schema.
- Save report/thesis-ready CSV data.

Primary input:
    results/fifo/day21/day21_experiment_summary.json

Fallback:
    results/fifo/day21/multi_seed_results.json

Outputs:
    results/fifo/day21/day21_results.csv
    results/final_results.csv
"""

import csv
import json
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

PRIMARY_INPUT = (
    DAY21_DIR
    / "day21_experiment_summary.json"
)

FALLBACK_INPUT = (
    DAY21_DIR
    / "multi_seed_results.json"
)

DAY21_CSV = (
    DAY21_DIR
    / "day21_results.csv"
)

FINAL_RESULTS_CSV = (
    ROOT
    / "results"
    / "final_results.csv"
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
            "Day 21 results must contain a JSON object."
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
        "Neither day21_experiment_summary.json nor "
        "multi_seed_results.json exists."
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
# FORMAT MISSING POINTS
# ============================================================

def format_missing_points(value):

    if value is None:
        return ""

    if isinstance(
        value,
        list
    ):

        return ";".join(
            str(item)
            for item in value
        )

    return str(value)


# ============================================================
# FORMAT BOOLEAN
# ============================================================

def format_boolean(value):

    if value is True:
        return "true"

    if value is False:
        return "false"

    return ""


# ============================================================
# NORMALIZE ONE RUN
# ============================================================

def normalize_run(
    run,
    fallback_index,
    transactions_per_run
):

    if not isinstance(
        run,
        dict
    ):

        raise ValueError(
            f"Run {fallback_index} is not a JSON object."
        )


    # --------------------------------------------------------
    # IMPORTANT FIX:
    #
    # Current schema:
    #     "run"
    #
    # Old schema:
    #     "run_index"
    # --------------------------------------------------------

    run_number = safe_int(
        run.get(
            "run",
            run.get(
                "run_index",
                fallback_index
            )
        ),
        fallback_index
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
            run.get(
                "cycles",
                transactions_per_run
            )
        ),
        transactions_per_run
    )


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


    coverage_percent = safe_float(
        run.get(
            "coverage_percent",
            0.0
        )
    )


    covered_points = safe_int(
        run.get(
            "covered_points",
            run.get(
                "covered_coverage_points",
                0
            )
        )
    )


    missing_points = format_missing_points(
        run.get(
            "missing_points",
            []
        )
    )


    unique_behavior_signatures = safe_int(
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


    redundancy_percent = safe_float(
        run.get(
            "redundancy_percent",
            0.0
        )
    )


    runtime_seconds = safe_float(
        run.get(
            "runtime_seconds",
            0.0
        )
    )


    pass_marker_found = format_boolean(
        run.get(
            "pass_marker_found"
        )
    )


    return {

        "day":
            21,

        "dut":
            "fifo",

        "strategy":
            "random",

        "run":
            run_number,

        "seed":
            seed,

        "transactions":
            transactions,

        "simulation_status":
            simulation_status,

        "total_checks":
            total_checks,

        "passed_checks":
            passed_checks,

        "failed_checks":
            failed_checks,

        "coverage_percent":
            round(
                coverage_percent,
                2
            ),

        "covered_points":
            covered_points,

        "missing_points":
            missing_points,

        "unique_behavior_signatures":
            unique_behavior_signatures,

        "redundant_cycles":
            redundant_cycles,

        "redundancy_percent":
            round(
                redundancy_percent,
                2
            ),

        "runtime_seconds":
            round(
                runtime_seconds,
                6
            ),

        "pass_marker_found":
            pass_marker_found,
    }


# ============================================================
# WRITE CSV
# ============================================================

def write_csv(
    path,
    rows
):

    path.parent.mkdir(
        parents=True,
        exist_ok=True
    )


    fieldnames = [

        "day",
        "dut",
        "strategy",

        "run",
        "seed",
        "transactions",

        "simulation_status",

        "total_checks",
        "passed_checks",
        "failed_checks",

        "coverage_percent",
        "covered_points",
        "missing_points",

        "unique_behavior_signatures",

        "redundant_cycles",
        "redundancy_percent",

        "runtime_seconds",

        "pass_marker_found",
    ]


    with path.open(
        "w",
        encoding="utf-8",
        newline=""
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()

        writer.writerows(
            rows
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


        # ----------------------------------------------------
        # Current schema
        # ----------------------------------------------------

        runs = data.get(
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
                "No Day 21 experiment runs were found."
            )


        number_of_runs = safe_int(
            data.get(
                "number_of_runs",
                data.get(
                    "total_runs",
                    len(runs)
                )
            ),
            len(runs)
        )


        # ----------------------------------------------------
        # Current field:
        # transactions_per_run
        #
        # Old fallbacks:
        # cycles_per_run
        # random_cycles
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


        normalized_rows = []


        for index, run in enumerate(
            runs,
            start=1
        ):

            normalized_rows.append(
                normalize_run(
                    run,
                    index,
                    transactions_per_run
                )
            )


        # ----------------------------------------------------
        # Validate number of runs
        # ----------------------------------------------------

        if (
            number_of_runs
            != len(
                normalized_rows
            )
        ):

            raise ValueError(
                "Run-count mismatch: "
                f"summary says {number_of_runs}, "
                f"but {len(normalized_rows)} "
                "run records were found."
            )


        # ----------------------------------------------------
        # Write Day-21 specific CSV
        # ----------------------------------------------------

        write_csv(
            DAY21_CSV,
            normalized_rows
        )


        # ----------------------------------------------------
        # Also generate project-level final_results.csv
        #
        # This satisfies the Day-21 master-plan deliverable.
        # ----------------------------------------------------

        write_csv(
            FINAL_RESULTS_CSV,
            normalized_rows
        )


        # ====================================================
        # VERIFY RESULTS
        # ====================================================

        passed_runs = sum(
            1
            for row in normalized_rows
            if (
                row[
                    "simulation_status"
                ]
                == "PASS"
                and row[
                    "failed_checks"
                ]
                == 0
            )
        )


        failed_runs = (
            len(
                normalized_rows
            )
            - passed_runs
        )


        coverage_values = [
            row[
                "coverage_percent"
            ]
            for row in normalized_rows
        ]


        redundancy_values = [
            row[
                "redundancy_percent"
            ]
            for row in normalized_rows
        ]


        average_coverage = round(
            sum(
                coverage_values
            )
            / len(
                coverage_values
            ),
            2
        )


        average_redundancy = round(
            sum(
                redundancy_values
            )
            / len(
                redundancy_values
            ),
            2
        )


        # ====================================================
        # PRINT SUMMARY
        # ====================================================

        print(
            "=" * 68
        )

        print(
            "DAY 21 CSV GENERATION"
        )

        print(
            "=" * 68
        )

        print(
            "Source JSON              :",
            input_file.relative_to(
                ROOT
            )
        )

        print(
            "Runs exported            :",
            len(
                normalized_rows
            )
        )

        print(
            "Transactions per run     :",
            transactions_per_run
        )

        print(
            "Passed runs              :",
            passed_runs
        )

        print(
            "Failed runs              :",
            failed_runs
        )

        print(
            "Average coverage         :",
            f"{average_coverage:.2f}%"
        )

        print(
            "Average redundancy       :",
            f"{average_redundancy:.2f}%"
        )

        print(
            "-" * 68
        )

        print(
            "Day 21 CSV               :",
            DAY21_CSV.relative_to(
                ROOT
            )
        )

        print(
            "Final results CSV         :",
            FINAL_RESULTS_CSV.relative_to(
                ROOT
            )
        )

        print(
            "=" * 68
        )

        print(
            "DAY 21 CSV GENERATION: PASS"
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
            "DAY 21 CSV GENERATION: FAIL"
        )

        print(
            f"ERROR: {exc}"
        )

        return 1


if __name__ == "__main__":

    sys.exit(
        main()
    )
