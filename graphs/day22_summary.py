#!/usr/bin/env python3

"""
Day 22 - Final Graph and Table Summary
======================================

Project:
AI-Driven RTL Test Generation,
Coverage Analysis and Verification

Purpose:
- Read the current Day-22 graph manifest.
- Read the current Day-22 graph-data JSON.
- Confirm all six graphs were generated.
- Confirm all six result copies are valid.
- Summarize Day-20 strategy data.
- Summarize Day-21 multi-seed measured results.
- Produce a final Day-22 summary JSON.

Inputs:
    results/fifo/day22/day22_manifest.json
    results/fifo/day22/day22_graph_data.json

Fallbacks:
    results/fifo/day22/graph_manifest.json
    results/fifo/day22/graph_data.json

Output:
    results/fifo/day22/day22_final_summary.json
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


PRIMARY_MANIFEST = (
    DAY22_DIR
    / "day22_manifest.json"
)

FALLBACK_MANIFEST = (
    DAY22_DIR
    / "graph_manifest.json"
)


PRIMARY_GRAPH_DATA = (
    DAY22_DIR
    / "day22_graph_data.json"
)

FALLBACK_GRAPH_DATA = (
    DAY22_DIR
    / "graph_data.json"
)


OUTPUT_FILE = (
    DAY22_DIR
    / "day22_final_summary.json"
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
            f"Expected JSON object in {path}"
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
# FILE SELECTION
# ============================================================

def select_manifest():

    if PRIMARY_MANIFEST.exists():

        return PRIMARY_MANIFEST


    if FALLBACK_MANIFEST.exists():

        return FALLBACK_MANIFEST


    raise FileNotFoundError(
        "Neither day22_manifest.json "
        "nor graph_manifest.json exists."
    )


def select_graph_data():

    if PRIMARY_GRAPH_DATA.exists():

        return PRIMARY_GRAPH_DATA


    if FALLBACK_GRAPH_DATA.exists():

        return FALLBACK_GRAPH_DATA


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
# EXTRACT MANIFEST COUNTS
# ============================================================

def extract_manifest_values(
    manifest
):

    # --------------------------------------------------------
    # CURRENT SCHEMA
    # --------------------------------------------------------

    expected_graph_count = safe_int(
        manifest.get(
            "expected_graph_count",
            manifest.get(
                "figure_count",
                6
            )
        ),
        6
    )


    generated_graph_count = safe_int(
        manifest.get(
            "generated_graph_count",
            manifest.get(
                "figure_count",
                0
            )
        ),
        0
    )


    valid_result_copy_count = safe_int(
        manifest.get(
            "valid_result_copy_count",
            generated_graph_count
        ),
        generated_graph_count
    )


    all_graphs_valid = bool(
        manifest.get(
            "all_graphs_valid",
            (
                generated_graph_count
                == expected_graph_count
            )
        )
    )


    all_result_copies_valid = bool(
        manifest.get(
            "all_result_copies_valid",
            (
                valid_result_copy_count
                == expected_graph_count
            )
        )
    )


    manifest_status = str(
        manifest.get(
            "status",
            "UNKNOWN"
        )
    ).strip().upper()


    graphs = manifest.get(
        "graphs",
        []
    )


    if not isinstance(
        graphs,
        list
    ):

        raise ValueError(
            "Manifest 'graphs' field must be a list."
        )


    return {

        "expected_graph_count":
            expected_graph_count,

        "generated_graph_count":
            generated_graph_count,

        "valid_result_copy_count":
            valid_result_copy_count,

        "all_graphs_valid":
            all_graphs_valid,

        "all_result_copies_valid":
            all_result_copies_valid,

        "manifest_status":
            manifest_status,

        "graphs":
            graphs,
    }


# ============================================================
# DAY 20 STRATEGY SUMMARY
# ============================================================

def extract_day20_strategies(
    graph_data
):

    strategies = graph_data.get(
        "day20_strategy_comparison"
    )


    if strategies is None:

        strategies = graph_data.get(
            "strategy_comparison"
        )


    if not isinstance(
        strategies,
        list
    ):

        raise ValueError(
            "Day 20 strategy data not found."
        )


    normalized = []


    for row in strategies:

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

                "coverage_percent":
                    round(
                        safe_float(
                            row.get(
                                "coverage_percent",
                                0.0
                            )
                        ),
                        2
                    ),

                "stimulus_cycles":
                    safe_int(
                        row.get(
                            "stimulus_cycles",
                            0
                        )
                    ),

                "unique_behavior_signatures":
                    safe_int(
                        row.get(
                            "unique_behavior_signatures",
                            0
                        )
                    ),

                "redundant_cycles":
                    safe_int(
                        row.get(
                            "redundant_cycles",
                            0
                        )
                    ),

                "redundancy_percent":
                    round(
                        safe_float(
                            row.get(
                                "redundancy_percent",
                                0.0
                            )
                        ),
                        2
                    ),
            }
        )


    if not normalized:

        raise ValueError(
            "No usable Day 20 strategy records found."
        )


    return normalized


# ============================================================
# DAY 21 SUMMARY
# ============================================================

def extract_day21_summary(
    graph_data
):

    summary = graph_data.get(
        "day21_multi_seed_summary",
        {}
    )


    if not isinstance(
        summary,
        dict
    ):

        raise ValueError(
            "day21_multi_seed_summary must be an object."
        )


    runs = graph_data.get(
        "day21_runs",
        []
    )


    if not isinstance(
        runs,
        list
    ):

        raise ValueError(
            "day21_runs must be a list."
        )


    number_of_runs = safe_int(
        summary.get(
            "number_of_runs",
            len(
                runs
            )
        ),
        len(
            runs
        )
    )


    transactions_per_run = safe_int(
        summary.get(
            "transactions_per_run",
            0
        )
    )


    total_transactions = safe_int(
        summary.get(
            "total_transactions",
            (
                number_of_runs
                * transactions_per_run
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


    average_coverage = safe_float(
        summary.get(
            "average_coverage_percent",
            0.0
        )
    )


    minimum_coverage = safe_float(
        summary.get(
            "minimum_coverage_percent",
            0.0
        )
    )


    maximum_coverage = safe_float(
        summary.get(
            "maximum_coverage_percent",
            0.0
        )
    )


    average_redundancy = safe_float(
        summary.get(
            "average_redundancy_percent",
            0.0
        )
    )


    average_runtime = safe_float(
        summary.get(
            "average_runtime_seconds",
            0.0
        )
    )


    total_checks = safe_int(
        summary.get(
            "total_verification_checks",
            0
        )
    )


    total_passed_checks = safe_int(
        summary.get(
            "total_passed_checks",
            0
        )
    )


    total_failed_checks = safe_int(
        summary.get(
            "total_failed_checks",
            0
        )
    )


    return {

        "number_of_runs":
            number_of_runs,

        "transactions_per_run":
            transactions_per_run,

        "total_transactions":
            total_transactions,

        "passed_runs":
            passed_runs,

        "failed_runs":
            failed_runs,

        "average_coverage_percent":
            round(
                average_coverage,
                2
            ),

        "minimum_coverage_percent":
            round(
                minimum_coverage,
                2
            ),

        "maximum_coverage_percent":
            round(
                maximum_coverage,
                2
            ),

        "average_redundancy_percent":
            round(
                average_redundancy,
                2
            ),

        "average_runtime_seconds":
            round(
                average_runtime,
                6
            ),

        "total_verification_checks":
            total_checks,

        "total_passed_checks":
            total_passed_checks,

        "total_failed_checks":
            total_failed_checks,
    }


# ============================================================
# VALIDATE FINAL DAY 22 STATE
# ============================================================

def validate_day22(
    manifest_values,
    day21_summary
):

    errors = []


    if (
        manifest_values[
            "manifest_status"
        ]
        != "PASS"
    ):

        errors.append(
            "Graph manifest status is not PASS."
        )


    if (
        manifest_values[
            "generated_graph_count"
        ]
        != manifest_values[
            "expected_graph_count"
        ]
    ):

        errors.append(
            "Generated graph count does not "
            "match expected graph count."
        )


    if (
        manifest_values[
            "valid_result_copy_count"
        ]
        != manifest_values[
            "expected_graph_count"
        ]
    ):

        errors.append(
            "Valid result-copy count does not "
            "match expected graph count."
        )


    if not manifest_values[
        "all_graphs_valid"
    ]:

        errors.append(
            "Not all main graph files are valid."
        )


    if not manifest_values[
        "all_result_copies_valid"
    ]:

        errors.append(
            "Not all result-copy graph files are valid."
        )


    if (
        day21_summary[
            "failed_runs"
        ]
        != 0
    ):

        errors.append(
            "Day 21 contains failed experiment runs."
        )


    if (
        day21_summary[
            "total_failed_checks"
        ]
        != 0
    ):

        errors.append(
            "Day 21 contains failed verification checks."
        )


    return errors


# ============================================================
# MAIN
# ============================================================

def main():

    try:

        manifest_file = (
            select_manifest()
        )


        graph_data_file = (
            select_graph_data()
        )


        manifest = load_json(
            manifest_file
        )


        graph_data = load_json(
            graph_data_file
        )


        manifest_values = (
            extract_manifest_values(
                manifest
            )
        )


        strategies = (
            extract_day20_strategies(
                graph_data
            )
        )


        day21_summary = (
            extract_day21_summary(
                graph_data
            )
        )


        errors = validate_day22(
            manifest_values,
            day21_summary
        )


        day22_status = (
            "PASS"
            if not errors
            else "FAIL"
        )


        # ====================================================
        # FINAL SUMMARY JSON
        # ====================================================

        final_summary = {

            "day":
                22,

            "dut":
                "fifo",

            "task":
                "generate_graphs_and_tables",

            "status":
                day22_status,

            "graph_manifest": {

                "source":
                    manifest_file.relative_to(
                        ROOT
                    ).as_posix(),

                "expected_graph_count":
                    manifest_values[
                        "expected_graph_count"
                    ],

                "generated_graph_count":
                    manifest_values[
                        "generated_graph_count"
                    ],

                "valid_result_copy_count":
                    manifest_values[
                        "valid_result_copy_count"
                    ],

                "all_graphs_valid":
                    manifest_values[
                        "all_graphs_valid"
                    ],

                "all_result_copies_valid":
                    manifest_values[
                        "all_result_copies_valid"
                    ],

                "graphs":
                    manifest_values[
                        "graphs"
                    ],
            },

            "day20_strategy_comparison":
                strategies,

            "day21_multi_seed_summary":
                day21_summary,

            "artifacts": {

                "graph_data_json":
                    graph_data_file.relative_to(
                        ROOT
                    ).as_posix(),

                "strategy_csv":
                    "results/fifo/day22/"
                    "strategy_comparison.csv",

                "multi_seed_csv":
                    "results/fifo/day22/"
                    "day21_multi_seed.csv",

                "coverage_distribution_csv":
                    "results/fifo/day22/"
                    "coverage_distribution.csv",

                "graph_points_csv":
                    "results/fifo/day22/"
                    "graph_points.csv",

                "summary_csv":
                    "results/fifo/day22/"
                    "day22_summary.csv",

                "manifest_json":
                    manifest_file.relative_to(
                        ROOT
                    ).as_posix(),
            },

            "validation_issues":
                errors,

            "rtl_modified":
                False,
        }


        save_json(
            OUTPUT_FILE,
            final_summary
        )


        # ====================================================
        # PRINT FINAL SUMMARY
        # ====================================================

        print(
            "=" * 74
        )


        print(
            "DAY 22 FINAL SUMMARY"
        )


        print(
            "=" * 74
        )


        print(
            "DUT                         : FIFO"
        )


        print(
            "Expected graphs             :",
            manifest_values[
                "expected_graph_count"
            ]
        )


        print(
            "Generated graphs            :",
            manifest_values[
                "generated_graph_count"
            ]
        )


        print(
            "Valid graph copies          :",
            manifest_values[
                "valid_result_copy_count"
            ]
        )


        print(
            "All main graphs valid       :",
            manifest_values[
                "all_graphs_valid"
            ]
        )


        print(
            "All graph copies valid      :",
            manifest_values[
                "all_result_copies_valid"
            ]
        )


        print(
            "-" * 74
        )


        print(
            "Day 20 strategies           :",
            len(
                strategies
            )
        )


        for strategy in strategies:

            print(
                f"  {strategy['strategy']:20s} "
                f"coverage="
                f"{strategy['coverage_percent']:6.2f}% "
                f"cycles="
                f"{strategy['stimulus_cycles']:3d} "
                f"redundancy="
                f"{strategy['redundancy_percent']:6.2f}%"
            )


        print(
            "-" * 74
        )


        print(
            "Day 21 experiment runs      :",
            day21_summary[
                "number_of_runs"
            ]
        )


        print(
            "Transactions per run        :",
            day21_summary[
                "transactions_per_run"
            ]
        )


        print(
            "Total transactions          :",
            day21_summary[
                "total_transactions"
            ]
        )


        print(
            "Passed runs                 :",
            day21_summary[
                "passed_runs"
            ]
        )


        print(
            "Failed runs                 :",
            day21_summary[
                "failed_runs"
            ]
        )


        print(
            "Average coverage            :",
            f"{day21_summary['average_coverage_percent']:.2f}%"
        )


        print(
            "Minimum coverage            :",
            f"{day21_summary['minimum_coverage_percent']:.2f}%"
        )


        print(
            "Maximum coverage            :",
            f"{day21_summary['maximum_coverage_percent']:.2f}%"
        )


        print(
            "Average redundancy          :",
            f"{day21_summary['average_redundancy_percent']:.2f}%"
        )


        print(
            "Total verification checks   :",
            day21_summary[
                "total_verification_checks"
            ]
        )


        print(
            "Failed verification checks  :",
            day21_summary[
                "total_failed_checks"
            ]
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
            "Summary output              :",
            OUTPUT_FILE.relative_to(
                ROOT
            )
        )


        print(
            "DAY 22 STATUS               :",
            day22_status
        )


        print(
            "=" * 74
        )


        if day22_status == "PASS":

            print(
                "DAY 22 SUMMARY: PASS"
            )

            return 0


        print(
            "DAY 22 SUMMARY: FAIL"
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
            "DAY 22 SUMMARY: FAIL"
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
