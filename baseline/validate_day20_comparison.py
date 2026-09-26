import json
import sys

from pathlib import Path


BASE = Path(
    "results/fifo/day20"
)


EXPECTED = {

    "manual_directed",

    "random",

    "feedback_driven",
}


def main():

    try:

        report = json.loads(

            (
                BASE
                / "strategy_comparison.json"
            ).read_text()
        )


        strategies = report[
            "strategies"
        ]


        names = {

            item[
                "strategy"
            ]

            for item
            in strategies
        }


        if names != EXPECTED:

            raise ValueError(
                "Strategy set mismatch."
            )


        for item in strategies:

            coverage = item[
                "coverage_percent"
            ]

            total_points = item[
                "total_points"
            ]

            covered_points = item[
                "covered_points"
            ]

            stimulus_cycles = item[
                "stimulus_cycles"
            ]


            if (
                coverage < 0
                or coverage > 100
            ):

                raise ValueError(
                    "Invalid coverage percentage."
                )


            if total_points != 10:

                raise ValueError(
                    "Coverage model mismatch."
                )


            if (
                covered_points < 0
                or covered_points > 10
            ):

                raise ValueError(
                    "Invalid covered-point count."
                )


            expected_coverage = round(

                (
                    covered_points
                    / total_points
                )
                * 100,

                2
            )


            if (
                coverage
                != expected_coverage
            ):

                raise ValueError(
                    "Coverage arithmetic mismatch."
                )


            if stimulus_cycles <= 0:

                raise ValueError(
                    "Strategy has no stimulus cycles."
                )


        if (
            report[
                "rtl_modified"
            ]
            is not False
        ):

            raise ValueError(
                "Day 20 must not modify RTL."
            )


    except Exception as error:

        print(
            "DAY 20 COMPARISON VALIDATION: FAIL"
        )

        print(
            "ERROR:",
            error
        )

        sys.exit(1)


    print(
        "DAY 20 COMPARISON VALIDATION: PASS"
    )


if __name__ == "__main__":
    main()
