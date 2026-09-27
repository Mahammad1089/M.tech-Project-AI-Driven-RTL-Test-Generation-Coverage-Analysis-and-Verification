#!/usr/bin/env python3

"""
Day 17 - FSM Targeted Sequence Generator

Project:
AI-Driven RTL Test Generation, Coverage Analysis and Verification

Purpose:
1. Read FSM knowledge from Day 16.
2. Read FSM coverage gaps from Day 17.
3. Identify uncovered FSM transitions.
4. Generate deterministic input sequences that exercise them.
5. Save the targeted sequences as JSON.

Default inputs:
results/fsm/day16/fsm_knowledge.json
results/fsm/day17/fsm_baseline_gaps.json

Default output:
results/fsm/day17/fsm_targeted_sequences.json
"""

import argparse
import json
import sys
from collections import deque
from pathlib import Path


# ============================================================
# PROJECT PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

DEFAULT_KNOWLEDGE = (
    ROOT
    / "results"
    / "fsm"
    / "day16"
    / "fsm_knowledge.json"
)

DEFAULT_GAPS = (
    ROOT
    / "results"
    / "fsm"
    / "day17"
    / "fsm_baseline_gaps.json"
)

DEFAULT_OUTPUT = (
    ROOT
    / "results"
    / "fsm"
    / "day17"
    / "fsm_targeted_sequences.json"
)


# ============================================================
# CANONICAL 1011 FSM TRANSITION MAP
#
# State meaning:
#
# S0 = no useful prefix
# S1 = saw 1
# S2 = saw 10
# S3 = saw 101
#
# TR_008 produces sequence detection for 1011.
# ============================================================

CANONICAL_TRANSITIONS = [

    {
        "transition_id": "TR_001",
        "from_state": "S0",
        "input": 0,
        "to_state": "S0",
        "detected": 0,
    },

    {
        "transition_id": "TR_002",
        "from_state": "S0",
        "input": 1,
        "to_state": "S1",
        "detected": 0,
    },

    {
        "transition_id": "TR_003",
        "from_state": "S1",
        "input": 0,
        "to_state": "S2",
        "detected": 0,
    },

    {
        "transition_id": "TR_004",
        "from_state": "S1",
        "input": 1,
        "to_state": "S1",
        "detected": 0,
    },

    {
        "transition_id": "TR_005",
        "from_state": "S2",
        "input": 0,
        "to_state": "S0",
        "detected": 0,
    },

    {
        "transition_id": "TR_006",
        "from_state": "S2",
        "input": 1,
        "to_state": "S3",
        "detected": 0,
    },

    {
        "transition_id": "TR_007",
        "from_state": "S3",
        "input": 0,
        "to_state": "S2",
        "detected": 0,
    },

    {
        "transition_id": "TR_008",
        "from_state": "S3",
        "input": 1,
        "to_state": "S1",
        "detected": 1,
    },
]


# ============================================================
# JSON LOAD
# ============================================================

def load_json(path):

    if not path.exists():

        raise FileNotFoundError(
            f"File not found: {path}"
        )

    try:

        with path.open(
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(
                file
            )

    except json.JSONDecodeError as exc:

        raise ValueError(
            f"Invalid JSON in {path}: "
            f"line {exc.lineno}, "
            f"column {exc.colno}: "
            f"{exc.msg}"
        ) from exc

    if not isinstance(
        data,
        dict
    ):

        raise ValueError(
            f"Expected a JSON object in {path}"
        )

    return data


# ============================================================
# JSON SAVE
# ============================================================

def save_json(
    path,
    data
):

    path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with path.open(
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            indent=2
        )

        file.write(
            "\n"
        )


# ============================================================
# HELPER
# ============================================================

def first_value(
    record,
    keys,
    default=None
):

    for key in keys:

        if (
            key in record
            and record[key] is not None
        ):

            return record[key]

    return default


# ============================================================
# NORMALIZE INPUT BIT
# ============================================================

def normalize_bit(
    value
):

    if isinstance(
        value,
        bool
    ):

        return int(
            value
        )

    if isinstance(
        value,
        int
    ):

        return (
            1
            if value
            else 0
        )

    text = str(
        value
    ).strip().lower()

    if text in {
        "1",
        "1'b1",
        "true",
        "high"
    }:

        return 1

    if text in {
        "0",
        "1'b0",
        "false",
        "low"
    }:

        return 0

    raise ValueError(
        f"Cannot interpret FSM input bit: {value!r}"
    )


# ============================================================
# NORMALIZE STATE
# ============================================================

def normalize_state(
    value
):

    if value is None:

        return None

    text = str(
        value
    ).strip()

    state_aliases = {

        "00": "S0",
        "01": "S1",
        "10": "S2",
        "11": "S3",

        "2'b00": "S0",
        "2'b01": "S1",
        "2'b10": "S2",
        "2'b11": "S3",
    }

    return state_aliases.get(
        text,
        text
    )


# ============================================================
# NORMALIZE TRANSITION RECORD
# ============================================================

def normalize_transition_record(
    record
):

    if not isinstance(
        record,
        dict
    ):

        return None

    transition_id = first_value(
        record,
        [
            "transition_id",
            "id",
            "transition",
            "name"
        ]
    )

    from_state = first_value(
        record,
        [
            "from_state",
            "source_state",
            "source",
            "current_state",
            "from"
        ]
    )

    to_state = first_value(
        record,
        [
            "to_state",
            "destination_state",
            "destination",
            "next_state",
            "to"
        ]
    )

    input_value = first_value(
        record,
        [
            "input",
            "din",
            "input_bit",
            "symbol",
            "condition"
        ]
    )

    detected = first_value(
        record,
        [
            "detected",
            "detect",
            "output",
            "expected_detect"
        ],
        0
    )

    if (
        transition_id is None
        or from_state is None
        or to_state is None
    ):

        return None

    try:

        bit = normalize_bit(
            input_value
        )

    except (
        TypeError,
        ValueError
    ):

        return None

    try:

        detected_bit = normalize_bit(
            detected
        )

    except (
        TypeError,
        ValueError
    ):

        detected_bit = 0

    return {

        "transition_id":
            str(
                transition_id
            ).strip(),

        "from_state":
            normalize_state(
                from_state
            ),

        "input":
            bit,

        "to_state":
            normalize_state(
                to_state
            ),

        "detected":
            detected_bit,
    }


# ============================================================
# FIND TRANSITION LISTS IN KNOWLEDGE JSON
# ============================================================

def recursively_find_transition_lists(
    obj
):

    candidates = []

    if isinstance(
        obj,
        dict
    ):

        for (
            key,
            value
        ) in obj.items():

            if (
                key.lower()
                in {
                    "transitions",
                    "fsm_transitions",
                    "transition_table",
                    "transition_list"
                }
                and isinstance(
                    value,
                    list
                )
            ):

                candidates.append(
                    value
                )

            candidates.extend(
                recursively_find_transition_lists(
                    value
                )
            )

    elif isinstance(
        obj,
        list
    ):

        for item in obj:

            candidates.extend(
                recursively_find_transition_lists(
                    item
                )
            )

    return candidates


# ============================================================
# EXTRACT TRANSITIONS FROM KNOWLEDGE
# ============================================================

def extract_transitions_from_knowledge(
    knowledge
):

    normalized = []

    candidate_lists = (
        recursively_find_transition_lists(
            knowledge
        )
    )

    for candidate_list in candidate_lists:

        for record in candidate_list:

            transition = (
                normalize_transition_record(
                    record
                )
            )

            if transition is not None:

                normalized.append(
                    transition
                )

    unique = {}

    for transition in normalized:

        unique[
            transition[
                "transition_id"
            ]
        ] = transition

    result = list(
        unique.values()
    )

    known_ids = {
        item["transition_id"]
        for item in result
    }

    # --------------------------------------------------------
    # If Day-16 knowledge has useful transition information,
    # use it.
    #
    # Otherwise use the known 1011 FSM transition map.
    # --------------------------------------------------------

    if {
        "TR_005",
        "TR_007"
    }.issubset(
        known_ids
    ):

        return (
            result,
            True
        )

    return (
        CANONICAL_TRANSITIONS,
        False
    )


# ============================================================
# GET MISSING TRANSITIONS FROM GAP REPORT
# ============================================================

def get_missing_transition_ids(
    gaps
):

    direct = gaps.get(
        "missing_transition_ids"
    )

    if isinstance(
        direct,
        list
    ):

        ids = [

            str(
                item
            ).strip()

            for item in direct

            if str(
                item
            ).strip()
        ]

        if ids:

            return ids

    gap_entries = gaps.get(
        "gaps",
        []
    )

    ids = []

    if isinstance(
        gap_entries,
        list
    ):

        for entry in gap_entries:

            if not isinstance(
                entry,
                dict
            ):

                continue

            transition_id = (
                entry.get(
                    "transition_id"
                )
            )

            if transition_id:

                ids.append(
                    str(
                        transition_id
                    ).strip()
                )

    return ids


# ============================================================
# DETERMINE GAP STATUS
# ============================================================

def determine_gap_status(
    gaps
):

    baseline_summary = gaps.get(
        "baseline_summary",
        {}
    )

    if isinstance(
        baseline_summary,
        dict
    ):

        coverage_complete = (
            baseline_summary.get(
                "coverage_complete"
            )
        )

        if coverage_complete is True:

            return (
                "coverage_complete"
            )

        if coverage_complete is False:

            return (
                "coverage_incomplete"
            )

    if get_missing_transition_ids(
        gaps
    ):

        return (
            "coverage_incomplete"
        )

    return (
        "unknown"
    )


# ============================================================
# DETERMINE RESET STATE
# ============================================================

def determine_reset_state(
    knowledge,
    transitions
):

    possible_values = [

        knowledge.get(
            "reset_state"
        ),

        knowledge.get(
            "initial_state"
        ),

        knowledge.get(
            "start_state"
        ),
    ]

    fsm_section = knowledge.get(
        "fsm"
    )

    if isinstance(
        fsm_section,
        dict
    ):

        possible_values.extend(
            [

                fsm_section.get(
                    "reset_state"
                ),

                fsm_section.get(
                    "initial_state"
                ),

                fsm_section.get(
                    "start_state"
                ),
            ]
        )

    for value in possible_values:

        if value is not None:

            return normalize_state(
                value
            )

    states = {

        item["from_state"]

        for item in transitions
    }

    states.update(
        item["to_state"]
        for item in transitions
    )

    if "S0" in states:

        return "S0"

    if states:

        return sorted(
            states
        )[0]

    return "S0"


# ============================================================
# BUILD FSM GRAPH
# ============================================================

def build_adjacency(
    transitions
):

    adjacency = {}

    for transition in transitions:

        adjacency.setdefault(
            transition[
                "from_state"
            ],
            []
        ).append(
            transition
        )

    for state in adjacency:

        adjacency[
            state
        ].sort(

            key=lambda item: (
                item[
                    "input"
                ],
                item[
                    "transition_id"
                ]
            )
        )

    return adjacency


# ============================================================
# SHORTEST PATH TO FSM STATE
# ============================================================

def shortest_path_to_state(
    reset_state,
    target_state,
    adjacency
):

    if reset_state == target_state:

        return []

    queue = deque()

    queue.append(
        (
            reset_state,
            []
        )
    )

    visited = {
        reset_state
    }

    while queue:

        (
            state,
            path
        ) = queue.popleft()

        for transition in adjacency.get(
            state,
            []
        ):

            next_state = (
                transition[
                    "to_state"
                ]
            )

            new_path = (
                path
                + [
                    transition
                ]
            )

            if (
                next_state
                == target_state
            ):

                return new_path

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
                        new_path
                    )
                )

    return None


# ============================================================
# EXPECTED OUTPUT SEQUENCE
# ============================================================

def sequence_outputs(
    path
):

    return [

        int(
            item.get(
                "detected",
                0
            )
        )

        for item in path
    ]


# ============================================================
# BUILD ONE TARGET
# ============================================================

def build_target(
    transition_id,
    transition_map,
    reset_state,
    adjacency
):

    if (
        transition_id
        not in transition_map
    ):

        return {

            "target_id":
                f"TARGET_{transition_id}",

            "transition_id":
                transition_id,

            "status":
                "unresolved",

            "reason":
                (
                    "Transition ID not found "
                    "in FSM transition map."
                ),
        }

    target_transition = (
        transition_map[
            transition_id
        ]
    )

    path_to_source = (
        shortest_path_to_state(

            reset_state,

            target_transition[
                "from_state"
            ],

            adjacency
        )
    )

    if path_to_source is None:

        return {

            "target_id":
                f"TARGET_{transition_id}",

            "transition_id":
                transition_id,

            "status":
                "unresolved",

            "reason":
                (
                    "Could not find path from "
                    f"reset state {reset_state} "
                    "to source state "
                    f"{target_transition['from_state']}."
                ),
        }

    full_path = (
        path_to_source
        + [
            target_transition
        ]
    )

    input_sequence = [

        item[
            "input"
        ]

        for item in full_path
    ]

    expected_detect = (
        sequence_outputs(
            full_path
        )
    )

    return {

        "target_id":
            f"TARGET_{transition_id}",

        "transition_id":
            transition_id,

        "status":
            "generated",

        "objective":
            (
                "Exercise uncovered FSM "
                f"transition {transition_id}."
            ),

        "reset_state":
            reset_state,

        "from_state":
            target_transition[
                "from_state"
            ],

        "target_input":
            target_transition[
                "input"
            ],

        "to_state":
            target_transition[
                "to_state"
            ],

        "input_sequence":
            input_sequence,

        "sequence_string":
            "".join(
                str(
                    bit
                )
                for bit
                in input_sequence
            ),

        "expected_detect_sequence":
            expected_detect,

        "expected_target_detect":
            target_transition[
                "detected"
            ],

        "path_transition_ids":
            [

                item[
                    "transition_id"
                ]

                for item
                in full_path
            ],
    }


# ============================================================
# BUILD COMPLETE OUTPUT JSON
# ============================================================

def build_output(
    knowledge,
    gaps
):

    (
        transitions,
        knowledge_used

    ) = extract_transitions_from_knowledge(
        knowledge
    )

    transition_map = {

        item[
            "transition_id"
        ]:
            item

        for item
        in transitions
    }

    adjacency = build_adjacency(
        transitions
    )

    reset_state = (
        determine_reset_state(
            knowledge,
            transitions
        )
    )

    missing_transition_ids = (
        get_missing_transition_ids(
            gaps
        )
    )

    targets = [

        build_target(

            transition_id,

            transition_map,

            reset_state,

            adjacency

        )

        for transition_id
        in missing_transition_ids
    ]

    generated_targets = [

        target

        for target
        in targets

        if target.get(
            "status"
        )
        == "generated"
    ]

    unresolved_targets = [

        target

        for target
        in targets

        if target.get(
            "status"
        )
        != "generated"
    ]

    return {

        "dut":
            "fsm_1011",

        "source_gap_status":
            determine_gap_status(
                gaps
            ),

        "source_missing_transition_ids":
            missing_transition_ids,

        "target_count":
            len(
                generated_targets
            ),

        "targets":
            targets,

        "unresolved_target_count":
            len(
                unresolved_targets
            ),

        "harness_used":
            False,

        "knowledge_transition_map_used":
            knowledge_used,

        "generation_method":
            "deterministic_fsm_graph_search",
    }


# ============================================================
# ARGUMENT PARSER
#
# Supports:
#
# python coverage/fsm_targeted_sequence_generator.py
#
# OR:
#
# python coverage/fsm_targeted_sequence_generator.py \
# results/fsm/day16/fsm_knowledge.json \
# results/fsm/day17/fsm_baseline_gaps.json \
# results/fsm/day17/fsm_targeted_sequences.json
# ============================================================

def parse_arguments():

    parser = argparse.ArgumentParser(

        description=(
            "Generate deterministic FSM "
            "input sequences for uncovered "
            "Day-17 transitions."
        )
    )

    parser.add_argument(

        "knowledge",

        nargs="?",

        type=Path,

        default=DEFAULT_KNOWLEDGE,

        help=(
            "FSM knowledge JSON. "
            "Default: "
            "results/fsm/day16/"
            "fsm_knowledge.json"
        )
    )

    parser.add_argument(

        "gaps",

        nargs="?",

        type=Path,

        default=DEFAULT_GAPS,

        help=(
            "FSM gap report JSON. "
            "Default: "
            "results/fsm/day17/"
            "fsm_baseline_gaps.json"
        )
    )

    parser.add_argument(

        "output",

        nargs="?",

        type=Path,

        default=DEFAULT_OUTPUT,

        help=(
            "Output targeted sequence JSON. "
            "Default: "
            "results/fsm/day17/"
            "fsm_targeted_sequences.json"
        )
    )

    return parser.parse_args()


# ============================================================
# RESOLVE PATH
# ============================================================

def resolve_path(
    path
):

    if path.is_absolute():

        return path

    return (
        ROOT
        / path
    )


# ============================================================
# MAIN
# ============================================================

def main():

    args = parse_arguments()

    knowledge_path = resolve_path(
        args.knowledge
    )

    gaps_path = resolve_path(
        args.gaps
    )

    output_path = resolve_path(
        args.output
    )

    try:

        knowledge = load_json(
            knowledge_path
        )

        gaps = load_json(
            gaps_path
        )

        output_data = build_output(
            knowledge,
            gaps
        )

        save_json(
            output_path,
            output_data
        )

    except (
        FileNotFoundError,
        ValueError,
        KeyError,
        OSError
    ) as exc:

        print(
            f"ERROR: {exc}",
            file=sys.stderr
        )

        return 1

    print(
        "=" * 64
    )

    print(
        "DAY 17 FSM TARGETED SEQUENCE GENERATION"
    )

    print(
        "=" * 64
    )

    print(
        "Gap status        : "
        f"{output_data['source_gap_status']}"
    )

    print(
        "Missing targets   : "
        f"{len(output_data['source_missing_transition_ids'])}"
    )

    print(
        "Generated targets : "
        f"{output_data['target_count']}"
    )

    print(
        "Unresolved targets: "
        f"{output_data['unresolved_target_count']}"
    )

    print(
        "-" * 64
    )

    for target in output_data[
        "targets"
    ]:

        if (
            target.get(
                "status"
            )
            == "generated"
        ):

            print(
                f"{target['transition_id']}: "
                f"sequence="
                f"{target['sequence_string']} "
                f"path="
                f"{target['path_transition_ids']}"
            )

        else:

            print(
                f"{target['transition_id']}: "
                "UNRESOLVED - "
                f"{target.get('reason', 'unknown reason')}"
            )

    print(
        "-" * 64
    )

    try:

        display_path = (
            output_path.relative_to(
                ROOT
            )
        )

    except ValueError:

        display_path = output_path

    print(
        "Output written to : "
        f"{display_path}"
    )

    print(
        "=" * 64
    )

    return 0


# ============================================================
# PROGRAM ENTRY
# ============================================================

if __name__ == "__main__":

    sys.exit(
        main()
    )
