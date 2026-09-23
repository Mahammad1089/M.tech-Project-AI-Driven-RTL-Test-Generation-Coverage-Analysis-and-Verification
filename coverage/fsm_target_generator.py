import json
import sys
from collections import deque
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


def build_graph(
    knowledge
):

    graph = {}

    transition_map = {}


    for transition in knowledge.get(
        "transitions",
        []
    ):

        source = transition["from"]

        graph.setdefault(
            source,
            []
        ).append(
            transition
        )

        transition_map[
            transition[
                "transition_id"
            ]
        ] = transition


    return (
        graph,
        transition_map
    )


def path_to_state(
    graph,
    start_state,
    target_state
):

    if (
        start_state
        == target_state
    ):

        return []


    queue = deque([
        (
            start_state,
            []
        )
    ])


    visited = {
        start_state
    }


    while queue:

        state, inputs = (
            queue.popleft()
        )


        for transition in graph.get(
            state,
            []
        ):

            next_state = (
                transition["to"]
            )

            next_inputs = (
                inputs
                + [
                    transition[
                        "input"
                    ]
                ]
            )


            if (
                next_state
                == target_state
            ):

                return next_inputs


            if (
                next_state
                not in visited
            ):

                visited.add(
                    next_state
                )

                queue.append(
                    (
                        next_state,
                        next_inputs
                    )
                )


    raise ValueError(
        f"No path from {start_state} "
        f"to {target_state}"
    )


def main():

    if len(sys.argv) != 4:

        print(
            "Usage: python "
            "coverage/"
            "fsm_target_generator.py "
            "<knowledge_json> "
            "<gaps_json> "
            "<output_json>"
        )

        sys.exit(1)


    try:

        knowledge = load_json(
            sys.argv[1]
        )

        gaps = load_json(
            sys.argv[2]
        )


        graph, transition_map = (
            build_graph(
                knowledge
            )
        )


        reset_state = (
            knowledge.get(
                "reset",
                {}
            ).get(
                "reset_state"
            )
        )


        if not reset_state:

            raise ValueError(
                "Reset state missing."
            )


        targets = []


        for gap in gaps.get(
            "transition_gaps",
            []
        ):

            transition_id = (
                gap[
                    "transition_id"
                ]
            )


            if (
                transition_id
                not in transition_map
            ):

                raise ValueError(
                    "Unknown target transition."
                )


            transition = (
                transition_map[
                    transition_id
                ]
            )


            prefix = path_to_state(
                graph,
                reset_state,
                transition["from"]
            )


            input_sequence = (
                prefix
                + [
                    transition[
                        "input"
                    ]
                ]
            )


            targets.append({

                "target_id":
                    (
                        "TARGET_"
                        + transition_id
                    ),

                "target_transition":
                    transition_id,

                "target_from":
                    transition["from"],

                "target_to":
                    transition["to"],

                "target_input":
                    transition["input"],

                "input_sequence":
                    input_sequence,

                "sequence_length":
                    len(
                        input_sequence
                    ),

                "generation_method":
                    (
                        "deterministic_"
                        "shortest_path"
                    )
            })


        result = {

            "dut":
                knowledge.get(
                    "dut"
                ),

            "source_gap_status":
                gaps.get(
                    "gap_status"
                ),

            "target_count":
                len(targets),

            "targets":
                targets,

            "hermes_used":
                False,

            "generation_method":
                (
                    "deterministic_"
                    "fsm_graph_search"
                )
        }


    except (
        FileNotFoundError,
        json.JSONDecodeError,
        ValueError,
        KeyError
    ) as error:

        print(
            "FSM TARGET GENERATION: FAIL"
        )

        print(
            f"ERROR: {error}"
        )

        sys.exit(1)


    output = Path(
        sys.argv[3]
    )

    output.write_text(
        json.dumps(
            result,
            indent=4
        )
    )


    print(
        "FSM TARGET GENERATION: PASS"
    )

    print(
        "Targets generated:",
        len(targets)
    )


if __name__ == "__main__":

    main()
