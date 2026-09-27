import json
import sys

from pathlib import Path


BASE = Path(
    "results/integration/day23"
)

EXECUTION_REPORT = (
    BASE
    / "day23_execution_report.json"
)

STRUCTURE_REPORT = (
    BASE
    / "structure_validation.json"
)

HISTORY_REPORT = (
    BASE
    / "historical_results_validation.json"
)

OUTPUT = (
    BASE
    / "day23_summary.json"
)


def load(path):

    if not path.exists():

        raise FileNotFoundError(
            path
        )

    return json.loads(
        path.read_text()
    )


def main():

    try:

        execution = load(
            EXECUTION_REPORT
        )

        structure = load(
            STRUCTURE_REPORT
        )

        history = load(
            HISTORY_REPORT
        )

        if (
            execution["status"]
            != "PASS"
        ):

            raise ValueError(
                "Integration execution "
                "is not PASS."
            )

        if (
            structure["status"]
            != "PASS"
        ):

            raise ValueError(
                "Structure validation "
                "is not PASS."
            )

        if (
            history["status"]
            != "PASS"
        ):

            raise ValueError(
                "Historical validation "
                "is not PASS."
            )

        summary = {

            "day": 23,

            "project":
                "AI-Driven RTL Test Generation, "
                "Coverage Analysis and Verification",

            "stage":
                "one-command integration",

            "duts": [
                "alu",
                "fsm",
                "fifo"
            ],

            "validated_milestones":
                len(
                    history[
                        "milestones"
                    ]
                ),

            "integration_steps":
                execution[
                    "executed_steps"
                ],

            "all_integration_steps_executed":
                execution[
                    "all_required_steps_executed"
                ],

            "one_command_entry":
                "python main.py",

            "rtl_modified":
                False,

            "new_tests_generated":
                False,

            "coverage_remeasured":
                False,

            "hermes_used":
                False,

            "negative_test_supported":
                True,

            "next_stage":
                "DAY_24_FINAL_FREEZE_AND_DOCUMENTATION",

            "status":
                "PASS"
        }

    except Exception as error:

        print(
            "DAY 23 SUMMARY: FAIL"
        )

        print(
            "ERROR:",
            error
        )

        sys.exit(1)

    OUTPUT.write_text(
        json.dumps(
            summary,
            indent=4
        )
    )

    print(
        json.dumps(
            summary,
            indent=4
        )
    )

    print()

    print(
        "DAY 23 SUMMARY: PASS"
    )


if __name__ == "__main__":

    main()
