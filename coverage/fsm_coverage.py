import csv
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


def load_trace(path):

    file_path = Path(path)

    if not file_path.exists():

        raise FileNotFoundError(
            f"Trace not found: {path}"
        )

    rows = []

    with file_path.open(
        newline=""
    ) as file:

        reader = csv.DictReader(
            file
        )

        required = {
            "from_state",
            "input",
            "to_state",
            "detected"
        }

        if set(
            reader.fieldnames or []
        ) != required:

            raise ValueError(
                "Unexpected trace columns."
            )

        for row in reader:

            rows.append(
                row
            )

    if not rows:

        raise ValueError(
            "Execution trace is empty."
        )

    return rows


def state_encoding_map(
    knowledge
):

    mapping = {}

    for state in knowledge.get(
        "states",
        []
    ):

        name = state.get(
            "name"
        )

        encoding = state.get(
            "encoding"
        )

        if not name or not encoding:

            raise ValueError(
                "Invalid state entry."
            )

        bits = encoding.split(
            "'b"
        )[-1]

        mapping[bits] = name

    return mapping


def legal_transition_map(
    knowledge
):

    transitions = {}

    for item in knowledge.get(
        "transitions",
        []
    ):

        transition_id = item.get(
            "transition_id"
        )

        signature = (
            item.get("from"),
            int(item.get("input")),
            item.get("to"),
            int(item.get("detected"))
        )

        if not transition_id:

            raise ValueError(
                "Transition ID missing."
            )

        transitions[
            signature
        ] = transition_id

    if not transitions:

        raise ValueError(
            "No legal transitions found."
        )

    return transitions


def main():

    if len(sys.argv) != 4:

        print(
            "Usage: python "
            "coverage/fsm_coverage.py "
            "<fsm_knowledge_json> "
            "<execution_trace_csv> "
            "<output_json>"
        )

        sys.exit(1)


    try:

        knowledge = load_json(
            sys.argv[1]
        )

        trace = load_trace(
            sys.argv[2]
        )

        encoding_map = (
            state_encoding_map(
                knowledge
            )
        )

        legal_transitions = (
            legal_transition_map(
                knowledge
            )
        )


        legal_states = {
            item["name"]
            for item
            in knowledge.get(
                "states",
                []
            )
        }


        visited_states = set()

        covered_transitions = set()

        transition_hits = {
            transition_id: 0
            for transition_id
            in legal_transitions.values()
        }


        for row in trace:

            from_bits = (
                row[
                    "from_state"
                ].strip()
            )

            to_bits = (
                row[
                    "to_state"
                ].strip()
            )

            if (
                from_bits
                not in encoding_map
            ):

                raise ValueError(
                    "Unknown from-state "
                    f"encoding: {from_bits}"
                )

            if (
                to_bits
                not in encoding_map
            ):

                raise ValueError(
                    "Unknown to-state "
                    f"encoding: {to_bits}"
                )


            from_state = (
                encoding_map[
                    from_bits
                ]
            )

            to_state = (
                encoding_map[
                    to_bits
                ]
            )

            input_bit = int(
                row["input"]
            )

            detected = int(
                row["detected"]
            )


            signature = (
                from_state,
                input_bit,
                to_state,
                detected
            )


            if (
                signature
                not in legal_transitions
            ):

                raise ValueError(
                    "Illegal transition "
                    f"observed: {signature}"
                )


            transition_id = (
                legal_transitions[
                    signature
                ]
            )


            visited_states.add(
                from_state
            )

            visited_states.add(
                to_state
            )

            covered_transitions.add(
                transition_id
            )

            transition_hits[
                transition_id
            ] += 1


        missing_states = sorted(
            legal_states
            - visited_states
        )


        all_transition_ids = set(
            legal_transitions.values()
        )

        missing_transitions = sorted(
            all_transition_ids
            - covered_transitions
        )


        state_total = len(
            legal_states
        )

        state_covered = len(
            visited_states
        )


        transition_total = len(
            all_transition_ids
        )

        transition_covered = len(
            covered_transitions
        )


        state_percent = round(
            (
                state_covered
                / state_total
                * 100
            ),
            2
        )


        transition_percent = round(
            (
                transition_covered
                / transition_total
                * 100
            ),
            2
        )


        report = {

            "dut":
                knowledge.get(
                    "dut"
                ),

            "coverage_type":
                "fsm_state_transition_coverage",

            "measurement_source":
                "executed_fsm_trace",

            "trace_rows":
                len(trace),

            "state_coverage": {

                "total_states":
                    state_total,

                "covered_states":
                    state_covered,

                "coverage_percent":
                    state_percent,

                "visited_states":
                    sorted(
                        visited_states
                    ),

                "missing_states":
                    missing_states
            },


            "transition_coverage": {

                "total_transitions":
                    transition_total,

                "covered_transitions":
                    transition_covered,

                "coverage_percent":
                    transition_percent,

                "covered_transition_ids":
                    sorted(
                        covered_transitions
                    ),

                "missing_transition_ids":
                    missing_transitions,

                "transition_hits":
                    transition_hits
            },


            "coverage_complete":
                (
                    not missing_states
                    and
                    not missing_transitions
                )
        }


    except (
        FileNotFoundError,
        json.JSONDecodeError,
        ValueError,
        KeyError
    ) as error:

        print(
            "FSM COVERAGE ANALYSIS: FAIL"
        )

        print(
            f"ERROR: {error}"
        )

        sys.exit(1)


    output = Path(
        sys.argv[3]
    )

    output.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    output.write_text(
        json.dumps(
            report,
            indent=4
        )
    )


    print(
        "FSM COVERAGE ANALYSIS: PASS"
    )

    print(
        "State coverage      :",
        state_percent
    )

    print(
        "Transition coverage :",
        transition_percent
    )

    print(
        "Missing states      :",
        len(missing_states)
    )

    print(
        "Missing transitions :",
        len(missing_transitions)
    )


if __name__ == "__main__":

    main()
