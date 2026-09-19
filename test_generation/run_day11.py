import subprocess
import sys
from pathlib import Path


VALIDATED_TESTS = (
    "results/alu/day10/"
    "validated_tests.json"
)

GENERATED_TB = (
    "testbench/generated/"
    "tb_alu_hermes_generated.v"
)

COMPILED_OUTPUT = (
    "results/alu/day11/"
    "alu_hermes_generated.out"
)

SIMULATION_LOG = (
    "results/alu/day11/"
    "generated_simulation.log"
)

SIMULATION_REPORT = (
    "results/alu/day11/"
    "generated_simulation_report.json"
)


def run_command(
    title,
    command
):

    print()

    print(
        "=" * 60
    )

    print(
        title
    )

    print(
        "=" * 60
    )

    process = subprocess.run(
        command
    )

    if process.returncode != 0:

        print()

        print(
            f"{title}: FAIL"
        )

        sys.exit(1)

    print()

    print(
        f"{title}: PASS"
    )


def run_simulation():

    print()

    print(
        "=" * 60
    )

    print(
        "4. RUN GENERATED "
        "VERILOG SIMULATION"
    )

    print(
        "=" * 60
    )

    process = subprocess.run(
        [
            "vvp",
            COMPILED_OUTPUT
        ],
        capture_output=True,
        text=True
    )

    Path(
        SIMULATION_LOG
    ).write_text(
        process.stdout
        + process.stderr
    )

    print(
        process.stdout,
        end=""
    )

    if process.stderr:

        print(
            process.stderr,
            end="",
            file=sys.stderr
        )

    if process.returncode != 0:

        print()

        print(
            "GENERATED SIMULATION: "
            "FAIL"
        )

        sys.exit(1)

    print()

    print(
        "GENERATED SIMULATION: "
        "PASS"
    )


def main():

    Path(
        "results/alu/day11"
    ).mkdir(
        parents=True,
        exist_ok=True
    )

    print(
        "========================================"
    )

    print(
        "DAY 11 - AUTOMATIC VERILOG "
        "TESTBENCH EXECUTION"
    )

    print(
        "========================================"
    )

    run_command(
        "1. ALU ORACLE VALIDATION",
        [
            sys.executable,
            "test_generation/"
            "test_alu_oracle.py"
        ]
    )

    run_command(
        "2. GENERATE VERILOG TESTBENCH",
        [
            sys.executable,
            "test_generation/"
            "tb_generator.py",
            VALIDATED_TESTS,
            GENERATED_TB
        ]
    )

    run_command(
        "3. COMPILE GENERATED TESTBENCH",
        [
            "iverilog",
            "-g2012",
            "-o",
            COMPILED_OUTPUT,
            "rtl/alu.v",
            GENERATED_TB
        ]
    )

    run_simulation()

    run_command(
        "5. PARSE SIMULATION RESULT",
        [
            sys.executable,
            "simulation/"
            "generated_result_parser.py",
            SIMULATION_LOG,
            SIMULATION_REPORT
        ]
    )

    run_command(
        "6. EXECUTION CROSS-CHECK",
        [
            sys.executable,
            "test_generation/"
            "validate_generated_execution.py",
            VALIDATED_TESTS,
            SIMULATION_REPORT
        ]
    )

    print()

    print(
        "========================================"
    )

    print(
        "DAY 11 HERMES-TO-SIMULATION "
        "PIPELINE: PASS"
    )

    print(
        "========================================"
    )


if __name__ == "__main__":
    main()
