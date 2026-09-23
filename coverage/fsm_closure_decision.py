import json
import sys
from pathlib import Path


def load_json(path):

    file_path = Path(path)

    if not file_path.exists():

        raise FileNotFoundError(
            f"File not found: {path}"
        )

    return json.loads(
        file_path.read_text()
    )


def main():

    if len(sys.argv) != 3:

        print(
            "Usage: python "
            "coverage/"
            "fsm_closure_decision.py "
            "<coverage_json> "
            "<output_json>"
        )

        sys.exit(1)


    try:

        coverage = load_json(
            sys.argv[1]
        )


        state = coverage.get(
            "state_coverage",
            {}
        )

        transition = coverage.get(
            "transition_coverage",
            {}
        )


        missing_states = (
            state.get(
                "missing_states",
                []
            )
        )


        missing_transitions = (
            transition.get(
                "missing_transition_ids",
                []
            )
        )


        if (
            not isinstance(
                missing_states,
                list
            )
            or
            not isinstance(
                missing_transitions,
                list
            )
        ):

            raise ValueError(
                "Invalid coverage gap lists."
            )


        complete = (
            len(missing_states) == 0
            and
            len(
                missing_transitions
            ) == 0
        )


        if complete:

            action = "STOP"

            reason = (
                "All legal FSM states "
                "and transitions are covered."
            )

        else:

            action = "CONTINUE"

            reason = (
                "Uncovered legal FSM states "
                "or transitions remain."
            )


        decision = {

            "state_coverage":
                state.get(
                    "coverage_percent"
                ),

            "transition_coverage":
                transition.get(
                    "coverage_percent"
                ),

            "missing_states":
                missing_states,

            "missing_transitions":
                missing_transitions,

            "coverage_complete":
                complete,

            "action":
                action,

            "reason":
                reason
        }


    except (
        FileNotFoundError,
        json.JSONDecodeError,
        ValueError
    ) as error:

        print(
            "FSM CLOSURE DECISION: FAIL"
        )

        print(
            f"ERROR: {error}"
        )

        sys.exit(1)


    output = Path(
        sys.argv[2]
    )

    output.write_text(
        json.dumps(
            decision,
            indent=4
        )
    )


    print(
        "FSM CLOSURE DECISION: PASS"
    )

    print(
        "Decision:",
        action
    )

    print(
        "Reason:",
        reason
    )


if __name__ == "__main__":

    main()
