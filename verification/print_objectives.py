import json
import sys
from pathlib import Path


def main():

    if len(sys.argv) != 2:

        print(
            "Usage: python "
            "verification/"
            "print_objectives.py "
            "<objectives_json>"
        )

        sys.exit(1)


    path = Path(
        sys.argv[1]
    )


    if not path.exists():

        print(
            "ERROR: Objectives file "
            "not found."
        )

        sys.exit(1)


    data = json.loads(
        path.read_text()
    )


    print(
        "ID | CATEGORY | OPERATION | "
        "CASE | PRIORITY | DESCRIPTION"
    )

    print(
        "-" * 110
    )


    for objective in data.get(
        "objectives",
        []
    ):

        print(
            f"{objective.get('objective_id')} | "
            f"{objective.get('category')} | "
            f"{objective.get('operation')} | "
            f"{objective.get('case_value')} | "
            f"{objective.get('priority')} | "
            f"{objective.get('description')}"
        )


if __name__ == "__main__":

    main()
