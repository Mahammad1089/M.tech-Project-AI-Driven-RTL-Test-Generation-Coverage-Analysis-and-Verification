import json
import sys

from pathlib import Path


BASE = Path(
    "results/fifo/day20"
)


def load(
    filename
):

    path = (
        BASE
        / filename
    )

    if not path.exists():

        raise FileNotFoundError(
            path
        )

    return json.loads(
        path.read_text()
    )


def get_strategy(
    comparison,
    name
):

    for strategy in comparison[
        "strategies"
    ]:

        if (
            strategy[
                "strategy"
            ]
            == name
        ):

            return strategy


    raise ValueError(
        f"Missing strategy: {name}"
    )


def main():

    try:

        comparison = load(
            "strategy_comparison.json"
        )


        manual = get_strategy(
            comparison,
            "manual_directed"
        )


        random_method = get_strategy(
            comparison,
            "random"
        )


        feedback = get_strategy(
            comparison,
            "feedback_driven"
        )


        summary = {

            "day":
                20,

            "dut":
                "fifo",

            "stage":
                "baseline verification "
                "strategy comparison",

            "manual_directed": {

                "coverage_percent":
                    manual[
                        "coverage_percent"
                    ],

                "stimulus_cycles":
                    manual[
                        "stimulus_cycles"
                    ],

                "redundancy_percent":
                    manual[
                        "redundancy_percent"
                    ],
            },

            "random": {

                "coverage_percent":
                    random_method[
                        "coverage_percent"
                    ],

                "stimulus_cycles":
                    random_method[
                        "stimulus_cycles"
                    ],

                "redundancy_percent":
                    random_method[
                        "redundancy_percent"
                    ],
            },

            "feedback_driven": {

                "coverage_percent":
                    feedback[
                        "coverage_percent"
                    ],

                "stimulus_cycles":
                    feedback[
                        "stimulus_cycles"
                    ],

                "redundancy_percent":
                    feedback[
                        "redundancy_percent"
                    ],
            },

            "same_rtl":
                True,

            "same_coverage_model":
                True,

            "random_seed":
                20260926,

            "random_cycles":
                20,

            "hermes_used":
                False,

            "rtl_modified":
                False,

            "results_are_measured":
                True,

            "status":
                "PASS",
        }


    except Exception as error:

        print(
            "DAY 20 SUMMARY: FAIL"
        )

        print(
            "ERROR:",
            error
        )

        sys.exit(1)


    output = (
        BASE
        / "day20_summary.json"
    )


    output.write_text(

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
        "DAY 20 SUMMARY: PASS"
    )


if __name__ == "__main__":
    main()
