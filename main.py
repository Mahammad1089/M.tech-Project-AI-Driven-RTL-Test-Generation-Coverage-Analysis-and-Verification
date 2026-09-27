import subprocess
import sys


def main():

    print()
    print(
        "=" * 72
    )

    print(
        "AI-DRIVEN RTL VERIFICATION FRAMEWORK"
    )

    print(
        "M.Tech Project Integration"
    )

    print(
        "=" * 72
    )

    result = subprocess.run(
        [
            sys.executable,
            "run_day23.py"
        ]
    )

    if (
        result.returncode
        != 0
    ):

        print()
        print(
            "PROJECT INTEGRATION: FAIL"
        )

        sys.exit(
            result.returncode
        )

    print()
    print(
        "=" * 72
    )

    print(
        "PROJECT INTEGRATION: PASS"
    )

    print(
        "Validated ALU, FSM, FIFO "
        "and experimental evidence."
    )

    print(
        "=" * 72
    )


if __name__ == "__main__":

    main()
