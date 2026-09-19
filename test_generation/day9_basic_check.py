import json
import sys
from pathlib import Path


def fail(
    message
):

    print(
        "DAY 9 BASIC CHECK: FAIL"
    )

    print(
        message
    )

    sys.exit(1)


def main():

    if len(sys.argv) != 2:

        print(
            "Usage: python "
            "test_generation/"
            "day9_basic_check.py "
            "<candidate_tests_json>"
        )

        sys.exit(1)

    path = Path(
        sys.argv[1]
    )

    if not path.exists():

        fail(
            "Candidate tests file "
            "not found."
        )

    try:

        data = json.loads(
            path.read_text()
        )

    except json.JSONDecodeError:

        fail(
            "Candidate tests file "
            "is not valid JSON."
        )

    if not isinstance(
        data,
        dict
    ):

        fail(
            "Top-level JSON must "
            "be an object."
        )

    required_keys = {
        "dut",
        "scenario_count",
        "scenarios",
        "generation_status"
    }

    missing_keys = (
        required_keys
        - set(
            data.keys()
        )
    )

    if missing_keys:

        fail(
            "Missing top-level keys: "
            + ", ".join(
                sorted(
                    missing_keys
                )
            )
        )

    scenarios = data.get(
        "scenarios"
    )

    if not isinstance(
        scenarios,
        list
    ):

        fail(
            "'scenarios' must "
            "be a list."
        )

    if len(
        scenarios
    ) == 0:

        fail(
            "No scenarios generated."
        )

    declared_count = data.get(
        "scenario_count"
    )

    actual_count = len(
        scenarios
    )

    if declared_count != actual_count:

        fail(
            "scenario_count does not "
            "match number of scenarios."
        )

    marker = (
        "HERMES TEST SCENARIO "
        "GENERATION COMPLETE"
    )

    if data.get(
        "generation_status"
    ) != marker:

        fail(
            "Generation completion "
            "marker is incorrect."
        )

    print(
        "Valid JSON              : PASS"
    )

    print(
        "Top-level structure     : PASS"
    )

    print(
        "Scenario list present   : PASS"
    )

    print(
        "Scenario count matches  : PASS"
    )

    print(
        "Completion marker       : PASS"
    )

    print()

    print(
        "Generated scenarios:",
        actual_count
    )

    print()

    print(
        "DAY 9 BASIC CHECK: PASS"
    )


if __name__ == "__main__":
    main()
