import subprocess
import sys


def run_step(
    title,
    command,
    required=True
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

    if (
        required
        and process.returncode != 0
    ):

        print()

        print(
            f"{title}: FAIL"
        )

        sys.exit(1)

    print()

    print(
        f"{title}: COMPLETE"
    )


def main():

    print(
        "========================================"
    )

    print(
        "DAY 10 - DETERMINISTIC TEST VALIDATION"
    )

    print(
        "========================================"
    )

    run_step(
        "1. DAY 9 BASIC CHECK",
        [
            sys.executable,
            "test_generation/"
            "day9_basic_check.py",
            "results/alu/day9/"
            "candidate_tests.json"
        ]
    )

    run_step(
        "2. DETERMINISTIC VALIDATOR",
        [
            sys.executable,
            "test_generation/"
            "test_validator.py",

            "results/alu/day9/"
            "candidate_tests.json",

            "results/alu/day6/"
            "alu_knowledge.json",

            "results/alu/day7/"
            "verification_objectives.json",

            "results/alu/day10/"
            "validated_tests.json",

            "results/alu/day10/"
            "rejection_report.json",

            "results/alu/day10/"
            "validation_report.json"
        ]
    )

    run_step(
        "3. DUPLICATE CHECK",
        [
            sys.executable,
            "test_generation/"
            "duplicate_checker.py",

            "results/alu/day9/"
            "candidate_tests.json"
        ]
    )

    run_step(
        "4. OBJECTIVE TRACEABILITY",
        [
            sys.executable,
            "test_generation/"
            "objective_traceability.py",

            "results/alu/day7/"
            "verification_objectives.json",

            "results/alu/day10/"
            "validated_tests.json"
        ]
    )

    run_step(
        "5. CORNER CASE CHECK",
        [
            sys.executable,
            "test_generation/"
            "corner_case_checker.py",

            "results/alu/day7/"
            "verification_objectives.json",

            "results/alu/day10/"
            "validated_tests.json"
        ]
    )

    print()
    print(
        "========================================"
    )

    print(
        "DAY 10 VALIDATION PIPELINE: PASS"
    )

    print(
        "========================================"
    )


if __name__ == "__main__":
    main()
