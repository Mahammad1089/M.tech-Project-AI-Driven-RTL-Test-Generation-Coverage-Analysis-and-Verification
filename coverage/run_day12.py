import subprocess
import sys
from pathlib import Path


KNOWLEDGE = (
    "results/alu/day6/"
    "alu_knowledge.json"
)

OBJECTIVES = (
    "results/alu/day7/"
    "verification_objectives.json"
)

VALIDATED_TESTS = (
    "results/alu/day10/"
    "validated_tests.json"
)

SIMULATION_REPORT = (
    "results/alu/day11/"
    "generated_simulation_report.json"
)

COVERAGE_REPORT = (
    "results/alu/day12/"
    "functional_coverage.json"
)

COVERAGE_CSV = (
    "results/alu/day12/"
    "operation_coverage.csv"
)


def run_step(
    title,
    command
):

    print()

    print(
        "=" * 64
    )

    print(
        title
    )

    print(
        "=" * 64
    )

    process = subprocess.run(
        command
    )

    if (
        process.returncode
        != 0
    ):

        print()

        print(
            f"{title}: FAIL"
        )

        sys.exit(1)

    print()

    print(
        f"{title}: PASS"
    )


def main():

    Path(
        "results/alu/day12"
    ).mkdir(
        parents=True,
        exist_ok=True
    )

    print(
        "========================================"
    )

    print(
        "DAY 12 - FUNCTIONAL "
        "COVERAGE ANALYSIS"
    )

    print(
        "========================================"
    )

    run_step(
        "1. GENERATE FUNCTIONAL COVERAGE",
        [
            sys.executable,
            "coverage/"
            "functional_coverage.py",
            KNOWLEDGE,
            OBJECTIVES,
            VALIDATED_TESTS,
            COVERAGE_REPORT
        ]
    )

    run_step(
        "2. VALIDATE COVERAGE REPORT",
        [
            sys.executable,
            "coverage/"
            "validate_coverage.py",
            COVERAGE_REPORT
        ]
    )

    run_step(
        "3. VALIDATE EXECUTION SOURCE",
        [
            sys.executable,
            "coverage/"
            "validate_execution_source.py",
            VALIDATED_TESTS,
            SIMULATION_REPORT,
            COVERAGE_REPORT
        ]
    )

    run_step(
        "4. PRINT COVERAGE REPORT",
        [
            sys.executable,
            "coverage/"
            "print_coverage.py",
            COVERAGE_REPORT
        ]
    )

    run_step(
        "5. GENERATE COVERAGE CSV",
        [
            sys.executable,
            "coverage/"
            "coverage_to_csv.py",
            COVERAGE_REPORT,
            COVERAGE_CSV
        ]
    )

    print()

    print(
        "========================================"
    )

    print(
        "DAY 12 FUNCTIONAL "
        "COVERAGE PIPELINE: PASS"
    )

    print(
        "========================================"
    )


if __name__ == "__main__":
    main()
