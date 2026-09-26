#!/usr/bin/env python3

"""
Day 21 - Multi-Seed Experiment Validator

Project:
AI-Driven RTL Test Generation,
Coverage Analysis and Verification

Purpose:
- Validate the actual Day-21 multi-seed experiment results.
- Support the current Day-21 summary JSON schema.
- Avoid obsolete fields such as "random_cycles".
- Confirm all runs completed successfully.
- Confirm verification counters are consistent.
- Confirm measured coverage values are valid.
"""

import json
import sys
from pathlib import Path


# ============================================================
# PROJECT PATHS
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

LEGACY_SUMMARY = (
    DAY21_DIR
    / "multi_seed_results.json"
)

RESULTS_CSV = (
    DAY21_DIR
    / "day21_experiment_results.csv"
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

    if not isinstance(data, dict):

        raise ValueError(
            "Day 21 summary must contain a JSON object."
        )

    return data


# ============================================================
# SELECT SUMMARY FILE
# ============================================================

def find_summary_file():

    if PRIMARY_SUMMARY.exists():
        return PRIMARY_SUMMARY

    if LEGACY_SUMMARY.exists():
        return LEGACY_SUMMARY

    raise FileNotFoundError(
        "Neither day21_experiment_summary.json nor "
        "multi_seed_results.json exists."
    )


# ============================================================
# SAFE INTEGER
# ============================================================

def safe_int(value, default=0):

    try:
        return int(value)

    except (
        TypeError,
        ValueError
    ):
        return default


# ============================================================
# SAFE FLOAT
# ============================================================

def safe_float(value, default=0.0):

    try:
        return float(value)

    except (
        TypeError,
        ValueError
    ):
        return default


# ============================================================
# PASS/FAIL FORMATTER
# ============================================================

def status_text(value):

    return (
        "PASS"
        if value
        else "FAIL"
    )


# ============================================================
# VALIDATE ONE RUN
# ============================================================

def validate_run(
    run,
    expected_run_number=None
):

    errors = []

    if not isinstance(run, dict):

        return [
            "Run entry is not a JSON object."
        ]


    run_number = safe_int(
        run.get(
            "run",
            expected_run_number
        ),
        0
    )


    simulation_status = str(
        run.get(
            "simulation_status",
            ""
        )
    ).strip().upper()


    total_checks = run.get(
        "total_checks"
    )

    passed_checks = run.get(
        "passed_checks"
    )

    failed_checks = run.get(
        "failed_checks"
    )


    if total_checks is None:

        errors.append(
            f"Run {run_number}: total_checks missing."
        )

    if passed_checks is None:

        errors.append(
            f"Run {run_number}: passed_checks missing."
        )

    if failed_checks is None:

        errors.append(
            f"Run {run_number}: failed_checks missing."
        )


    total_checks = safe_int(
        total_checks,
        -1
    )

    passed_checks = safe_int(
        passed_checks,
        -1
    )

    failed_checks = safe_int(
        failed_checks,
        -1
    )


    if simulation_status != "PASS":

        errors.append(
            f"Run {run_number}: "
            f"simulation_status={simulation_status!r}, "
            "expected PASS."
        )


    if failed_checks != 0:

        errors.append(
            f"Run {run_number}: "
            f"failed_checks={failed_checks}, "
            "expected 0."
        )


    if (
        total_checks >= 0
        and passed_checks >= 0
        and passed_checks != total_checks
    ):

        errors.append(
            f"Run {run_number}: "
            f"passed_checks={passed_checks} "
            f"does not equal total_checks={total_checks}."
        )


    coverage_percent = safe_float(
        run.get(
            "coverage_percent"
        ),
        -1.0
    )


    if not (
        0.0
        <= coverage_percent
        <= 100.0
    ):

        errors.append(
            f"Run {run_number}: invalid "
            f"coverage_percent={coverage_percent}."
        )


    redundancy_percent = safe_float(
        run.get(
            "redundancy_percent",
            0.0
        ),
        -1.0
    )


    if not (
        0.0
        <= redundancy_percent
        <= 100.0
    ):

        errors.append(
            f"Run {run_number}: invalid "
            f"redundancy_percent={redundancy_percent}."
        )


    transactions = safe_int(
        run.get(
            "transactions",
            0
        ),
        0
    )


    if transactions <= 0:

        errors.append(
            f"Run {run_number}: "
            "transaction count must be greater than zero."
        )


    return errors


# ============================================================
# MAIN VALIDATION
# ============================================================

def main():

    try:

        summary_file = (
            find_summary_file()
        )

        data = load_json(
            summary_file
        )


        # ====================================================
        # CURRENT DAY-21 SCHEMA
        # ====================================================

        number_of_runs = safe_int(
            data.get(
                "number_of_runs",
                data.get(
                    "total_runs",
                    0
                )
            ),
            0
        )


        transactions_per_run = safe_int(
            data.get(
                "transactions_per_run",
                data.get(
                    "random_cycles",
                    data.get(
                        "cycles_per_run",
                        0
                    )
                )
            ),
            0
        )


        passed_runs = safe_int(
            data.get(
                "passed_runs",
                0
            ),
            0
        )


        failed_runs = safe_int(
            data.get(
                "failed_runs",
                0
            ),
            0
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
                "'runs' must be a JSON list."
            )


        errors = []


        # ====================================================
        # BASIC SUMMARY VALIDATION
        # ====================================================

        if number_of_runs <= 0:

            errors.append(
                "number_of_runs is missing or invalid."
            )


        if transactions_per_run <= 0:

            errors.append(
                "transactions_per_run is missing or invalid."
            )


        if len(runs) != number_of_runs:

            errors.append(
                "Run-count mismatch: "
                f"number_of_runs={number_of_runs}, "
                f"actual run entries={len(runs)}."
            )


        if (
            passed_runs
            + failed_runs
            != number_of_runs
        ):

            errors.append(
                "Summary run counts inconsistent: "
                f"passed_runs({passed_runs}) + "
                f"failed_runs({failed_runs}) != "
                f"number_of_runs({number_of_runs})."
            )


        # ====================================================
        # VALIDATE EACH RUN
        # ====================================================

        for index, run in enumerate(
            runs,
            start=1
        ):

            run_errors = validate_run(
                run,
                expected_run_number=index
            )

            errors.extend(
                run_errors
            )


        # ====================================================
        # RECOMPUTE PASS COUNTS
        # ====================================================

        actual_passed_runs = 0

        for run in runs:

            if not isinstance(
                run,
                dict
            ):
                continue


            simulation_status = str(
                run.get(
                    "simulation_status",
                    ""
                )
            ).strip().upper()


            failed_checks = safe_int(
                run.get(
                    "failed_checks"
                ),
                -1
            )


            total_checks = safe_int(
                run.get(
                    "total_checks"
                ),
                -1
            )


            passed_checks = safe_int(
                run.get(
                    "passed_checks"
                ),
                -1
            )


            if (
                simulation_status == "PASS"
                and failed_checks == 0
                and total_checks >= 0
                and passed_checks == total_checks
            ):

                actual_passed_runs += 1


        actual_failed_runs = (
            len(runs)
            - actual_passed_runs
        )


        if (
            passed_runs
            != actual_passed_runs
        ):

            errors.append(
                "passed_runs mismatch: "
                f"summary={passed_runs}, "
                f"measured={actual_passed_runs}."
            )


        if (
            failed_runs
            != actual_failed_runs
        ):

            errors.append(
                "failed_runs mismatch: "
                f"summary={failed_runs}, "
                f"measured={actual_failed_runs}."
            )


        # ====================================================
        # CHECK ALL-SIMULATIONS FLAG
        # ====================================================

        all_simulations_passed = data.get(
            "all_simulations_passed"
        )


        expected_all_passed = (
            number_of_runs > 0
            and actual_passed_runs
            == number_of_runs
        )


        if (
            all_simulations_passed
            is not None
            and bool(
                all_simulations_passed
            )
            != expected_all_passed
        ):

            errors.append(
                "all_simulations_passed does not "
                "match measured run results."
            )


        # ====================================================
        # COVERAGE SUMMARY VALIDATION
        # ====================================================

        coverage_values = []

        redundancy_values = []


        for run in runs:

            if not isinstance(
                run,
                dict
            ):
                continue


            coverage = safe_float(
                run.get(
                    "coverage_percent"
                ),
                -1.0
            )


            if coverage >= 0:

                coverage_values.append(
                    coverage
                )


            redundancy = safe_float(
                run.get(
                    "redundancy_percent"
                ),
                -1.0
            )


            if redundancy >= 0:

                redundancy_values.append(
                    redundancy
                )


        if coverage_values:

            measured_average_coverage = round(
                sum(
                    coverage_values
                )
                / len(
                    coverage_values
                ),
                2
            )


            recorded_average_coverage = (
                data.get(
                    "average_coverage_percent"
                )
            )


            if recorded_average_coverage is not None:

                recorded_average_coverage = (
                    safe_float(
                        recorded_average_coverage
                    )
                )


                if abs(
                    recorded_average_coverage
                    - measured_average_coverage
                ) > 0.02:

                    errors.append(
                        "Average coverage mismatch: "
                        f"summary="
                        f"{recorded_average_coverage}, "
                        f"measured="
                        f"{measured_average_coverage}."
                    )


        else:

            measured_average_coverage = 0.0


        if redundancy_values:

            measured_average_redundancy = round(
                sum(
                    redundancy_values
                )
                / len(
                    redundancy_values
                ),
                2
            )

        else:

            measured_average_redundancy = 0.0


        # ====================================================
        # CHECK RESULTS CSV
        # ====================================================

        csv_exists = (
            RESULTS_CSV.exists()
        )


        if not csv_exists:

            errors.append(
                "Day 21 experiment results CSV "
                "is missing."
            )


        # ====================================================
        # FINAL RESULT
        # ====================================================

        validation_pass = (
            len(errors) == 0
            and actual_passed_runs
            == number_of_runs
            and actual_failed_runs == 0
        )


        print(
            "=" * 68
        )

        print(
            "DAY 21 EXPERIMENT VALIDATION"
        )

        print(
            "=" * 68
        )

        print(
            "Summary file             :",
            summary_file.relative_to(
                ROOT
            )
        )

        print(
            "Number of runs           :",
            number_of_runs
        )

        print(
            "Transactions per run     :",
            transactions_per_run
        )

        print(
            "Passed runs              :",
            actual_passed_runs
        )

        print(
            "Failed runs              :",
            actual_failed_runs
        )

        print(
            "Average coverage         :",
            f"{measured_average_coverage:.2f}%"
        )

        print(
            "Average redundancy       :",
            f"{measured_average_redundancy:.2f}%"
        )

        print(
            "Results CSV exists       :",
            csv_exists
        )

        print(
            "-" * 68
        )


        if errors:

            print(
                "VALIDATION ISSUES:"
            )

            for error in errors:

                print(
                    " -",
                    error
                )


        print(
            "-" * 68
        )

        print(
            "DAY 21 VALIDATION STATUS :",
            status_text(
                validation_pass
            )
        )

        print(
            "=" * 68
        )


        if validation_pass:

            print(
                "DAY 21 EXPERIMENT VALIDATION: PASS"
            )

            return 0


        print(
            "DAY 21 EXPERIMENT VALIDATION: FAIL"
        )

        return 1


    except (
        FileNotFoundError,
        ValueError,
        TypeError,
        OSError
    ) as exc:

        print(
            "DAY 21 EXPERIMENT VALIDATION: FAIL"
        )

        print(
            f"ERROR: {exc}"
        )

        return 1


if __name__ == "__main__":

    sys.exit(
        main()
    )
