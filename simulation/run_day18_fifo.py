import json
import subprocess
import sys
from pathlib import Path


RESULT_DIR = Path(
    "results/fifo/day18"
)

RTL_FILE = Path(
    "rtl/fifo.v"
)

TB_FILE = Path(
    "testbench/automated/tb_fifo_day18.v"
)

SIM_FILE = RESULT_DIR / "fifo_day18.out"

LOG_FILE = RESULT_DIR / "fifo_day18.log"

KNOWLEDGE_FILE = (
    RESULT_DIR
    / "fifo_knowledge.json"
)


def run_command(
    command,
    description
):

    print()
    print(
        "=" * 72
    )

    print(
        description
    )

    print(
        "=" * 72
    )

    print(
        "COMMAND:",
        " ".join(command)
    )

    result = subprocess.run(
        command,
        text=True,
        capture_output=True
    )

    if result.stdout:

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

        print()
        print(
            f"{description}: FAIL"
        )

        sys.exit(
            result.returncode
        )

    print(
        f"{description}: PASS"
    )

    return result


def main():

    RESULT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )


    run_command(
        [
            "iverilog",
            "-g2012",
            "-o",
            str(SIM_FILE),
            str(RTL_FILE),
            str(TB_FILE)
        ],
        "FIFO COMPILATION"
    )


    print()
    print(
        "=" * 72
    )

    print(
        "FIFO SIMULATION"
    )

    print(
        "=" * 72
    )

    simulation = subprocess.run(
        [
            "vvp",
            str(SIM_FILE)
        ],
        text=True,
        capture_output=True
    )

    LOG_FILE.write_text(
        simulation.stdout
        + simulation.stderr
    )

    print(
        simulation.stdout,
        end=""
    )

    if simulation.stderr:

        print(
            simulation.stderr,
            end=""
        )

    if simulation.returncode != 0:

        print(
            "FIFO SIMULATION: FAIL"
        )

        sys.exit(
            simulation.returncode
        )


    if (
        "DAY 18 FIFO VERIFICATION PASS"
        not in simulation.stdout
    ):

        print(
            "FIFO SIMULATION: FAIL"
        )

        print(
            "PASS marker not found."
        )

        sys.exit(1)


    if (
        "FAILED CHECKS = 0"
        not in simulation.stdout
    ):

        print(
            "FIFO SIMULATION: FAIL"
        )

        print(
            "Zero-failure marker not found."
        )

        sys.exit(1)


    print(
        "FIFO SIMULATION: PASS"
    )


    run_command(
        [
            sys.executable,
            "parser/fifo_knowledge.py"
        ],
        "FIFO KNOWLEDGE GENERATION"
    )


    run_command(
        [
            sys.executable,
            "parser/validate_fifo_knowledge.py",
            str(KNOWLEDGE_FILE)
        ],
        "FIFO KNOWLEDGE VALIDATION"
    )


    print()
    print(
        "=" * 72
    )

    print(
        "DAY 18 FIFO PIPELINE: PASS"
    )

    print(
        "=" * 72
    )


if __name__ == "__main__":
    main()
