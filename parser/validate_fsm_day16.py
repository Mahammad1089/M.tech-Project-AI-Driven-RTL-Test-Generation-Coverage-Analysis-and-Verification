import json
import sys
from pathlib import Path


EXPECTED_STATES = {
    "IDLE",
    "S1",
    "S10",
    "S101"
}


EXPECTED_TRANSITIONS = {

    (
        "IDLE",
        0,
        "IDLE",
        0
    ),

    (
        "IDLE",
        1,
        "S1",
        0
    ),

    (
        "S1",
        0,
        "S10",
        0
    ),

    (
        "S1",
        1,
        "S1",
        0
    ),

    (
        "S10",
        0,
        "IDLE",
        0
    ),

    (
        "S10",
        1,
        "S101",
        0
    ),

    (
        "S101",
        0,
        "S10",
        0
    ),

    (
        "S101",
        1,
        "S1",
        1
    )
}


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


def main():

    if len(sys.argv) != 2:

        print(
            "Usage: python "
            "parser/validate_fsm_day16.py "
            "<fsm_knowledge_json>"
        )

        sys.exit(1)

    try:

        data = load_json(
            sys.argv[1]
        )

        if data.get(
            "dut"
        ) != "fsm_1011":

            raise ValueError(
                "Unexpected DUT."
            )

        states = data.get(
            "states"
        )

        transitions = data.get(
            "transitions"
        )

        if not isinstance(
            states,
            list
        ):

            raise ValueError(
                "states must be a list."
            )

        if not isinstance(
            transitions,
            list
        ):

            raise ValueError(
                "transitions must be a list."
            )

        actual_states = {
            item.get(
                "name"
            )
            for item in states
        }

        if (
            actual_states
            != EXPECTED_STATES
        ):

            raise ValueError(
                "FSM state set mismatch."
            )

        actual_transitions = set()

        transition_ids = set()

        for transition in transitions:

            transition_id = (
                transition.get(
                    "transition_id"
                )
            )

            if not transition_id:

                raise ValueError(
                    "Transition ID missing."
                )

            if (
                transition_id
                in transition_ids
            ):

                raise ValueError(
                    "Duplicate transition ID."
                )

            transition_ids.add(
                transition_id
            )

            signature = (
                transition.get(
                    "from"
                ),

                transition.get(
                    "input"
                ),

                transition.get(
                    "to"
                ),

                transition.get(
                    "detected"
                )
            )

            actual_transitions.add(
                signature
            )

        if (
            actual_transitions
            != EXPECTED_TRANSITIONS
        ):

            raise ValueError(
                "FSM transition set mismatch."
            )

        if data.get(
            "coverage_measured"
        ) is not False:

            raise ValueError(
                "Day 16 must not claim "
                "coverage measurement."
            )

        if data.get(
            "detection_transition"
        ) != "TR_008":

            raise ValueError(
                "Detection transition mismatch."
            )

    except (
        FileNotFoundError,
        json.JSONDecodeError,
        ValueError
    ) as error:

        print(
            "DAY 16 FSM KNOWLEDGE "
            "VALIDATION: FAIL"
        )

        print(
            f"ERROR: {error}"
        )

        sys.exit(1)

    print(
        "FSM states validated      :",
        len(actual_states)
    )

    print(
        "FSM transitions validated :",
        len(actual_transitions)
    )

    print(
        "DAY 16 FSM KNOWLEDGE "
        "VALIDATION: PASS"
    )


if __name__ == "__main__":
    main()

