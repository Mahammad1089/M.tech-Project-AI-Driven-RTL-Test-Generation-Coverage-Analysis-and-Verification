import json
import sys
from pathlib import Path


def fail(
    message
):

    print(
        "TRACEABILITY: FAIL"
    )

    print(
        message
    )

    sys.exit(1)


def main():

    if len(sys.argv) != 3:

        print(
            "Usage: python "
            "verification/"
            "validate_traceability.py "
            "<knowledge_json> "
            "<objectives_json>"
        )

        sys.exit(1)


    knowledge_path = Path(
        sys.argv[1]
    )


    objective_path = Path(
        sys.argv[2]
    )


    if not knowledge_path.exists():

        fail(
            "Knowledge JSON not found."
        )


    if not objective_path.exists():

        fail(
            "Objectives JSON not found."
        )


    knowledge = json.loads(
        knowledge_path.read_text()
    )


    objective_data = json.loads(
        objective_path.read_text()
    )


    knowledge_entries = set()


    for module in knowledge.get(
        "modules",
        []
    ):

        for case_info in module.get(
            "case_logic",
            []
        ):

            selector = case_info.get(
                "selector"
            )


            for branch in case_info.get(
                "branches",
                []
            ):

                operation = branch.get(
                    "operator"
                )


                if operation in {
                    "ADD",
                    "SUB",
                    "AND",
                    "OR",
                    "XOR",
                    "NOT",
                    "SHIFT_LEFT",
                    "SHIFT_RIGHT"
                }:

                    knowledge_entries.add(
                        (
                            selector,
                            branch.get(
                                "case_value"
                            ),
                            operation
                        )
                    )


    functional_entries = set()


    for objective in objective_data.get(
        "objectives",
        []
    ):

        if objective.get(
            "category"
        ) != "functional":

            continue


        functional_entries.add(
            (
                objective.get(
                    "selector"
                ),
                objective.get(
                    "case_value"
                ),
                objective.get(
                    "operation"
                )
            )
        )


    if (
        functional_entries
        != knowledge_entries
    ):

        print(
            "Knowledge entries:"
        )

        print(
            knowledge_entries
        )


        print(
            "Objective entries:"
        )

        print(
            functional_entries
        )


        fail(
            "Functional objectives do not "
            "match RTL knowledge."
        )


    print(
        "Knowledge → Objective "
        "traceability: PASS"
    )


    print(
        "DAY 7 TRACEABILITY: PASS"
    )


if __name__ == "__main__":

    main()
