import json
import sys
from pathlib import Path


def main():

    if len(sys.argv) != 2:

        print(
            "Usage: python "
            "parser/print_knowledge.py "
            "<knowledge_json>"
        )

        sys.exit(1)


    path = Path(
        sys.argv[1]
    )


    if not path.exists():

        print(
            "ERROR: JSON file not found."
        )

        sys.exit(1)


    data = json.loads(
        path.read_text()
    )


    for module in data[
        "modules"
    ]:

        print(
            "Module:",
            module[
                "module_name"
            ]
        )

        print()


        for case_info in module[
            "case_logic"
        ]:

            print(
                "Case selector:",
                case_info[
                    "selector"
                ]
            )

            print()


            print(
                "VALUE | OPERATION | "
                "DEST | EXPRESSION"
            )

            print(
                "-" * 55
            )


            for branch in case_info[
                "branches"
            ]:

                print(
                    f"{branch.get('case_value')} "
                    f"| "
                    f"{branch.get('operator')} "
                    f"| "
                    f"{branch.get('destination')} "
                    f"| "
                    f"{branch.get('expression')}"
                )


if __name__ == "__main__":

    main()
