import json
import sys

from pathlib import Path


def load_json(
    path
):

    file_path = Path(
        path
    )

    if not file_path.exists():

        raise FileNotFoundError(
            path
        )

    return json.loads(
        file_path.read_text()
    )


def main():

    if len(
        sys.argv
    ) != 3:

        print(
            "Usage: python "
            "coverage/fifo_gap_analyzer.py "
            "<coverage.json> "
            "<gaps.json>"
        )

        sys.exit(1)


    try:

        coverage = load_json(
            sys.argv[1]
        )


        definitions = coverage[
            "point_definitions"
        ]


        missing = coverage[
            "missing_points"
        ]


        gaps = []


        for coverage_id in missing:

            if (
                coverage_id
                not in definitions
            ):

                raise ValueError(
                    "Unknown coverage gap: "
                    f"{coverage_id}"
                )


            gaps.append({

                "coverage_id":
                    coverage_id,

                "behavior":
                    definitions[
                        coverage_id
                    ],

                "status":
                    "uncovered",
            })


        gap_status = (

            "NO_GAPS"

            if len(
                gaps
            ) == 0

            else "GAPS_FOUND"
        )


        report = {

            "dut":
                "fifo",

            "analysis_type":
                "fifo_functional_coverage_gap_analysis",

            "source_coverage_percent":
                coverage[
                    "coverage_percent"
                ],

            "gap_count":
                len(gaps),

            "gaps":
                gaps,

            "gap_status":
                gap_status,

            "hermes_used":
                False,

            "new_tests_generated":
                False,

            "coverage_remeasured":
                False,
        }


    except Exception as error:

        print(
            "FIFO GAP ANALYSIS: FAIL"
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
        "FIFO GAP ANALYSIS: PASS"
    )

    print(
        "Gap status :",
        gap_status
    )

    print(
        "Gap count  :",
        len(gaps)
    )


if __name__ == "__main__":
    main()
