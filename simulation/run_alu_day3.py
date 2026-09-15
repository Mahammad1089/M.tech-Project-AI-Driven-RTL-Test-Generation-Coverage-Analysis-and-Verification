import subprocess
import sys
from pathlib import Path


RTL = "rtl/alu.v"

TESTBENCH = (
    "testbench/automated/"
    "tb_alu_selfcheck.v"
)

OUTPUT = (
    "results/alu/day3/"
    "alu_python.out"
)


def compile_verilog():

    command = [
        "iverilog",
        "-o",
        OUTPUT,
        RTL,
        TESTBENCH
    ]

    print(
        "===================================="
    )

    print(
        "COMPILING ALU VERIFICATION"
    )

    print(
        "===================================="
    )

    result = subprocess.run(
        command,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:

        print(
            "COMPILATION: FAIL"
        )

        print(
            result.stderr
        )

        return False

    print(
        "COMPILATION: PASS"
    )

    return True


def run_simulation():

    result = subprocess.run(
        [
            "vvp",
            OUTPUT
        ],
        capture_output=True,
        text=True
    )

    print()

    print(
        "===================================="
    )

    print(
        "SIMULATION OUTPUT"
    )

    print(
        "===================================="
    )

    print(
        result.stdout
    )

    return result


def main():

    Path(
        "results/alu/day3"
    ).mkdir(
        parents=True,
        exist_ok=True
    )


    if not compile_verilog():

        sys.exit(1)


    result = run_simulation()


    log_file = Path(
        "results/alu/day3/"
        "python_simulation.log"
    )


    log_file.write_text(
        result.stdout
    )


    if (
        result.returncode == 0
        and
        "FAILED TESTS = 0"
        in result.stdout
    ):

        print(
            "PYTHON ALU VERIFICATION: PASS"
        )

        sys.exit(0)

    else:

        print(
            "PYTHON ALU VERIFICATION: FAIL"
        )

        sys.exit(1)


if __name__ == "__main__":

    main()
