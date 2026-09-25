import json
import sys

from pathlib import Path


BASE = Path(
    "results/fifo/day19"
)


def load_json(
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


def main():

    try:

        baseline = load_json(
            "fifo_baseline_coverage.json"
        )

        final = load_json(
            "fifo_closed_coverage.json"
        )

        comparison = load_json(
            "fifo_coverage_comparison.json"
        )

        gaps = load_json(
            "fifo_remaining_gaps.json"
        )

        decision = load_json(
            "fifo_closure_decision.json"
        )

        targets = load_json(
            "fifo_targeted_sequences.json"
        )


        if (
            comparison[
                "trend"
            ]
            == "REGRESSION"
        ):

            raise ValueError(
                "Coverage regression detected."
            )


        summary = {

            "day":
                19,

            "dut":
                "fifo",

            "stage":
                "FIFO functional coverage "
                "and deterministic closure",

            "coverage_model":
                "10 defined FIFO functional "
                "coverage points",

            "baseline_coverage_percent":
                baseline[
                    "coverage_percent"
                ],

            "baseline_covered_points":
                baseline[
                    "covered_coverage_points"
                ],

            "baseline_missing_points":
                len(
                    baseline[
                        "missing_points"
                    ]
                ),

            "target_count":
                targets[
                    "target_count"
                ],

            "final_coverage_percent":
                final[
                    "coverage_percent"
                ],

            "final_covered_points":
                final[
                    "covered_coverage_points"
                ],

            "coverage_delta":
                comparison[
                    "coverage_delta"
                ],

            "coverage_trend":
                comparison[
                    "trend"
                ],

            "remaining_gap_count":
                gaps[
                    "gap_count"
                ],

            "gap_status":
                gaps[
                    "gap_status"
                ],

            "closure_action":
                decision[
                    "action"
                ],

            "closure_reason":
                decision[
                    "reason"
                ],

            "hermes_used":
                False,

            "coverage_measured":
                True,

            "target_generation":
                "deterministic_target_library",

            "rtl_modified":
                False,

            "status":
                "PASS",
        }


    except Exception as error:

        print(
            "DAY 19 SUMMARY: FAIL"
        )

        print(
            "ERROR:",
            error
        )

        sys.exit(1)


    output = (
        BASE
        / "day19_summary.json"
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
        "DAY 19 SUMMARY: PASS"
    )


if __name__ == "__main__":
    main()
