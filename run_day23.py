import json
import subprocess
import sys

from pathlib import Path


RESULT_DIR = Path(
    "results/integration/day23"
)

OUTPUT = (
    RESULT_DIR
    / "day23_execution_report.json"
)


STEPS = [

    (
        "Project structure validation",
        [
            sys.executable,
            "integration_validator.py"
        ]
    ),

    (
        "Historical result validation",
        [
            sys.executable,
            "validate_project_results.py"
        ]
    ),

    (
        "Day 20 comparison validation",
        [
            sys.executable,
            "baseline/"
            "validate_day20_comparison.py"
        ]
    ),

    (
        "Day 21 experiment validation",
        [
            sys.executable,
            "baseline/"
            "validate_day21_experiments.py"
        ]
    ),

    (
        "Day 22 graph validation",
        [
            sys.executable,
            "graphs/"
            "validate_day22_graphs.py"
        ]
    ),
]


def execute_step(
    index,
    description,
    command
):

    print()
    print(
        "=" * 72
    )

    print(
        f"STEP {index}: "
        f"{description}"
    )

    print(
        "=" * 72
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

    return {
        "step":
            index,

        "description":
            description,

        "command":
            command,

        "return_code":
            result.returncode,

        "status":
            "PASS"
            if result.returncode == 0
            else "FAIL"
    }


def main():

    RESULT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    results = []

    overall_pass = True

    for index, (
        description,
        command
    ) in enumerate(
        STEPS,
        start=1
    ):

        result = execute_step(
            index,
            description,
            command
        )

        results.append(
            result
        )

        if (
            result[
                "status"
            ]
            != "PASS"
        ):

            overall_pass = False

            break

    report = {

        "day": 23,

        "project":
            "AI-Driven RTL Test Generation, "
            "Coverage Analysis and Verification",

        "mode":
            "integration_validation",

        "steps":
            results,

        "total_configured_steps":
            len(STEPS),

        "executed_steps":
            len(results),

        "all_required_steps_executed":
            len(results)
            == len(STEPS),

        "rtl_modified":
            False,

        "new_tests_generated":
            False,

        "coverage_remeasured":
            False,

        "hermes_used":
            False,

        "status":
            "PASS"
            if (
                overall_pass
                and len(results)
                == len(STEPS)
            )
            else "FAIL"
    }

    OUTPUT.write_text(
        json.dumps(
            report,
            indent=4
        )
    )

    print()
    print(
        "=" * 72
    )

    if (
        report["status"]
        == "PASS"
    ):

        print(
            "DAY 23 INTEGRATION: PASS"
        )

    else:

        print(
            "DAY 23 INTEGRATION: FAIL"
        )

    print(
        "Executed steps:",
        len(results),
        "/",
        len(STEPS)
    )

    print(
        "Report:",
        OUTPUT
    )

    print(
        "=" * 72
    )

    if (
        report["status"]
        != "PASS"
    ):

        sys.exit(1)


if __name__ == "__main__":

    main()
