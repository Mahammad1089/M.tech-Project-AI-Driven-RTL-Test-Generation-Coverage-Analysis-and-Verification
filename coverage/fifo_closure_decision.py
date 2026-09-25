import json
import sys

from pathlib import Path


def main():

    if len(
        sys.argv
    ) != 3:

        print(
            "Usage: python "
            "coverage/fifo_closure_decision.py "
            "<coverage.json> "
            "<decision.json>"
        )

        sys.exit(1)


    try:

        coverage = json.loads(

            Path(
                sys.argv[1]
            ).read_text()
        )


        missing = coverage[
            "missing_points"
        ]


        complete = (

            len(
                missing
            )
            == 0
        )


        if complete:

            action = "STOP"

            reason = (
                "All defined FIFO functional "
                "coverage points are covered."
            )

        else:

            action = "CONTINUE"

            reason = (
                "One or more defined FIFO "
                "functional coverage points "
                "remain uncovered."
            )


        report = {

            "coverage_percent":
                coverage[
                    "coverage_percent"
                ],

            "missing_points":
                missing,

            "coverage_complete":
                complete,

            "action":
                action,

            "reason":
                reason,
        }


    except Exception as error:

        print(
            "FIFO CLOSURE DECISION: FAIL"
        )

        print(
            "ERROR:",
            error
        )

        sys.exit(1)


    Path(
        sys.argv[2]
    ).write_text(

        json.dumps(
            report,
            indent=4
        )
    )


    print(
        "FIFO CLOSURE DECISION: PASS"
    )

    print(
        "Decision:",
        action
    )

    print(
        "Reason:",
        reason
    )


if __name__ == "__main__":
    main()
