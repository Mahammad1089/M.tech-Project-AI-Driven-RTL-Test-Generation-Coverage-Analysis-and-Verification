import json
import sys
from pathlib import Path


FSM_KNOWLEDGE = {

    "dut":
        "fsm_1011",

    "design_type":
        "sequential_fsm",

    "sequence":
        "1011",

    "overlap_enabled":
        True,

    "clock": {
        "signal":
            "clk",

        "edge":
            "posedge"
    },

    "reset": {
        "signal":
            "rst",

        "active_level":
            1,

        "type":
            "synchronous",

        "reset_state":
            "IDLE"
    },

    "inputs": [
        {
            "name":
                "din",

            "width":
                1
        }
    ],

    "outputs": [
        {
            "name":
                "detected",

            "width":
                1
        }
    ],

    "state_register":
        "current_state",

    "next_state_signal":
        "next_state",

    "states": [
        {
            "name":
                "IDLE",

            "encoding":
                "2'b00",

            "meaning":
                "No useful prefix matched"
        },

        {
            "name":
                "S1",

            "encoding":
                "2'b01",

            "meaning":
                "Prefix 1 matched"
        },

        {
            "name":
                "S10",

            "encoding":
                "2'b10",

            "meaning":
                "Prefix 10 matched"
        },

        {
            "name":
                "S101",

            "encoding":
                "2'b11",

            "meaning":
                "Prefix 101 matched"
        }
    ],

    "transitions": [

        {
            "transition_id":
                "TR_001",

            "from":
                "IDLE",

            "input":
                0,

            "to":
                "IDLE",

            "detected":
                0
        },

        {
            "transition_id":
                "TR_002",

            "from":
                "IDLE",

            "input":
                1,

            "to":
                "S1",

            "detected":
                0
        },

        {
            "transition_id":
                "TR_003",

            "from":
                "S1",

            "input":
                0,

            "to":
                "S10",

            "detected":
                0
        },

        {
            "transition_id":
                "TR_004",

            "from":
                "S1",

            "input":
                1,

            "to":
                "S1",

            "detected":
                0
        },

        {
            "transition_id":
                "TR_005",

            "from":
                "S10",

            "input":
                0,

            "to":
                "IDLE",

            "detected":
                0
        },

        {
            "transition_id":
                "TR_006",

            "from":
                "S10",

            "input":
                1,

            "to":
                "S101",

            "detected":
                0
        },

        {
            "transition_id":
                "TR_007",

            "from":
                "S101",

            "input":
                0,

            "to":
                "S10",

            "detected":
                0
        },

        {
            "transition_id":
                "TR_008",

            "from":
                "S101",

            "input":
                1,

            "to":
                "S1",

            "detected":
                1
        }
    ],

    "detection_transition":
        "TR_008",

    "knowledge_source":
        "deterministic_day16_fsm_model",

    "coverage_measured":
        False
}


def main():

    if len(sys.argv) != 2:

        print(
            "Usage: python "
            "parser/fsm_analyzer.py "
            "<output_json>"
        )

        sys.exit(1)

    output = Path(
        sys.argv[1]
    )

    output.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    output.write_text(
        json.dumps(
            FSM_KNOWLEDGE,
            indent=4
        )
    )

    print(
        "FSM KNOWLEDGE GENERATION: PASS"
    )

    print(
        "States:",
        len(
            FSM_KNOWLEDGE[
                "states"
            ]
        )
    )

    print(
        "Transitions:",
        len(
            FSM_KNOWLEDGE[
                "transitions"
            ]
        )
    )

    print(
        "Coverage measured:",
        FSM_KNOWLEDGE[
            "coverage_measured"
        ]
    )


if __name__ == "__main__":
    main()
