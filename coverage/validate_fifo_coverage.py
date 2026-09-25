import json
import sys

from pathlib import Path


EXPECTED_IDS = {

    "COV_FIFO_001",
    "COV_FIFO_002",
    "COV_FIFO_003",
    "COV_FIFO_004",
    "COV_FIFO_005",
    "COV_FIFO_006",
    "COV_FIFO_007",
    "COV_FIFO_008",
    "COV_FIFO_009",
    "COV_FIFO_010",
}


def main():

    if len(
        sys.argv
    ) != 2:

        print(
            "Usage: python "
            "coverage/validate_fifo_coverage.py "
            "<coverage.json>"
        )

        sys.exit(1)


    try:

        path = Path(
            sys.argv[1]
        )

        if not path.exists():

            raise FileNotFoundError(
                sys.argv[1]
            )


        report = json.loads(
            path.read_text()
        )


        if (
            report.get(
                "dut"
            )
            != "fifo"
        ):

            raise ValueError(
                "Unexpected DUT."
            )


        if (
            report.get(
                "coverage_type"
            )
            !=
            "fifo_functional_coverage"
        ):

            raise ValueError(
                "Unexpected coverage type."
            )


        definitions = set(

            report.get(
                "point_definitions",
                {}
            ).keys()
        )


        if (
            definitions
            != EXPECTED_IDS
        ):

            raise ValueError(
                "Coverage-point definition mismatch."
            )


        covered = set(

            report.get(
                "covered_points",
                []
            )
        )


        missing = set(

            report.get(
                "missing_points",
                []
            )
        )


        if (
            covered & missing
        ):

            raise ValueError(
                "Covered and missing sets overlap."
            )


        if (
            covered | missing
        ) != EXPECTED_IDS:

            raise ValueError(
                "Coverage accounting mismatch."
            )


        if (
            report[
                "total_coverage_points"
            ]
            != 10
        ):

            raise ValueError(
                "Total coverage points must be 10."
            )


        if (
            report[
                "covered_coverage_points"
            ]
            != len(
                covered
            )
        ):

            raise ValueError(
                "Covered-point count mismatch."
            )


        expected_percent = round(

            (
                len(covered)
                / 10
            )
            * 100,

            2
        )


        if (
            report[
                "coverage_percent"
            ]
            != expected_percent
        ):

            raise ValueError(
                "Coverage percentage mismatch."
            )


        expected_complete = (

            len(
                missing
            )
            == 0
        )


        if (
            report[
                "coverage_complete"
            ]
            != expected_complete
        ):

            raise ValueError(
                "coverage_complete mismatch."
            )


        hits = report.get(
            "point_hits",
            {}
        )


        if (
            set(
                hits.keys()
            )
            != EXPECTED_IDS
        ):

            raise ValueError(
                "Point-hit set mismatch."
            )


        for coverage_id in covered:

            if (
                hits[
                    coverage_id
                ]
                <= 0
            ):

                raise ValueError(
                    "Covered point has zero hits."
                )


        for coverage_id in missing:

            if (
                hits[
                    coverage_id
                ]
                != 0
            ):

                raise ValueError(
                    "Missing point has non-zero hits."
                )


    except Exception as error:

        print(
            "FIFO COVERAGE VALIDATION: FAIL"
        )

        print(
            "ERROR:",
            error
        )

        sys.exit(1)


    print(
        "FIFO COVERAGE VALIDATION: PASS"
    )


if __name__ == "__main__":
    main()
