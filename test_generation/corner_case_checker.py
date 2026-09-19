import json
import sys
from pathlib import Path


def load_json(path):

    file_path = Path(
        path
    )

    if not file_path.exists():

        raise FileNotFoundError(
            f"File not found: {path}"
        )

    return json.loads(
        file_path.read_text()
    )


def get_objectives(data):

    if isinstance(
        data,
        list
    ):
        return data

    if isinstance(
        data,
        dict
    ):

        for key in (
            "objectives",
            "verification_objectives"
        ):

            value = data.get(
                key
            )

            if isinstance(
                value,
                list
            ):
                return value

    return []


def check_corner_case(
    operation,
    corner_case,
    a,
    b
):

    if corner_case == "zero_operands":

        return (
            a == 0
            and b == 0
        )

    if corner_case == "maximum_operands":

        return (
            a == 15
            and b == 15
        )

    if corner_case == "overflow_wraparound":

        return (
            a + b > 15
        )

    if corner_case == "equal_operands":

        return (
            a == b
        )

    if corner_case == "zero_subtrahend":

        return (
            b == 0
        )

    if corner_case == "underflow_wraparound":

        return (
            a < b
        )

    if corner_case == "all_zero":

        return (
            a == 0
            and b == 0
        )

    if corner_case == "all_one":

        if operation == "NOT":
            return a == 15

        return (
            a == 15
            and b == 15
        )

    if corner_case in {
        "alternating_patterns",
        "alternating_pattern"
    }:

        patterns = {
            0b0101,
            0b1010
        }

        if operation == "NOT":

            return (
                a in patterns
            )

        return (
            a in patterns
            and b in patterns
        )

    if corner_case == "complementary_patterns":

        return (
            (a == 0b0101 and b == 0b1010)
            or
            (a == 0b1010 and b == 0b0101)
        )

    if corner_case == "zero_input":

        return (
            a == 0
        )

    if corner_case == "msb_discard":

        return (
            (a & 0b1000) != 0
        )

    if corner_case == "lsb_discard":

        return (
            (a & 0b0001) != 0
        )

    return None


def main():

    if len(sys.argv) != 3:

        print(
            "Usage: python "
            "test_generation/"
            "corner_case_checker.py "
            "<objectives_json> "
            "<validated_tests_json>"
        )

        sys.exit(1)

    try:

        objective_data = load_json(
            sys.argv[1]
        )

        test_data = load_json(
            sys.argv[2]
        )

    except (
        FileNotFoundError,
        json.JSONDecodeError
    ) as error:

        print(
            "CORNER CASE CHECK: FAIL"
        )

        print(
            error
        )

        sys.exit(1)

    objective_map = {
        item.get(
            "objective_id"
        ): item
        for item in get_objectives(
            objective_data
        )
        if item.get(
            "objective_id"
        )
    }

    checked = 0

    passed = 0

    failed = []

    skipped = []

    for scenario in test_data.get(
        "scenarios",
        []
    ):

        objective = objective_map.get(
            scenario.get(
                "objective_id"
            )
        )

        if not objective:
            continue

        if objective.get(
            "category"
        ) != "corner_case":
            continue

        corner_case = objective.get(
            "corner_case"
        )

        if not corner_case:
            continue

        inputs = scenario.get(
            "inputs",
            {}
        )

        a = inputs.get(
            "a"
        )

        b = inputs.get(
            "b"
        )

        result = check_corner_case(
            scenario.get(
                "operation"
            ),
            corner_case,
            a,
            b
        )

        if result is None:

            skipped.append({
                "scenario_id":
                    scenario.get(
                        "scenario_id"
                    ),

                "objective_id":
                    scenario.get(
                        "objective_id"
                    ),

                "corner_case":
                    corner_case
            })

            continue

        checked += 1

        if result:

            passed += 1

        else:

            failed.append({
                "scenario_id":
                    scenario.get(
                        "scenario_id"
                    ),

                "objective_id":
                    scenario.get(
                        "objective_id"
                    ),

                "operation":
                    scenario.get(
                        "operation"
                    ),

                "corner_case":
                    corner_case,

                "inputs":
                    inputs
            })

    print(
        "Corner cases checked :",
        checked
    )

    print(
        "Corner cases passed  :",
        passed
    )

    print(
        "Corner cases failed  :",
        len(
            failed
        )
    )

    print(
        "Rules skipped        :",
        len(
            skipped
        )
    )

    if failed:

        print()

        print(
            "Failed corner-case scenarios:"
        )

        for item in failed:

            print(
                " -",
                item
            )

    if skipped:

        print()

        print(
            "Unimplemented corner rules:"
        )

        for item in skipped:

            print(
                " -",
                item
            )

    print()

    if not failed:

        print(
            "CORNER CASE CHECK: PASS"
        )

    else:

        print(
            "CORNER CASE CHECK: "
            "ISSUES FOUND"
        )


if __name__ == "__main__":
    main()
