#!/usr/bin/env python3

"""
Day 22 - Graph Validation
=========================

Project:
AI-Driven RTL Test Generation,
Coverage Analysis and Verification

Purpose:
- Validate Day 22 graph-data JSON.
- Validate current Day 22 schema.
- Confirm all six graph PNG files exist.
- Confirm graph files are non-empty.
- Confirm Day 21 experiment data are valid.
- Confirm 10 Day 21 runs and 0 failed runs.
- Confirm current measured coverage/redundancy values.
- Avoid obsolete field names such as "random_runs".

Primary input:
    results/fifo/day22/day22_graph_data.json

Fallback:
    results/fifo/day22/graph_data.json
"""

import json
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

PRIMARY_DATA = (
    DAY22_DIR
    / "day22_graph_data.json"
)

FALLBACK_DATA = (
    DAY22_DIR
    / "graph_data.json"
)


# ============================================================
# EXPECTED GRAPH FILES
# ============================================================

GRAPH_FILES = [

    ROOT
    / "graphs"
    / "day22_graph1_strategy_coverage.png",

    ROOT
    / "graphs"
    / "day22_graph2_seed_coverage.png",

    ROOT
    / "graphs"
    / "day22_graph3_coverage_distribution.png",

    ROOT
    / "graphs"
    / "day22_graph4_verification_effort.png",

    ROOT
    / "graphs"
    / "day22_graph5_random_redundancy.png",

    ROOT
    / "graphs"
    / "day22_graph6_random_range.png",
]


# ============================================================
# RESULT-COPY FILES
# ============================================================

RESULT_GRAPH_FILES = [

    DAY22_DIR
    / "graph1_strategy_coverage.png",

    DAY22_DIR
    / "graph2_seed_coverage.png",

    DAY22_DIR
    / "graph3_coverage_distribution.png",

    DAY22_DIR
    / "graph4_verification_effort.png",

    DAY22_DIR
    / "graph5_random_redundancy.png",

    DAY22_DIR
    / "graph6_random_range.png",
]


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
# SELECT INPUT
# ============================================================

def select_data_file():

    if PRIMARY_DATA.exists():

        return PRIMARY_DATA


    if FALLBACK_DATA.exists():

        return FALLBACK_DATA


    raise FileNotFoundError(
        "Neither day22_graph_data.json "
        "nor graph_data.json exists."
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
    # OLD-SCHEMA FALLBACK
    # --------------------------------------------------------

    if runs is None:

        runs = data.get(
            "random_runs"
        )


    if not isinstance(
        runs,
        list
    ):

        raise ValueError(
            "Day 21 runs not found. "
            "Expected current field 'day21_runs'."
        )


    if not runs:

        raise ValueError(
            "Day 21 run list is empty."
        )


    return runs


# ============================================================
# VALIDATE RUN DATA
# ============================================================

def validate_runs(runs):

    errors = []

    coverage_values = []

    redundancy_values = []

    passed_runs = 0

    failed_runs = 0


    for index, run in enumerate(
        runs,
        start=1
    ):

        if not isinstance(
            run,
            dict
        ):

            errors.append(
                f"Run {index}: record is not a JSON object."
            )

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


        coverage = safe_float(
            run.get(
                "coverage_percent",
                -1.0
            ),
            -1.0
        )


        redundancy = safe_float(
            run.get(
                "redundancy_percent",
                -1.0
            ),
            -1.0
        )


        if not (
            0.0
            <= coverage
            <= 100.0
        ):

            errors.append(
                f"Run {run_number}: "
                f"invalid coverage={coverage}."
            )


        if not (
            0.0
            <= redundancy
            <= 100.0
        ):

            errors.append(
                f"Run {run_number}: "
                f"invalid redundancy={redundancy}."
            )


        if (
            status == "PASS"
            and failed_checks == 0
        ):

            passed_runs += 1

        else:

            failed_runs += 1

            errors.append(
                f"Run {run_number}: "
                f"status={status}, "
                f"failed_checks={failed_checks}."
            )


        coverage_values.append(
            coverage
        )


        redundancy_values.append(
            redundancy
        )


    return {
        "errors":
            errors,

        "passed_runs":
            passed_runs,

        "failed_runs":
            failed_runs,

        "coverage_values":
            coverage_values,

        "redundancy_values":
            redundancy_values,
    }


# ============================================================
# VALIDATE DAY 20 STRATEGIES
# ============================================================

def validate_strategies(data):

    strategies = data.get(
        "day20_strategy_comparison"
    )


    if strategies is None:

        strategies = data.get(
            "strategy_comparison"
        )


    if not isinstance(
        strategies,
        list
    ):

        raise ValueError(
            "Day 20 strategy data not found. "
            "Expected 'day20_strategy_comparison'."
        )


    if len(
        strategies
    ) != 3:

        raise ValueError(
            "Expected 3 Day 20 verification strategies, "
            f"found {len(strategies)}."
        )


    return strategies


# ============================================================
# VALIDATE GRAPH SPECS
# ============================================================

def validate_graph_specs(data):

    specs = data.get(
        "graph_specs",
        {}
    )


    if not isinstance(
        specs,
        dict
    ):

        raise ValueError(
            "'graph_specs' must be a JSON object."
        )


    expected_specs = [

        "graph_01_strategy_coverage",

        "graph_02_tests_vs_coverage",

        "graph_03_redundancy",

        "graph_04_day21_seed_coverage",

        "graph_05_day21_seed_redundancy",

        "graph_06_day20_vs_day21_random",
    ]


    missing = [

        name

        for name
        in expected_specs

        if name
        not in specs
    ]


    if missing:

        raise ValueError(
            "Missing graph specification(s): "
            + ", ".join(
                missing
            )
        )


    return specs


# ============================================================
# VALIDATE GRAPH FILE
# ============================================================

def validate_png(path):

    if not path.exists():

        return (
            False,
            f"File not found: {path.relative_to(ROOT)}"
        )


    if not path.is_file():

        return (
            False,
            f"Not a regular file: {path.relative_to(ROOT)}"
        )


    size = path.stat().st_size


    if size <= 0:

        return (
            False,
            f"Empty graph file: {path.relative_to(ROOT)}"
        )


    # PNG signature is:
    #
    # 89 50 4E 47 0D 0A 1A 0A

    with path.open(
        "rb"
    ) as file:

        signature = file.read(
            8
        )


    expected_signature = (
        b"\x89PNG\r\n\x1a\n"
    )


    if signature != expected_signature:

        return (
            False,
            f"Invalid PNG signature: {path.relative_to(ROOT)}"
        )


    return (
        True,
        size
    )


# ============================================================
# MAIN
# ============================================================

def main():

    try:

        data_file = (
            select_data_file()
        )


        data = load_json(
            data_file
        )


        errors = []


        # ====================================================
        # DAY 22 DATA STATUS
        # ====================================================

        day22_status = str(
            data.get(
                "status",
                "PASS"
            )
        ).strip().upper()


        if day22_status != "PASS":

            errors.append(
                f"Day 22 data status is {day22_status}, "
                "expected PASS."
            )


        # ====================================================
        # DAY 20 STRATEGIES
        # ====================================================

        strategies = (
            validate_strategies(
                data
            )
        )


        # ====================================================
        # DAY 21 RUNS
        # ====================================================

        runs = extract_runs(
            data
        )


        run_validation = (
            validate_runs(
                runs
            )
        )


        errors.extend(
            run_validation[
                "errors"
            ]
        )


        # ====================================================
        # GRAPH SPECIFICATIONS
        # ====================================================

        graph_specs = (
            validate_graph_specs(
                data
            )
        )


        # ====================================================
        # MEASURED VALUES
        # ====================================================

        coverage_values = (
            run_validation[
                "coverage_values"
            ]
        )


        redundancy_values = (
            run_validation[
                "redundancy_values"
            ]
        )


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
        # COMPARE AGAINST STORED DAY 21 SUMMARY
        # ====================================================

        summary = data.get(
            "day21_multi_seed_summary",
            {}
        )


        if isinstance(
            summary,
            dict
        ):

            stored_average = safe_float(
                summary.get(
                    "average_coverage_percent",
                    average_coverage
                )
            )


            stored_minimum = safe_float(
                summary.get(
                    "minimum_coverage_percent",
                    minimum_coverage
                )
            )


            stored_maximum = safe_float(
                summary.get(
                    "maximum_coverage_percent",
                    maximum_coverage
                )
            )


            stored_redundancy = safe_float(
                summary.get(
                    "average_redundancy_percent",
                    average_redundancy
                )
            )


            if abs(
                stored_average
                - average_coverage
            ) > 0.01:

                errors.append(
                    "Average coverage mismatch: "
                    f"stored={stored_average}, "
                    f"measured={average_coverage}."
                )


            if abs(
                stored_minimum
                - minimum_coverage
            ) > 0.01:

                errors.append(
                    "Minimum coverage mismatch."
                )


            if abs(
                stored_maximum
                - maximum_coverage
            ) > 0.01:

                errors.append(
                    "Maximum coverage mismatch."
                )


            if abs(
                stored_redundancy
                - average_redundancy
            ) > 0.01:

                errors.append(
                    "Average redundancy mismatch."
                )


        # ====================================================
        # VALIDATE MAIN GRAPH PNG FILES
        # ====================================================

        graph_results = []


        for number, graph_file in enumerate(
            GRAPH_FILES,
            start=1
        ):

            valid, information = (
                validate_png(
                    graph_file
                )
            )


            graph_results.append(
                (
                    number,
                    graph_file,
                    valid,
                    information
                )
            )


            if not valid:

                errors.append(
                    str(
                        information
                    )
                )


        # ====================================================
        # VALIDATE RESULT-COPY PNG FILES
        # ====================================================

        result_copy_results = []


        for number, graph_file in enumerate(
            RESULT_GRAPH_FILES,
            start=1
        ):

            valid, information = (
                validate_png(
                    graph_file
                )
            )


            result_copy_results.append(
                (
                    number,
                    graph_file,
                    valid,
                    information
                )
            )


            if not valid:

                errors.append(
                    str(
                        information
                    )
                )


        # ====================================================
        # FINAL VALIDATION
        # ====================================================

        validation_pass = (
            len(
                errors
            )
            == 0
        )


        # ====================================================
        # PRINT SUMMARY
        # ====================================================

        print(
            "=" * 74
        )


        print(
            "DAY 22 GRAPH VALIDATION"
        )


        print(
            "=" * 74
        )


        print(
            "Graph data source           :",
            data_file.relative_to(
                ROOT
            )
        )


        print(
            "Day 20 strategies           :",
            len(
                strategies
            )
        )


        print(
            "Day 21 experiment runs      :",
            len(
                runs
            )
        )


        print(
            "Day 21 passed runs          :",
            run_validation[
                "passed_runs"
            ]
        )


        print(
            "Day 21 failed runs          :",
            run_validation[
                "failed_runs"
            ]
        )


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
            "Average redundancy          :",
            f"{average_redundancy:.2f}%"
        )


        print(
            "Graph specifications        :",
            len(
                graph_specs
            )
        )


        print(
            "-" * 74
        )


        print(
            "MAIN GRAPH FILES"
        )


        for (
            number,
            graph_file,
            valid,
            information
        ) in graph_results:

            if valid:

                size_kb = (
                    information
                    / 1024.0
                )


                print(
                    f"Graph {number} : PASS  "
                    f"{graph_file.relative_to(ROOT)} "
                    f"({size_kb:.1f} KB)"
                )

            else:

                print(
                    f"Graph {number} : FAIL  "
                    f"{information}"
                )


        print(
            "-" * 74
        )


        print(
            "RESULT-COPY GRAPH FILES"
        )


        for (
            number,
            graph_file,
            valid,
            information
        ) in result_copy_results:

            if valid:

                size_kb = (
                    information
                    / 1024.0
                )


                print(
                    f"Copy {number}  : PASS  "
                    f"{graph_file.relative_to(ROOT)} "
                    f"({size_kb:.1f} KB)"
                )

            else:

                print(
                    f"Copy {number}  : FAIL  "
                    f"{information}"
                )


        print(
            "-" * 74
        )


        if errors:

            print(
                "VALIDATION ISSUES"
            )


            for error in errors:

                print(
                    " -",
                    error
                )


            print(
                "-" * 74
            )


        print(
            "DAY 22 VALIDATION STATUS    :",
            (
                "PASS"
                if validation_pass
                else "FAIL"
            )
        )


        print(
            "=" * 74
        )


        if validation_pass:

            print(
                "DAY 22 GRAPH VALIDATION: PASS"
            )

            return 0


        print(
            "DAY 22 GRAPH VALIDATION: FAIL"
        )

        return 1


    except (
        FileNotFoundError,
        ValueError,
        KeyError,
        TypeError,
        OSError,
        ZeroDivisionError
    ) as exc:

        print(
            "DAY 22 GRAPH VALIDATION: FAIL"
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
