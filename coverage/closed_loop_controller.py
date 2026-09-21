import subprocess
import sys
from pathlib import Path


INITIAL_TESTS = (
    "results/alu/day10/"
    "validated_tests.json"
)

TARGETED_TESTS = (
    "results/alu/day14/"
    "targeted_validated_tests.json"
)

COMBINED_TESTS = (
    "results/alu/day15/"
    "combined_validated_tests.json"
)

REVALIDATED_TESTS = (
    "results/alu/day15/"
    "revalidated_tests.json"
)

REJECTED = (
    "results/alu/day15/"
    "revalidation_rejected.json"
)

REVALIDATION_REPORT = (
    "results/alu/day15/"
    "revalidation_report.json"
)

TB_FILE = (
    "testbench/generated/"
    "tb_alu_day15_closed_loop.v"
)

SIM_OUT = (
    "results/alu/day15/"
    "alu_closed_loop.out"
)

SIM_LOG = (
    "results/alu/day15/"
    "closed_loop_simulation.log"
)

SIM_REPORT = (
    "results/alu/day15/"
    "closed_loop_simulation_report.json"
)

KNOWLEDGE = (
    "results/alu/day6/"
    "alu_knowledge.json"
)

OBJECTIVES = (
    "results/alu/day7/"
    "verification_objectives.json"
)

OLD_COVERAGE = (
    "results/alu/day12/"
    "functional_coverage.json"
)

NEW_COVERAGE = (
    "results/alu/day15/"
    "closed_loop_coverage.json"
)

OLD_GAPS = (
    "results/alu/day13/"
    "coverage_gaps.json"
)

NEW_GAPS = (
    "results/alu/day15/"
    "remaining_gaps.json"
)

COVERAGE_COMPARISON = (
    "results/alu/day15/"
    "coverage_comparison.json"
)

GAP_COMPARISON = (
    "results/alu/day15/"
    "gap_comparison.json"
)

DECISION = (
    "results/alu/day15/"
    "closure_decision.json"
)


def run_step(
    title,
    command
):
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)

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


def compile_verilog():
    print()
    print("=" * 72)
    print("5. COMPILE GENERATED VERILOG")
    print("=" * 72)

    result = subprocess.run([
        "iverilog",
        "-g2012",
        "-o",
        SIM_OUT,
        "rtl/alu.v",
        TB_FILE
    ])

    if result.returncode != 0:
        print(
            "VERILOG COMPILATION: FAIL"
        )
        sys.exit(1)

    print(
        "VERILOG COMPILATION: PASS"
    )


def run_simulation():
    print()
    print("=" * 72)
    print("6. RUN CLOSED-LOOP SIMULATION")
    print("=" * 72)

    result = subprocess.run(
        [
            "vvp",
            SIM_OUT
        ],
        capture_output=True,
        text=True
    )

    Path(
        SIM_LOG
    ).write_text(
        result.stdout
        + result.stderr
    )

    print(
        result.stdout,
        end=""
    )

    if result.stderr:
        print(
            result.stderr,
            end=""
        )

    if result.returncode != 0:
        print(
            "CLOSED-LOOP SIMULATION: FAIL"
        )
        sys.exit(1)

    print(
        "CLOSED-LOOP SIMULATION: PASS"
    )


def main():
    Path(
        "results/alu/day15"
    ).mkdir(
        parents=True,
        exist_ok=True
    )

    print(
        "=========================================="
    )
    print(
        "DAY 15 - CLOSED-LOOP CONTROLLER"
    )
    print(
        "=========================================="
    )

    run_step(
        "1. MERGE TEST SETS",
        [
            sys.executable,
            "test_generation/"
            "merge_test_sets.py",
            INITIAL_TESTS,
            TARGETED_TESTS,
            COMBINED_TESTS
        ]
    )

    run_step(
        "2. REVALIDATE COMBINED TESTS",
        [
            sys.executable,
            "test_generation/"
            "test_validator.py",
            COMBINED_TESTS,
            KNOWLEDGE,
            OBJECTIVES,
            REVALIDATED_TESTS,
            REJECTED,
            REVALIDATION_REPORT
        ]
    )

    run_step(
        "3. VALIDATE ALU ORACLE",
        [
            sys.executable,
            "test_generation/"
            "test_alu_oracle.py"
        ]
    )

    run_step(
        "4. GENERATE VERILOG TESTBENCH",
        [
            sys.executable,
            "test_generation/"
            "tb_generator.py",
            REVALIDATED_TESTS,
            TB_FILE
        ]
    )

    compile_verilog()

    run_simulation()

    run_step(
        "7. PARSE SIMULATION",
        [
            sys.executable,
            "simulation/"
            "generated_result_parser.py",
            SIM_LOG,
            SIM_REPORT
        ]
    )

    run_step(
        "8. VALIDATE EXECUTION",
        [
            sys.executable,
            "test_generation/"
            "validate_day15_execution.py",
            REVALIDATED_TESTS,
            SIM_REPORT
        ]
    )

    run_step(
        "9. RECALCULATE COVERAGE",
        [
            sys.executable,
            "coverage/"
            "functional_coverage.py",
            KNOWLEDGE,
            OBJECTIVES,
            REVALIDATED_TESTS,
            NEW_COVERAGE
        ]
    )

    run_step(
        "10. VALIDATE COVERAGE",
        [
            sys.executable,
            "coverage/"
            "validate_coverage.py",
            NEW_COVERAGE
        ]
    )

    run_step(
        "11. REANALYZE GAPS",
        [
            sys.executable,
            "coverage/"
            "gap_analyzer.py",
            KNOWLEDGE,
            OBJECTIVES,
            NEW_COVERAGE,
            NEW_GAPS
        ]
    )

    run_step(
        "12. VALIDATE REMAINING GAPS",
        [
            sys.executable,
            "coverage/"
            "validate_gaps.py",
            NEW_GAPS
        ]
    )

    run_step(
        "13. COMPARE COVERAGE",
        [
            sys.executable,
            "coverage/"
            "compare_coverage.py",
            OLD_COVERAGE,
            NEW_COVERAGE,
            COVERAGE_COMPARISON
        ]
    )

    run_step(
        "14. COMPARE GAPS",
        [
            sys.executable,
            "coverage/"
            "compare_gaps.py",
            OLD_GAPS,
            NEW_GAPS,
            GAP_COMPARISON
        ]
    )

    run_step(
        "15. MAKE CLOSURE DECISION",
        [
            sys.executable,
            "coverage/"
            "closure_decision.py",
            NEW_COVERAGE,
            NEW_GAPS,
            "1",
            DECISION
        ]
    )

    print()
    print(
        "=========================================="
    )
    print(
        "DAY 15 CLOSED-LOOP PIPELINE: PASS"
    )
    print(
        "=========================================="
    )


if __name__ == "__main__":
    main()
