import json
import sys
from pathlib import Path


def main():

    if len(sys.argv) != 2:

        print(
            "Usage: python "
            "parser/print_fsm_knowledge.py "
            "<fsm_knowledge_json>"
        )

        sys.exit(1)

    path = Path(
        sys.argv[1]
    )

    if not path.exists():

        print(
            "FSM KNOWLEDGE PRINT: FAIL"
        )

        print(
            f"Missing file: {path}"
        )

        sys.exit(1)

    data = json.loads(
        path.read_text()
    )

    print()

    print(
        "=" * 72
    )

    print(
        "FSM 1011 KNOWLEDGE MODEL"
    )

    print(
        "=" * 72
    )

    print(
        "DUT             :",
        data.get("dut")
    )

    print(
        "Sequence        :",
        data.get("sequence")
    )

    print(
        "Overlap enabled :",
        data.get(
            "overlap_enabled"
        )
    )

    print()

    print(
        "STATES"
    )

    print(
        "-" * 72
    )

    for state in data.get(
        "states",
        []
    ):

        print(
            f"{state['name']:<8} "
            f"{state['encoding']:<8} "
            f"{state['meaning']}"
        )

    print()

    print(
        "TRANSITIONS"
    )

    print(
        "-" * 72
    )

    print(
        f"{'ID':<8}"
        f"{'FROM':<8}"
        f"{'IN':<6}"
        f"{'TO':<8}"
        f"{'DETECT'}"
    )

    for transition in data.get(
        "transitions",
        []
    ):

        print(
            f"{transition['transition_id']:<8}"
            f"{transition['from']:<8}"
            f"{transition['input']:<6}"
            f"{transition['to']:<8}"
            f"{transition['detected']}"
        )

    print(
        "=" * 72
    )


if __name__ == "__main__":
    main()
