#!/usr/bin/env python3

"""
Day 21 - FIFO Multi-Seed Final Experiments
==========================================

Project:
AI-Driven RTL Test Generation,
Coverage Analysis and Verification

Purpose:
- Execute 10 reproducible FIFO random-baseline experiments.
- Generate transactions with different deterministic seeds.
- Generate a Verilog testbench for every seed.
- Compile and simulate every generated testbench.
- Validate simulation using FAILED_CHECKS == 0.
- Measure the same 10-point FIFO functional coverage.
- Measure trace redundancy.
- Save per-run JSON and final CSV/JSON results.

Important:
The simulation PASS decision does NOT depend on only one
hard-coded PASS-marker string. A valid run requires:

    simulator return code = 0
    FAILED_CHECKS = 0

The printed PASS marker is recorded as supporting evidence.
"""

import csv
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path


# ============================================================
# PROJECT PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

PYTHON = sys.executable

DAY21_DIR = (
    ROOT
    / "results"
    / "fifo"
    / "day21"
)

RUNS_DIR = (
    DAY21_DIR
    / "runs"
)

GENERATED_TB_DIR = (
    ROOT
    / "testbench"
    / "generated"
    / "day21"
)

RTL_FILE = (
    ROOT
    / "rtl"
    / "fifo.v"
)

RANDOM_GENERATOR = (
    ROOT
    / "baseline"
    / "random_fifo_generator.py"
)

TB_GENERATOR = (
    ROOT
    / "baseline"
    / "random_fifo_tb_generator.py"
)


# ============================================================
# EXPERIMENT SETTINGS
# ============================================================

BASE_SEED = 20260921

NUMBER_OF_RUNS = 10

TRANSACTIONS_PER_RUN = 20


# ============================================================
# FIFO COVERAGE MODEL
# ============================================================

COVERAGE_POINTS = {
    "COV_FIFO_001": "RESET",
    "COV_FIFO_002": "WRITE",
    "COV_FIFO_003": "READ",
    "COV_FIFO_004": "IDLE",
    "COV_FIFO_005": "SIMULTANEOUS_WRITE_READ",
    "COV_FIFO_006": "EMPTY_STATE",
    "COV_FIFO_007": "FULL_STATE",
    "COV_FIFO_008": "READ_WHEN_EMPTY",
    "COV_FIFO_009": "WRITE_WHEN_FULL",
    "COV_FIFO_010": "POINTER_WRAPAROUND",
}


# ============================================================
# PRINT SECTION
# ============================================================

def print_section(title):

    print()
    print("=" * 68)
    print(title)
    print("=" * 68)


# ============================================================
# RUN COMMAND
# ============================================================

def run_command(
    command,
    title,
    cwd=ROOT
):

    print_section(title)

    printable = " ".join(
        str(item)
        for item in command
    )

    print(
        "COMMAND:",
        printable
    )

    start_time = time.perf_counter()

    result = subprocess.run(
        [str(item) for item in command],
        cwd=cwd,
        text=True,
        capture_output=True
    )

    elapsed = (
        time.perf_counter()
        - start_time
    )

    if result.stdout:

        print(
            result.stdout,
            end=""
        )

    if result.stderr:

        print(
            result.stderr,
            end="",
            file=sys.stderr
        )

    return result, elapsed


# ============================================================
# LOAD JSON
# ============================================================

def load_json(path):

    with path.open(
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


# ============================================================
# SAVE JSON
# ============================================================

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
# FIND RANDOM GENERATOR OUTPUT
# ============================================================

def find_generator_output(stdout_text):

    # --------------------------------------------------------
    # Prefer path printed by random_fifo_generator.py
    # --------------------------------------------------------

    match = re.search(
        r"Output\s*:\s*(.+)",
        stdout_text
    )

    if match:

        candidate = Path(
            match.group(1).strip()
        )

        if not candidate.is_absolute():

            candidate = (
                ROOT
                / candidate
            )

        if candidate.exists():

            return candidate


    # --------------------------------------------------------
    # Existing Day-20 generator default
    # --------------------------------------------------------

    fallback = (
        ROOT
        / "results"
        / "fifo"
        / "day20"
        / "random_transactions.json"
    )

    if fallback.exists():

        return fallback


    raise FileNotFoundError(
        "Random transaction JSON was not generated."
    )


# ============================================================
# INTEGER CONVERSION
# ============================================================

def value_to_int(
    row,
    key,
    default=0
):

    value = row.get(
        key,
        default
    )

    try:

        return int(
            str(value).strip()
        )

    except (
        TypeError,
        ValueError
    ):

        return default


# ============================================================
# READ TRACE CSV
# ============================================================

def read_trace(path):

    if not path.exists():

        raise FileNotFoundError(
            f"Trace file not found: {path}"
        )

    rows = []

    with path.open(
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        reader = csv.DictReader(
            file
        )

        required = {
            "rst",
            "wr_en",
            "rd_en",
            "count_before",
            "count_after",
            "write_ptr_before",
            "write_ptr_after",
            "read_ptr_before",
            "read_ptr_after",
            "full",
            "empty",
        }

        available = set(
            reader.fieldnames
            or []
        )

        missing = (
            required
            - available
        )

        if missing:

            raise ValueError(
                "Trace is missing columns: "
                + ", ".join(
                    sorted(missing)
                )
            )

        for row in reader:

            if not row:

                continue

            rows.append(
                row
            )

    if not rows:

        raise ValueError(
            "FIFO execution trace is empty."
        )

    return rows


# ============================================================
# FIFO FUNCTIONAL COVERAGE
# ============================================================

def analyze_coverage(rows):

    hits = {
        point_id: 0
        for point_id in COVERAGE_POINTS
    }

    for row in rows:

        rst = value_to_int(
            row,
            "rst"
        )

        wr_en = value_to_int(
            row,
            "wr_en"
        )

        rd_en = value_to_int(
            row,
            "rd_en"
        )

        count_before = value_to_int(
            row,
            "count_before"
        )

        write_ptr_before = value_to_int(
            row,
            "write_ptr_before"
        )

        write_ptr_after = value_to_int(
            row,
            "write_ptr_after"
        )

        read_ptr_before = value_to_int(
            row,
            "read_ptr_before"
        )

        read_ptr_after = value_to_int(
            row,
            "read_ptr_after"
        )

        full = value_to_int(
            row,
            "full"
        )

        empty = value_to_int(
            row,
            "empty"
        )


        # ----------------------------------------------------
        # COV_FIFO_001 - RESET
        # ----------------------------------------------------

        if rst == 1:

            hits[
                "COV_FIFO_001"
            ] += 1


        # ----------------------------------------------------
        # COV_FIFO_002 - WRITE
        # ----------------------------------------------------

        if (
            rst == 0
            and wr_en == 1
            and count_before < 4
        ):

            hits[
                "COV_FIFO_002"
            ] += 1


        # ----------------------------------------------------
        # COV_FIFO_003 - READ
        # ----------------------------------------------------

        if (
            rst == 0
            and rd_en == 1
            and count_before > 0
        ):

            hits[
                "COV_FIFO_003"
            ] += 1


        # ----------------------------------------------------
        # COV_FIFO_004 - IDLE
        # ----------------------------------------------------

        if (
            rst == 0
            and wr_en == 0
            and rd_en == 0
        ):

            hits[
                "COV_FIFO_004"
            ] += 1


        # ----------------------------------------------------
        # COV_FIFO_005 - SIMULTANEOUS WRITE / READ
        # ----------------------------------------------------

        if (
            rst == 0
            and wr_en == 1
            and rd_en == 1
        ):

            hits[
                "COV_FIFO_005"
            ] += 1


        # ----------------------------------------------------
        # COV_FIFO_006 - EMPTY STATE
        # ----------------------------------------------------

        if empty == 1:

            hits[
                "COV_FIFO_006"
            ] += 1


        # ----------------------------------------------------
        # COV_FIFO_007 - FULL STATE
        # ----------------------------------------------------

        if full == 1:

            hits[
                "COV_FIFO_007"
            ] += 1


        # ----------------------------------------------------
        # COV_FIFO_008 - READ WHILE EMPTY
        # ----------------------------------------------------

        if (
            rst == 0
            and rd_en == 1
            and count_before == 0
        ):

            hits[
                "COV_FIFO_008"
            ] += 1


        # ----------------------------------------------------
        # COV_FIFO_009 - WRITE WHILE FULL
        # ----------------------------------------------------

        if (
            rst == 0
            and wr_en == 1
            and count_before == 4
        ):

            hits[
                "COV_FIFO_009"
            ] += 1


        # ----------------------------------------------------
        # COV_FIFO_010 - POINTER WRAPAROUND
        # ----------------------------------------------------

        write_wrap = (
            write_ptr_after
            < write_ptr_before
        )

        read_wrap = (
            read_ptr_after
            < read_ptr_before
        )

        if (
            write_wrap
            or read_wrap
        ):

            hits[
                "COV_FIFO_010"
            ] += 1


    covered_points = [
        point_id
        for point_id, count
        in hits.items()
        if count > 0
    ]

    missing_points = [
        point_id
        for point_id, count
        in hits.items()
        if count == 0
    ]

    total_points = len(
        COVERAGE_POINTS
    )

    covered_count = len(
        covered_points
    )

    coverage_percent = round(
        (
            covered_count
            / total_points
        )
        * 100.0,
        2
    )

    return {
        "dut":
            "fifo",

        "coverage_type":
            "fifo_functional_coverage",

        "measurement_source":
            "executed_fifo_trace",

        "trace_rows":
            len(rows),

        "total_coverage_points":
            total_points,

        "covered_coverage_points":
            covered_count,

        "coverage_percent":
            coverage_percent,

        "covered_points":
            covered_points,

        "missing_points":
            missing_points,

        "point_hits":
            hits,

        "point_definitions":
            COVERAGE_POINTS,

        "coverage_complete":
            covered_count
            == total_points,
    }


# ============================================================
# TRACE STATISTICS
# ============================================================

def analyze_statistics(rows):

    reset_rows = [
        row
        for row in rows
        if value_to_int(
            row,
            "rst"
        ) == 1
    ]

    stimulus_rows = [
        row
        for row in rows
        if value_to_int(
            row,
            "rst"
        ) == 0
    ]


    signatures = []

    write_requests = 0
    read_requests = 0
    simultaneous_requests = 0
    blocked_writes = 0
    blocked_reads = 0
    idle_cycles = 0


    for row in stimulus_rows:

        wr_en = value_to_int(
            row,
            "wr_en"
        )

        rd_en = value_to_int(
            row,
            "rd_en"
        )

        count_before = value_to_int(
            row,
            "count_before"
        )


        signature = (
            wr_en,
            rd_en,
            count_before
        )

        signatures.append(
            signature
        )


        if wr_en == 1:

            write_requests += 1


        if rd_en == 1:

            read_requests += 1


        if (
            wr_en == 1
            and rd_en == 1
        ):

            simultaneous_requests += 1


        if (
            wr_en == 0
            and rd_en == 0
        ):

            idle_cycles += 1


        if (
            wr_en == 1
            and count_before == 4
        ):

            blocked_writes += 1


        if (
            rd_en == 1
            and count_before == 0
        ):

            blocked_reads += 1


    unique_signatures = len(
        set(signatures)
    )

    stimulus_cycles = len(
        stimulus_rows
    )

    redundant_cycles = max(
        0,
        stimulus_cycles
        - unique_signatures
    )

    if stimulus_cycles > 0:

        redundancy_percent = round(
            (
                redundant_cycles
                / stimulus_cycles
            )
            * 100.0,
            2
        )

    else:

        redundancy_percent = 0.0


    return {
        "strategy":
            "random",

        "trace_rows":
            len(rows),

        "reset_cycles":
            len(reset_rows),

        "stimulus_cycles":
            stimulus_cycles,

        "idle_cycles":
            idle_cycles,

        "write_requests":
            write_requests,

        "read_requests":
            read_requests,

        "simultaneous_requests":
            simultaneous_requests,

        "blocked_writes":
            blocked_writes,

        "blocked_reads":
            blocked_reads,

        "unique_behavior_signatures":
            unique_signatures,

        "redundant_cycles":
            redundant_cycles,

        "redundancy_percent":
            redundancy_percent,

        "signature_definition":
            "(wr_en, rd_en, count_before)",
    }


# ============================================================
# PARSE SIMULATION COUNTER
# ============================================================

def parse_counter(
    text,
    name
):

    match = re.search(
        rf"{re.escape(name)}\s*=\s*(\d+)",
        text
    )

    if not match:

        return None

    return int(
        match.group(1)
    )


# ============================================================
# SIMULATION VALIDATION
# ============================================================

def validate_simulation(
    simulation_result
):

    stdout = (
        simulation_result.stdout
        or ""
    )

    stderr = (
        simulation_result.stderr
        or ""
    )


    total_checks = parse_counter(
        stdout,
        "TOTAL_CHECKS"
    )

    passed_checks = parse_counter(
        stdout,
        "PASSED_CHECKS"
    )

    failed_checks = parse_counter(
        stdout,
        "FAILED_CHECKS"
    )


    pass_markers = [
        "DAY 21 FIFO RANDOM: PASS",
        "DAY 20 FIFO RANDOM BASELINE: PASS",
        "FIFO RANDOM: PASS",
    ]

    pass_marker_found = any(
        marker in stdout
        for marker in pass_markers
    )


    # --------------------------------------------------------
    # IMPORTANT:
    #
    # The actual counters are the primary PASS evidence.
    #
    # This fixes the previous:
    #
    # ERROR: Random simulation PASS marker not found.
    # --------------------------------------------------------

    counters_pass = (
        total_checks is not None
        and passed_checks is not None
        and failed_checks is not None
        and failed_checks == 0
        and passed_checks == total_checks
    )


    simulation_pass = (
        simulation_result.returncode == 0
        and counters_pass
    )


    return {
        "simulation_pass":
            simulation_pass,

        "return_code":
            simulation_result.returncode,

        "total_checks":
            total_checks,

        "passed_checks":
            passed_checks,

        "failed_checks":
            failed_checks,

        "pass_marker_found":
            pass_marker_found,

        "stdout":
            stdout,

        "stderr":
            stderr,
    }


# ============================================================
# WRITE FINAL CSV
# ============================================================

def write_results_csv(
    output_file,
    results
):

    fieldnames = [
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
    ]


    with output_file.open(
        "w",
        encoding="utf-8",
        newline=""
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()


        for result in results:

            writer.writerow(
                {
                    "run":
                        result[
                            "run"
                        ],

                    "seed":
                        result[
                            "seed"
                        ],

                    "transactions":
                        result[
                            "transactions"
                        ],

                    "simulation_status":
                        result[
                            "simulation_status"
                        ],

                    "total_checks":
                        result[
                            "total_checks"
                        ],

                    "passed_checks":
                        result[
                            "passed_checks"
                        ],

                    "failed_checks":
                        result[
                            "failed_checks"
                        ],

                    "coverage_percent":
                        result[
                            "coverage_percent"
                        ],

                    "covered_points":
                        result[
                            "covered_points"
                        ],

                    "missing_points":
                        result[
                            "missing_points"
                        ],

                    "unique_behavior_signatures":
                        result[
                            "unique_behavior_signatures"
                        ],

                    "redundant_cycles":
                        result[
                            "redundant_cycles"
                        ],

                    "redundancy_percent":
                        result[
                            "redundancy_percent"
                        ],

                    "runtime_seconds":
                        result[
                            "runtime_seconds"
                        ],
                }
            )


# ============================================================
# MAIN
# ============================================================

def main():

    DAY21_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    RUNS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    GENERATED_TB_DIR.mkdir(
        parents=True,
        exist_ok=True
    )


    results = []


    try:

        for run_number in range(
            1,
            NUMBER_OF_RUNS + 1
        ):

            seed = (
                BASE_SEED
                + run_number
                - 1
            )

            run_dir = (
                RUNS_DIR
                / f"seed_{seed}"
            )

            run_dir.mkdir(
                parents=True,
                exist_ok=True
            )


            print()
            print("#" * 68)

            print(
                f"DAY 21 RUN {run_number}/{NUMBER_OF_RUNS}"
            )

            print(
                f"SEED: {seed}"
            )

            print("#" * 68)


            # =================================================
            # STEP 1 - RANDOM TRANSACTION GENERATION
            # =================================================

            generation_result, generation_time = run_command(

                [
                    PYTHON,
                    RANDOM_GENERATOR,
                    str(seed),
                    str(
                        TRANSACTIONS_PER_RUN
                    ),
                ],

                "Generate random transactions"
            )


            if generation_result.returncode != 0:

                raise RuntimeError(
                    "Random transaction generation "
                    f"failed with exit code "
                    f"{generation_result.returncode}"
                )


            generator_output = (
                find_generator_output(
                    generation_result.stdout
                )
            )


            transactions_file = (
                run_dir
                / "random_transactions.json"
            )


            shutil.copy2(
                generator_output,
                transactions_file
            )


            # =================================================
            # STEP 2 - GENERATE VERILOG TESTBENCH
            # =================================================

            tb_file = (
                GENERATED_TB_DIR
                / f"tb_fifo_seed_{seed}.v"
            )


            tb_result, tb_time = run_command(

                [
                    PYTHON,
                    TB_GENERATOR,
                    transactions_file,
                    tb_file,
                ],

                "Generate random Verilog testbench"
            )


            if tb_result.returncode != 0:

                raise RuntimeError(
                    "Random FIFO TB generation "
                    f"failed with exit code "
                    f"{tb_result.returncode}"
                )


            # =================================================
            # STEP 3 - COMPILE
            # =================================================

            simulation_out = (
                run_dir
                / "simulation.out"
            )


            compile_result, compile_time = run_command(

                [
                    "iverilog",
                    "-g2012",
                    "-o",
                    simulation_out,
                    RTL_FILE,
                    tb_file,
                ],

                "Compile FIFO random simulation"
            )


            compile_log = (
                run_dir
                / "compile.log"
            )


            compile_log.write_text(

                "STDOUT:\n"
                + (
                    compile_result.stdout
                    or ""
                )
                + "\nSTDERR:\n"
                + (
                    compile_result.stderr
                    or ""
                ),

                encoding="utf-8"
            )


            if compile_result.returncode != 0:

                raise RuntimeError(
                    "Compile FIFO random simulation "
                    f"failed with exit code "
                    f"{compile_result.returncode}"
                )


            # =================================================
            # STEP 4 - SIMULATION
            # =================================================

            simulation_result, simulation_time = run_command(

                [
                    "vvp",
                    simulation_out,
                ],

                "Run FIFO random simulation"
            )


            simulation_log = (
                run_dir
                / "simulation.log"
            )


            simulation_log.write_text(

                (
                    simulation_result.stdout
                    or ""
                )
                + (
                    simulation_result.stderr
                    or ""
                ),

                encoding="utf-8"
            )


            simulation = (
                validate_simulation(
                    simulation_result
                )
            )


            if not simulation[
                "simulation_pass"
            ]:

                raise RuntimeError(
                    "Random simulation failed. "
                    f"TOTAL_CHECKS="
                    f"{simulation['total_checks']} "
                    f"PASSED_CHECKS="
                    f"{simulation['passed_checks']} "
                    f"FAILED_CHECKS="
                    f"{simulation['failed_checks']} "
                    f"return_code="
                    f"{simulation['return_code']}"
                )


            # =================================================
            # STEP 5 - TRACE
            # =================================================

            trace_file = (
                run_dir
                / "random_trace.csv"
            )


            trace_rows = read_trace(
                trace_file
            )


            # =================================================
            # STEP 6 - COVERAGE
            # =================================================

            coverage = analyze_coverage(
                trace_rows
            )


            coverage_file = (
                run_dir
                / "coverage.json"
            )


            save_json(
                coverage_file,
                coverage
            )


            # =================================================
            # STEP 7 - TRACE STATISTICS
            # =================================================

            statistics = (
                analyze_statistics(
                    trace_rows
                )
            )


            statistics_file = (
                run_dir
                / "statistics.json"
            )


            save_json(
                statistics_file,
                statistics
            )


            # =================================================
            # STEP 8 - RUN SUMMARY
            # =================================================

            runtime_seconds = round(
                generation_time
                + tb_time
                + compile_time
                + simulation_time,
                6
            )


            run_summary = {
                "day":
                    21,

                "run":
                    run_number,

                "seed":
                    seed,

                "dut":
                    "fifo",

                "strategy":
                    "random",

                "transactions":
                    TRANSACTIONS_PER_RUN,

                "simulation_status":
                    "PASS",

                "total_checks":
                    simulation[
                        "total_checks"
                    ],

                "passed_checks":
                    simulation[
                        "passed_checks"
                    ],

                "failed_checks":
                    simulation[
                        "failed_checks"
                    ],

                "pass_marker_found":
                    simulation[
                        "pass_marker_found"
                    ],

                "coverage_percent":
                    coverage[
                        "coverage_percent"
                    ],

                "covered_points":
                    coverage[
                        "covered_coverage_points"
                    ],

                "missing_points":
                    coverage[
                        "missing_points"
                    ],

                "unique_behavior_signatures":
                    statistics[
                        "unique_behavior_signatures"
                    ],

                "redundant_cycles":
                    statistics[
                        "redundant_cycles"
                    ],

                "redundancy_percent":
                    statistics[
                        "redundancy_percent"
                    ],

                "runtime_seconds":
                    runtime_seconds,
            }


            save_json(
                run_dir
                / "run_summary.json",

                run_summary
            )


            results.append(
                run_summary
            )


            print_section(
                f"DAY 21 RUN {run_number} RESULT"
            )

            print(
                "Seed             :",
                seed
            )

            print(
                "Simulation       : PASS"
            )

            print(
                "Checks           :",
                f"{simulation['passed_checks']}/"
                f"{simulation['total_checks']}"
            )

            print(
                "Failed checks    :",
                simulation[
                    "failed_checks"
                ]
            )

            print(
                "Coverage         :",
                f"{coverage['coverage_percent']}%"
            )

            print(
                "Missing points   :",
                coverage[
                    "missing_points"
                ]
            )

            print(
                "Redundancy       :",
                f"{statistics['redundancy_percent']}%"
            )


        # =====================================================
        # FINAL CSV
        # =====================================================

        final_csv = (
            DAY21_DIR
            / "day21_experiment_results.csv"
        )


        write_results_csv(
            final_csv,
            results
        )


        # =====================================================
        # FINAL SUMMARY
        # =====================================================

        coverage_values = [
            result[
                "coverage_percent"
            ]
            for result in results
        ]


        redundancy_values = [
            result[
                "redundancy_percent"
            ]
            for result in results
        ]


        passed_runs = sum(
            1
            for result in results
            if (
                result[
                    "simulation_status"
                ]
                == "PASS"
            )
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


        average_redundancy = round(
            sum(
                redundancy_values
            )
            / len(
                redundancy_values
            ),
            2
        )


        final_summary = {
            "day":
                21,

            "dut":
                "fifo",

            "strategy":
                "random_multi_seed",

            "number_of_runs":
                NUMBER_OF_RUNS,

            "transactions_per_run":
                TRANSACTIONS_PER_RUN,

            "base_seed":
                BASE_SEED,

            "passed_runs":
                passed_runs,

            "failed_runs":
                NUMBER_OF_RUNS
                - passed_runs,

            "average_coverage_percent":
                average_coverage,

            "minimum_coverage_percent":
                min(
                    coverage_values
                ),

            "maximum_coverage_percent":
                max(
                    coverage_values
                ),

            "average_redundancy_percent":
                average_redundancy,

            "all_simulations_passed":
                passed_runs
                == NUMBER_OF_RUNS,

            "results_csv":
                "results/fifo/day21/"
                "day21_experiment_results.csv",

            "runs":
                results,
        }


        save_json(
            DAY21_DIR
            / "day21_experiment_summary.json",

            final_summary
        )


        print()
        print("=" * 68)

        if (
            passed_runs
            == NUMBER_OF_RUNS
        ):

            print(
                "DAY 21 MULTI-SEED EXPERIMENT: PASS"
            )

        else:

            print(
                "DAY 21 MULTI-SEED EXPERIMENT: FAIL"
            )

        print("=" * 68)

        print(
            "Completed runs       :",
            len(results)
        )

        print(
            "Passed runs          :",
            passed_runs
        )

        print(
            "Failed runs          :",
            NUMBER_OF_RUNS
            - passed_runs
        )

        print(
            "Average coverage     :",
            f"{average_coverage}%"
        )

        print(
            "Average redundancy   :",
            f"{average_redundancy}%"
        )

        print(
            "Results CSV          :",
            "results/fifo/day21/"
            "day21_experiment_results.csv"
        )

        print(
            "Summary JSON         :",
            "results/fifo/day21/"
            "day21_experiment_summary.json"
        )

        print("=" * 68)


        if (
            passed_runs
            != NUMBER_OF_RUNS
        ):

            return 1


        return 0


    except Exception as exc:

        print()
        print("=" * 68)
        print(
            "DAY 21 MULTI-SEED EXPERIMENT: FAIL"
        )
        print("=" * 68)

        print(
            "ERROR:",
            exc
        )

        return 1


# ============================================================
# PROGRAM ENTRY
# ============================================================

if __name__ == "__main__":

    sys.exit(
        main()
    )
