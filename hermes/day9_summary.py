import json
from pathlib import Path


CANDIDATE_FILE = Path(
    "results/alu/day9/"
    "candidate_tests.json"
)


SUMMARY_FILE = Path(
    "results/alu/day9/"
    "day9_summary.json"
)


def main():

    if not CANDIDATE_FILE.exists():

        print(
            "DAY 9 SUMMARY: FAIL"
        )

        print(
            "candidate_tests.json "
            "not found."
        )

        raise SystemExit(1)

    try:

        data = json.loads(
            CANDIDATE_FILE.read_text()
        )

    except json.JSONDecodeError:

        print(
            "DAY 9 SUMMARY: FAIL"
        )

        print(
            "Candidate file contains "
            "invalid JSON."
        )

        raise SystemExit(1)

    scenarios = data.get(
        "scenarios",
        []
    )

    operations = sorted({
        scenario.get(
            "operation"
        )
        for scenario in scenarios
        if scenario.get(
            "operation"
        )
    })

    objective_ids = {
        scenario.get(
            "objective_id"
        )
        for scenario in scenarios
        if scenario.get(
            "objective_id"
        )
    }

    marker = (
        "HERMES TEST SCENARIO "
        "GENERATION COMPLETE"
    )

    summary = {

        "day":
            9,

        "dut":
            data.get(
                "dut"
            ),

        "stage":
            (
                "Hermes initial "
                "test scenario generation"
            ),

        "scenario_count":
            len(
                scenarios
            ),

        "declared_scenario_count":
            data.get(
                "scenario_count"
            ),

        "unique_objective_references":
            len(
                objective_ids
            ),

        "operations_proposed":
            operations,

        "generation_marker":
            (
                data.get(
                    "generation_status"
                )
                == marker
            ),

        "semantic_validation":
            "PENDING_DAY_10",

        "verilog_generated":
            False,

        "coverage_measured":
            False,

        "status":
            (
                "PASS"
                if (
                    len(
                        scenarios
                    ) > 0
                    and data.get(
                        "scenario_count"
                    ) == len(
                        scenarios
                    )
                    and data.get(
                        "generation_status"
                    ) == marker
                )
                else "FAIL"
            )
    }

    SUMMARY_FILE.write_text(
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

    if summary[
        "status"
    ] != "PASS":

        raise SystemExit(1)


if __name__ == "__main__":
    main()
