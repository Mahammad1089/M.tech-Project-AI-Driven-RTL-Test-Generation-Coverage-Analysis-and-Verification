import json
import sys
from collections import Counter
from pathlib import Path


def main():

    if len(sys.argv) != 2:

        print(
            "Usage: python "
            "verification/"
            "objective_statistics.py "
            "<objectives_json>"
        )

        sys.exit(1)


    path = Path(
        sys.argv[1]
    )


    if not path.exists():

        print(
            "ERROR: File not found."
        )

        sys.exit(1)


    data = json.loads(
        path.read_text()
    )


    objectives = data.get(
        "objectives",
        []
    )


    category_counts = Counter(

        objective.get(
            "category"
        )

        for objective in objectives
    )


    operation_counts = Counter(

        objective.get(
            "operation"
        )

        for objective in objectives
    )


    priority_counts = Counter(

        objective.get(
            "priority"
        )

        for objective in objectives
    )


    print(
        "OBJECTIVE STATISTICS"
    )

    print(
        "===================="
    )

    print()


    print(
        "Total:",
        len(
            objectives
        )
    )


    print()

    print(
        "By category:"
    )


    for key, value in (
        sorted(
            category_counts.items()
        )
    ):

        print(
            f"  {key}: {value}"
        )


    print()

    print(
        "By operation:"
    )


    for key, value in (
        sorted(
            operation_counts.items()
        )
    ):

        print(
            f"  {key}: {value}"
        )


    print()

    print(
        "By priority:"
    )


    for key, value in (
        sorted(
            priority_counts.items()
        )
    ):

        print(
            f"  {key}: {value}"
        )


if __name__ == "__main__":

    main()
