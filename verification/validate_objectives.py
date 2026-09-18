import json
import sys
from pathlib import Path


EXPECTED_FUNCTIONS = {
    "ADD",
    "SUB",
    "AND",
    "OR",
    "XOR",
    "NOT",
    "SHIFT_LEFT",
    "SHIFT_RIGHT"
}


REQUIRED_FIELDS = {
    "objective_id",
    "category",
    "operation",
    "selector",
    "case_value",
    "description",
    "priority",
    "source"
}


def fail(
    message
):

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
            "verification/"
            "validate_objectives.py "
            "<objectives_json>"
        )

        sys.exit(1)


    path = Path(
        sys.argv[1]
    )


    if not path.exists():

        fail(
            "Objectives JSON "
            "not found."
        )


    data = json.loads(
        path.read_text()
    )


    objectives = data.get(
        "objectives",
        []
    )


    if not objectives:

        fail(
            "No objectives generated."
        )


    ids = []


    for objective in objectives:

        missing = (
            REQUIRED_FIELDS
            - set(
                objective.keys()
            )
        )


        if missing:

            fail(
                f"Missing fields in "
                f"{objective.get('objective_id')}: "
                f"{sorted(missing)}"
            )


        ids.append(
            objective[
                "objective_id"
            ]
        )


    if len(ids) != len(set(ids)):

        fail(
            "Duplicate objective IDs "
            "detected."
        )


    functional = [

        objective

        for objective in objectives

        if objective.get(
            "category"
        ) == "functional"
    ]


    corner = [

        objective

        for objective in objectives

        if objective.get(
            "category"
        ) == "corner_case"
    ]


    operations = {

        objective.get(
            "operation"
        )

        for objective in functional
    }


    if operations != EXPECTED_FUNCTIONS:

        fail(
            "Functional operation set "
            "does not match expected ALU "
            "operations."
        )


    functional_ids = {

        objective[
            "objective_id"
        ]

        for objective in functional
    }


    for objective in corner:

        parent = objective.get(
            "parent_objective"
        )


        if parent not in functional_ids:

            fail(
                f"Invalid parent for "
                f"{objective['objective_id']}"
            )


    if (
        data.get(
            "functional_objective_count"
        )
        != len(
            functional
        )
    ):

        fail(
            "Functional count mismatch."
        )


    if (
        data.get(
            "corner_case_objective_count"
        )
        != len(
            corner
        )
    ):

        fail(
            "Corner-case count mismatch."
        )


    if (
        data.get(
            "total_objective_count"
        )
        != len(
            objectives
        )
    ):

        fail(
            "Total count mismatch."
        )


    print(
        "Objective JSON         : PASS"
    )

    print(
        "Required fields        : PASS"
    )

    print(
        "Unique IDs             : PASS"
    )

    print(
        "Functional operations  : PASS"
    )

    print(
        "Parent relationships   : PASS"
    )

    print(
        "Objective counts       : PASS"
    )

    print()

    print(
        "DAY 7 OBJECTIVE "
        "VALIDATION: PASS"
    )


if __name__ == "__main__":

    main()
