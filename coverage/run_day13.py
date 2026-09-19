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

COVERAGE = (
    "results/alu/day12/"
    "functional_coverage.json"
)

GAPS = (
    "results/alu/day13/"
    "coverage_gaps.json"
)

FEEDBACK_INPUT = (
    "results/alu/day13/"
    "day14_feedback_input.json"
)


def run_step(
    title,
    command
):
    print()

    print(
        "=" * 70
    )

    print(
        title
    )

    print(
        "=" * 70
    )

    result = subprocess.run(
        command
    )

    if result.returncode != 0:

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
        "results/alu/day13"
    ).mkdir(
        parents=True,
        exist_ok=True
    )

    print(
        "========================================"
    )

    print(
        "DAY 13 - COVERAGE GAP ANALYSIS"
    )

    print(
        "========================================"
    )

    run_step(
        "1. GENERATE COVERAGE GAPS",
        [
            sys.executable,
            "coverage/gap_analyzer.py",
            KNOWLEDGE,
            OBJECTIVES,
            COVERAGE,
            GAPS
        ]
    )

    run_step(
        "2. VALIDATE GAP REPORT",
        [
            sys.executable,
            "coverage/validate_gaps.py",
            GAPS
        ]
    )

    run_step(
        "3. VALIDATE GAP SOURCE",
        [
            sys.executable,
            "coverage/"
            "validate_gap_source.py",
            COVERAGE,
            GAPS
        ]
    )

    run_step(
        "4. PRINT GAP REPORT",
        [
            sys.executable,
            "coverage/print_gaps.py",
            GAPS
        ]
    )

    run_step(
        "5. PREPARE DAY-14 INPUT",
        [
            sys.executable,
            "coverage/"
            "prepare_feedback_input.py",
            GAPS,
            FEEDBACK_INPUT
        ]
    )

    print()

    print(
        "========================================"
    )

    print(
        "DAY 13 COVERAGE GAP "
        "PIPELINE: PASS"
    )

    print(
        "========================================"
    )


if __name__ == "__main__":
    main()
