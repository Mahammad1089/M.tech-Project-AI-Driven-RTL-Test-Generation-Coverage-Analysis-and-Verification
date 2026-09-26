import json
import sys

from pathlib import Path


DAY20 = Path(
    "results/fifo/day20"
)

DAY19 = Path(
    "results/fifo/day19"
)


def load(
    path
):

    if not path.exists():

        raise FileNotFoundError(
            path
        )

    return json.loads(
        path.read_text()
    )


def build_strategy(
    name,
    coverage,
    statistics
):

    stimulus_cycles = statistics[
        "stimulus_cycles"
    ]


    coverage_percent = coverage[
        "coverage_percent"
    ]


    if stimulus_cycles == 0:

        coverage_per_cycle = 0.0

    else:

        coverage_per_cycle = round(

            coverage_percent
            / stimulus_cycles,

            4
        )


    return {

        "strategy":
            name,

        "coverage_percent":
            coverage_percent,

        "covered_points":
            coverage[
                "covered_coverage_points"
            ],

        "total_points":
            coverage[
                "total_coverage_points"
            ],

        "missing_points":
            coverage[
                "missing_points"
            ],

        "stimulus_cycles":
            stimulus_cycles,

        "unique_behavior_signatures":
            statistics[
                "unique_behavior_signatures"
            ],

        "redundant_cycles":
            statistics[
                "redundant_cycles"
            ],

        "redundancy_percent":
            statistics[
                "redundancy_percent"
            ],

        "coverage_percent_per_stimulus_cycle":
            coverage_per_cycle,
    }


def main():

    try:

        manual_cov = load(
            DAY20
            / "manual_coverage.json"
        )

        random_cov = load(
            DAY20
            / "random_coverage.json"
        )

        feedback_cov = load(
            DAY19
            / "fifo_closed_coverage.json"
        )


        manual_stats = load(
            DAY20
            / "manual_statistics.json"
        )

        random_stats = load(
            DAY20
            / "random_statistics.json"
        )

        feedback_stats = load(
            DAY20
            / "feedback_statistics.json"
        )


        methods = [

            build_strategy(
                "manual_directed",
                manual_cov,
                manual_stats
            ),

            build_strategy(
                "random",
                random_cov,
                random_stats
            ),

            build_strategy(
                "feedback_driven",
                feedback_cov,
                feedback_stats
            ),
        ]


        report = {

            "day":
                20,

            "dut":
                "fifo",

            "comparison_type":
                "verification_strategy_comparison",

            "coverage_model":
                "same_day19_10_point_fifo_functional_coverage",

            "strategies":
                methods,

            "interpretation_rule":
                "Report measured values without "
                "assuming a strategy is superior.",

            "rtl_modified":
                False,

            "hermes_used_for_day20_baselines":
                False,
        }


    except Exception as error:

        print(
            "DAY 20 STRATEGY COMPARISON: FAIL"
        )

        print(
            "ERROR:",
            error
        )

        sys.exit(1)


    output = (
        DAY20
        / "strategy_comparison.json"
    )


    output.write_text(

        json.dumps(
            report,
            indent=4
        )
    )


    print(
        "DAY 20 STRATEGY COMPARISON: PASS"
    )


    for method in methods:

        print()

        print(
            "Strategy:",
            method[
                "strategy"
            ]
        )

        print(
            "Coverage:",
            method[
                "coverage_percent"
            ],
            "%"
        )

        print(
            "Stimulus cycles:",
            method[
                "stimulus_cycles"
            ]
        )

        print(
            "Redundancy:",
            method[
                "redundancy_percent"
            ],
            "%"
        )


if __name__ == "__main__":
    main()
