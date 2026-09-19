import json
import sys
from pathlib import Path


def main():

    if len(sys.argv) != 2:

        print(
            "Usage: python "
            "test_generation/"
            "duplicate_checker.py "
            "<candidate_tests_json>"
        )

        sys.exit(1)

    path = Path(
        sys.argv[1]
    )

    if not path.exists():

        print(
            "DUPLICATE CHECK: FAIL"
        )

        print(
            "Input file not found."
        )

        sys.exit(1)

    try:

        data = json.loads(
            path.read_text()
        )

    except json.JSONDecodeError:

        print(
            "DUPLICATE CHECK: FAIL"
        )

        print(
            "Invalid JSON."
        )

        sys.exit(1)

    scenarios = data.get(
        "scenarios",
        []
    )

    seen_ids = set()

    seen_signatures = {}

    duplicate_ids = []

    duplicate_stimuli = []

    for scenario in scenarios:

        scenario_id = scenario.get(
            "scenario_id"
        )

        if scenario_id in seen_ids:

            duplicate_ids.append(
                scenario_id
            )

        else:

            seen_ids.add(
                scenario_id
            )

        inputs = scenario.get(
            "inputs",
            {}
        )

        signature = (
            scenario.get(
                "operation"
            ),
            scenario.get(
                "selector"
            ),
            inputs.get(
                "a"
            ),
            inputs.get(
                "b"
            )
        )

        if signature in seen_signatures:

            duplicate_stimuli.append({
                "first_scenario":
                    seen_signatures[
                        signature
                    ],

                "duplicate_scenario":
                    scenario_id,

                "signature":
                    signature
            })

        else:

            seen_signatures[
                signature
            ] = scenario_id

    print(
        "Scenario count      :",
        len(
            scenarios
        )
    )

    print(
        "Duplicate IDs       :",
        len(
            duplicate_ids
        )
    )

    print(
        "Duplicate stimuli   :",
        len(
            duplicate_stimuli
        )
    )

    if duplicate_ids:

        print()

        print(
            "Duplicate scenario IDs:"
        )

        for item in duplicate_ids:

            print(
                " -",
                item
            )

    if duplicate_stimuli:

        print()

        print(
            "Duplicate stimulus "
            "signatures:"
        )

        for item in (
            duplicate_stimuli
        ):

            print(
                " -",
                item
            )

    print()

    if (
        duplicate_ids
        or duplicate_stimuli
    ):

        print(
            "DUPLICATE CHECK: "
            "DUPLICATES FOUND"
        )

    else:

        print(
            "DUPLICATE CHECK: PASS"
        )


if __name__ == "__main__":
    main()
