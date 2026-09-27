import json
import sys

from pathlib import Path


OUTPUT = Path(
    "results/integration/day23/"
    "historical_results_validation.json"
)


RESULT_FILES = {

    "day15_alu":
        Path(
            "results/alu/day15/"
            "day15_summary.json"
        ),

    "day17_fsm":
        Path(
            "results/fsm/day17/"
            "day17_summary.json"
        ),

    "day19_fifo":
        Path(
            "results/fifo/day19/"
            "day19_summary.json"
        ),

    "day20_comparison":
        Path(
            "results/fifo/day20/"
            "day20_summary.json"
        ),

    "day21_experiments":
        Path(
            "results/fifo/day21/"
            "day21_summary.json"
        ),

    "day22_visualization":
        Path(
            "results/fifo/day22/"
            "day22_summary.json"
        ),
}


def main():

    milestone_results = []

    overall_pass = True

    try:

        for (
            milestone,
            path
        ) in RESULT_FILES.items():

            entry = {
                "milestone":
                    milestone,

                "file":
                    str(path),

                "exists":
                    path.exists(),

                "reported_status":
                    None,

                "validation":
                    "FAIL"
            }

            if path.exists():

                try:

                    data = json.loads(
                        path.read_text()
                    )

                    status = data.get(
                        "status"
                    )

                    entry[
                        "reported_status"
                    ] = status

                    if status == "PASS":

                        entry[
                            "validation"
                        ] = "PASS"

                    else:

                        overall_pass = False

                except Exception as error:

                    entry[
                        "error"
                    ] = str(error)

                    overall_pass = False

            else:

                overall_pass = False

            milestone_results.append(
                entry
            )

        report = {

            "day": 23,

            "check":
                "historical_results",

            "milestones":
                milestone_results,

            "status":
                "PASS"
                if overall_pass
                else "FAIL"
        }

        OUTPUT.write_text(
            json.dumps(
                report,
                indent=4
            )
        )

    except Exception as error:

        print(
            "DAY 23 HISTORICAL RESULT VALIDATION: FAIL"
        )

        print(
            "ERROR:",
            error
        )

        sys.exit(1)

    if not overall_pass:

        print(
            "DAY 23 HISTORICAL RESULT VALIDATION: FAIL"
        )

        for entry in milestone_results:

            print(
                entry["milestone"],
                ":",
                entry["validation"]
            )

        sys.exit(1)

    print(
        "DAY 23 HISTORICAL RESULT VALIDATION: PASS"
    )

    print(
        "Validated milestones:",
        len(milestone_results)
    )


if __name__ == "__main__":

    main()
