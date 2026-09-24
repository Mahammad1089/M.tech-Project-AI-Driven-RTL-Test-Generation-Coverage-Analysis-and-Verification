import json
from pathlib import Path


OUTPUT_FILE = Path(
    "results/fifo/day18/fifo_knowledge.json"
)


def build_fifo_knowledge():

    knowledge = {

        "dut": "fifo",

        "benchmark_type": "synchronous_fifo",

        "parameters": {

            "data_width": 8,

            "depth": 4,

            "address_width": 2
        },

        "clocking": {

            "clock": "clk",

            "edge": "posedge"
        },

        "reset": {

            "signal": "rst",

            "active_level": 1,

            "type": "synchronous",

            "effects": [
                "write_ptr becomes zero",
                "read_ptr becomes zero",
                "count becomes zero",
                "data_out becomes zero"
            ]
        },

        "ports": [

            {
                "name": "clk",
                "direction": "input",
                "width": 1
            },

            {
                "name": "rst",
                "direction": "input",
                "width": 1
            },

            {
                "name": "wr_en",
                "direction": "input",
                "width": 1
            },

            {
                "name": "rd_en",
                "direction": "input",
                "width": 1
            },

            {
                "name": "data_in",
                "direction": "input",
                "width": 8
            },

            {
                "name": "data_out",
                "direction": "output",
                "width": 8
            },

            {
                "name": "full",
                "direction": "output",
                "width": 1
            },

            {
                "name": "empty",
                "direction": "output",
                "width": 1
            }
        ],

        "storage": {

            "type": "register_array",

            "entries": 4,

            "entry_width": 8,

            "name": "memory"
        },

        "internal_state": {

            "write_pointer": {

                "name": "write_ptr",

                "width": 2
            },

            "read_pointer": {

                "name": "read_ptr",

                "width": 2
            },

            "occupancy_counter": {

                "name": "count",

                "minimum": 0,

                "maximum": 4
            }
        },

        "status_conditions": {

            "empty": {

                "condition": "count == 0"
            },

            "full": {

                "condition": "count == DEPTH"
            }
        },

        "operations": [

            {
                "operation_id": "FIFO_OP_001",

                "name": "IDLE",

                "request": {
                    "wr_en": 0,
                    "rd_en": 0
                },

                "effect": "No FIFO transaction"
            },

            {
                "operation_id": "FIFO_OP_002",

                "name": "WRITE",

                "condition": "wr_en == 1 and full == 0",

                "effect": [
                    "store data_in at write_ptr",
                    "increment write_ptr",
                    "increment count"
                ]
            },

            {
                "operation_id": "FIFO_OP_003",

                "name": "READ",

                "condition": "rd_en == 1 and empty == 0",

                "effect": [
                    "copy memory at read_ptr to data_out",
                    "increment read_ptr",
                    "decrement count"
                ]
            },

            {
                "operation_id": "FIFO_OP_004",

                "name": "SIMULTANEOUS_WRITE_READ",

                "condition":
                    "wr_en == 1 and rd_en == 1 "
                    "and full == 0 and empty == 0",

                "effect": [
                    "perform one write",
                    "perform one read",
                    "count remains unchanged"
                ]
            }
        ],

        "blocked_operations": [

            {
                "name": "WRITE_WHEN_FULL",

                "condition":
                    "wr_en == 1 and full == 1",

                "expected_behavior":
                    "write transaction is blocked"
            },

            {
                "name": "READ_WHEN_EMPTY",

                "condition":
                    "rd_en == 1 and empty == 1",

                "expected_behavior":
                    "read transaction is blocked"
            }
        ],

        "ordering_property": {

            "type": "FIFO",

            "description":
                "Data must be read in the same order "
                "in which successful writes occurred."
        },

        "verification_targets": [

            "reset behavior",

            "single write",

            "single read",

            "FIFO ordering",

            "empty condition",

            "full condition",

            "write when full",

            "read when empty",

            "pointer wraparound",

            "simultaneous write and read"
        ],

        "knowledge_status":
            "FIFO KNOWLEDGE MODEL COMPLETE"
    }

    return knowledge


def main():

    knowledge = build_fifo_knowledge()

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    OUTPUT_FILE.write_text(
        json.dumps(
            knowledge,
            indent=4
        )
    )

    print(
        "FIFO KNOWLEDGE GENERATION: PASS"
    )

    print(
        "Output:",
        OUTPUT_FILE
    )


if __name__ == "__main__":
    main()
