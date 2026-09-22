import subprocess
import sys
from pathlib import Path


RTL = (
    "rtl/fsm_1011.v"
)

TB = (
    "testbench/automated/"
    "tb_fsm_1011_selfcheck.v"
)

OUTPUT_DIR = Path(
    "results/fsm/day16"
)

SIM_OUT = OUTPUT_DIR / (
    "fsm_day16_integrated.out"
)

SIM_LOG = OUTPUT_DIR / (
    "fsm_day16_integrated.log"
)

SIM_REPORT = OUTPUT_DIR / (
    "fsm_baseline_report.json"
)

KNOWLEDGE = OUTPUT_DIR / (
    "fsm_knowledge.json"
)


def run_step(
    title,
    command
):

    print()

    print(
        "=" * 72
    )

    print(
        title
    )

    print(
        "=" * 72
    )

    result = subprocess.run(
        command
    )

    if result.returncode != 0:

        print(
            f"{title}: FAIL"
        )

        sys.exit(1)

    print(
        f"{title}: PASS"
    )


def compile_fsm():

    print()

    print(
        "=" * 72
    )

    print(
        "1. COMPILE FSM"
    )

    print(
        "=" * 72
    )

    result = subprocess.run([
        "iverilog",
        "-g2012",
        "-o",
        str(SIM_OUT),
        RTL,
        TB
    ])

    if result.returncode != 0:

        print(
            "FSM COMPILATION: FAIL"
        )

        sys.exit(1)

    print(
        "FSM COMPILATION: PASS"
    )


def simulate_fsm():

    print()

    print(
        "=" * 72
    )

    print(
        "2. SIMULATE FSM"
    )

    print(
        "=" * 72
    )

    result = subprocess.run(
        [
            "vvp",
            str(SIM_OUT)
        ],
        capture_output=True,
        text=True
    )

    SIM_LOG.write_text(
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
            "FSM SIMULATION: FAIL"
        )

        sys.exit(1)

    print(
        "FSM SIMULATION: PASS"
    )


def main():

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    print(
        "=========================================="
    )

    print(
        "DAY 16 - FSM BENCHMARK"
    )

    print(
        "=========================================="
    )

    compile_fsm()

    simulate_fsm()

    run_step(
        "3. PARSE FSM RESULT",
        [
            sys.executable,
            "simulation/"
            "fsm_result_parser.py",
            str(SIM_LOG),
            str(SIM_REPORT)
        ]
    )

    run_step(
        "4. GENERATE FSM KNOWLEDGE",
        [
            sys.executable,
            "parser/"
            "fsm_analyzer.py",
            str(KNOWLEDGE)
        ]
    )

    run_step(
        "5. VALIDATE FSM KNOWLEDGE",
        [
            sys.executable,
            "parser/"
            "validate_fsm_day16.py",
            str(KNOWLEDGE)
        ]
    )

    run_step(
        "6. PRINT FSM KNOWLEDGE",
        [
            sys.executable,
            "parser/"
            "print_fsm_knowledge.py",
            str(KNOWLEDGE)
        ]
    )

    print()

    print(
        "=========================================="
    )

    print(
        "DAY 16 FSM PIPELINE: PASS"
    )

    print(
        "=========================================="
    )


if __name__ == "__main__":
    main()
