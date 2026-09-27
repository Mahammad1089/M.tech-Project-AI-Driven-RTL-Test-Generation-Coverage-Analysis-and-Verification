import subprocess
import sys


STEPS = [

    (
        "Day-23 integration",
        [
            sys.executable,
            "run_day23.py"
        ]
    ),

    (
        "Collect tool versions",
        [
            sys.executable,
            "docs/final/"
            "collect_tool_versions.py"
        ]
    ),

    (
        "Generate final artifact manifest",
        [
            sys.executable,
            "docs/final/"
            "generate_final_manifest.py"
        ]
    ),

    (
        "Generate final project summary",
        [
            sys.executable,
            "docs/final/"
            "generate_final_summary.py"
        ]
    ),

    (
        "Validate final project",
        [
            sys.executable,
            "docs/final/"
            "validate_final_project.py"
        ]
    )
]


def main():

    for index, (
        description,
        command
    ) in enumerate(
        STEPS,
        start=1
    ):

        print()
        print(
            "=" * 72
        )

        print(
            f"DAY 24 STEP {index}: "
            f"{description}"
        )

        print(
            "=" * 72
        )

        result = subprocess.run(
            command
        )

        if (
            result.returncode
            != 0
        ):

            print()
            print(
                "DAY 24 FINAL FREEZE: FAIL"
            )

            print(
                "Failed stage:",
                description
            )

            sys.exit(
                result.returncode
            )

    print()
    print(
        "=" * 72
    )

    print(
        "DAY 24 FINAL FREEZE: PASS"
    )

    print(
        "PROJECT IMPLEMENTATION: COMPLETE"
    )

    print(
        "=" * 72
    )


if __name__ == "__main__":

    main()
