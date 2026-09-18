import json
import sys
from pathlib import Path


EXPECTED_OPERATIONS = {

    "3'b000":
        "ADD",

    "3'b001":
        "SUB",

    "3'b010":
        "AND",

    "3'b011":
        "OR",

    "3'b100":
        "XOR",

    "3'b101":
        "NOT",

    "3'b110":
        "SHIFT_LEFT",

    "3'b111":
        "SHIFT_RIGHT"
}


def fail(message):

    print(
        "VALIDATION: FAIL"
    )

    print(
        message
    )

    sys.exit(1)


def main():

    if len(sys.argv) != 2:

        print(
            "Usage: python "
            "parser/validate_day6.py "
            "<knowledge_json>"
        )

        sys.exit(1)


    json_path = Path(
        sys.argv[1]
    )


    if not json_path.exists():

        fail(
            "Knowledge JSON not found."
        )


    data = json.loads(
        json_path.read_text()
    )


    modules = data.get(
        "modules",
        []
    )


    if len(modules) != 1:

        fail(
            "Expected exactly one module."
        )


    module = modules[0]


    if module.get(
        "module_name"
    ) != "alu":

        fail(
            "Module name is not alu."
        )


    case_logic = module.get(
        "case_logic",
        []
    )


    if len(case_logic) != 1:

        fail(
            "Expected exactly one "
            "case statement."
        )


    case_info = case_logic[0]


    if case_info.get(
        "selector"
    ) != "sel":

        fail(
            "Case selector is not sel."
        )


    branches = case_info.get(
        "branches",
        []
    )


    branch_map = {

        branch.get(
            "case_value"
        ):
            branch

        for branch in branches
    }


    for (
        case_value,
        expected_operator
    ) in EXPECTED_OPERATIONS.items():

        if case_value not in branch_map:

            fail(
                f"Missing case: "
                f"{case_value}"
            )


        actual_operator = (
            branch_map[
                case_value
            ].get(
                "operator"
            )
        )


        if (
            actual_operator
            != expected_operator
        ):

            fail(
                f"{case_value}: "
                f"expected "
                f"{expected_operator}, "
                f"got "
                f"{actual_operator}"
            )


    print(
        "Module detection       : PASS"
    )

    print(
        "Case selector          : PASS"
    )

    print(
        "Eight ALU cases        : PASS"
    )

    print(
        "ADD extraction         : PASS"
    )

    print(
        "SUB extraction         : PASS"
    )

    print(
        "AND extraction         : PASS"
    )

    print(
        "OR extraction          : PASS"
    )

    print(
        "XOR extraction         : PASS"
    )

    print(
        "NOT extraction         : PASS"
    )

    print(
        "SHIFT LEFT extraction  : PASS"
    )

    print(
        "SHIFT RIGHT extraction : PASS"
    )

    print()

    print(
        "DAY 6 RTL KNOWLEDGE "
        "VALIDATION: PASS"
    )


if __name__ == "__main__":

    main()
