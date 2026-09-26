import csv
import json
import sys

from pathlib import Path


SOURCE = Path(
    "results/fifo/day20/strategy_comparison.json"
)

OUTPUT = Path(
    "results/fifo/day20/strategy_comparison.csv"
)


def main():

    try:

        data = json.loads(
            SOURCE.read_text()
        )


        fieldnames = [

            "strategy",

            "coverage_percent",

            "covered_points",

            "total_points",

            "stimulus_cycles",

            "unique_behavior_signatures",

            "redundant_cycles",

            "redundancy_percent",

            "coverage_percent_per_stimulus_cycle",
        ]


        with OUTPUT.open(
            "w",
            newline=""
        ) as file_handle:

            writer = csv.DictWriter(

                file_handle,

                fieldnames=fieldnames
            )


            writer.writeheader()


            for strategy in data[
                "strategies"
            ]:

                writer.writerow({

                    key:
                        strategy[
                            key
                        ]

                    for key
                    in fieldnames
                })


    except Exception as error:

        print(
            "DAY 20 CSV GENERATION: FAIL"
        )

        print(
            "ERROR:",
            error
        )

        sys.exit(1)


    print(
        "DAY 20 CSV GENERATION: PASS"
    )

    print(
        "Output:",
        OUTPUT
    )


if __name__ == "__main__":
    main()
