import json
import sys

from pathlib import Path


def load_json(
    path
):

    return json.loads(
        Path(
            path
        ).read_text()
    )


def main():

    if len(
        sys.argv
    ) != 4:

        print(
            "Usage: python "
            "coverage/compare_fifo_coverage.py "
            "<before.json> "
            "<after.json> "
            "<comparison.json>"
        )

        sys.exit(1)


    try:

        before = load_json(
            sys.argv[1]
        )

        after = load_json(
            sys.argv[2]
        )


        before_percent = before[
            "coverage_percent"
        ]

        after_percent = after[
            "coverage_percent"
        ]


        delta = round(

            after_percent
            - before_percent,

            2
        )


        if delta > 0:

            trend = "IMPROVED"

        elif delta == 0:

            trend = "UNCHANGED"

        else:

            trend = "REGRESSION"


        report = {

            "before_coverage_percent":
                before_percent,

            "after_coverage_percent":
                after_percent,

            "coverage_delta":
                delta,

            "before_missing_points":
                before[
                    "missing_points"
                ],

            "after_missing_points":
                after[
                    "missing_points"
                ],

            "trend":
                trend,
        }


    except Exception as error:

        print(
            "FIFO COVERAGE COMPARISON: FAIL"
        )

        print(
            "ERROR:",
            error
        )

        sys.exit(1)


    Path(
        sys.argv[3]
    ).write_text(

        json.dumps(
            report,
            indent=4
        )
    )


    print(
        "FIFO COVERAGE COMPARISON: PASS"
    )

    print(
        "Trend:",
        trend
    )

    print(
        "Delta:",
        delta
    )


if __name__ == "__main__":
    main()
