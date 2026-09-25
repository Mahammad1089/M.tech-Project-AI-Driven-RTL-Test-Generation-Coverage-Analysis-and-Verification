import json
import sys

from pathlib import Path


TARGET_LIBRARY = {

    "COV_FIFO_001": {

        "description":
            "Apply synchronous reset.",

        "actions": [
            {
                "action": "RESET"
            }
        ]
    },


    "COV_FIFO_002": {

        "description":
            "Perform one successful write.",

        "actions": [
            {
                "action": "RESET"
            },
            {
                "action": "WRITE",
                "data": 17
            }
        ]
    },


    "COV_FIFO_003": {

        "description":
            "Write one value and read it.",

        "actions": [
            {
                "action": "RESET"
            },
            {
                "action": "WRITE",
                "data": 34
            },
            {
                "action": "READ",
                "expected": 34
            }
        ]
    },


    "COV_FIFO_004": {

        "description":
            "Execute an idle cycle.",

        "actions": [
            {
                "action": "RESET"
            },
            {
                "action": "IDLE"
            }
        ]
    },


    "COV_FIFO_005": {

        "description":
            "Exercise simultaneous legal write/read.",

        "actions": [
            {
                "action": "RESET"
            },
            {
                "action": "WRITE",
                "data": 49
            },
            {
                "action": "SIMULTANEOUS",
                "data": 50,
                "expected": 49
            }
        ]
    },


    "COV_FIFO_006": {

        "description":
            "Observe the empty FIFO state.",

        "actions": [
            {
                "action": "RESET"
            },
            {
                "action": "IDLE"
            }
        ]
    },


    "COV_FIFO_007": {

        "description":
            "Fill FIFO to depth four.",

        "actions": [
            {
                "action": "RESET"
            },
            {
                "action": "WRITE",
                "data": 65
            },
            {
                "action": "WRITE",
                "data": 66
            },
            {
                "action": "WRITE",
                "data": 67
            },
            {
                "action": "WRITE",
                "data": 68
            }
        ]
    },


    "COV_FIFO_008": {

        "description":
            "Attempt read while FIFO is empty.",

        "actions": [
            {
                "action": "RESET"
            },
            {
                "action": "READ_EMPTY"
            }
        ]
    },


    "COV_FIFO_009": {

        "description":
            "Fill FIFO then attempt another write.",

        "actions": [
            {
                "action": "RESET"
            },
            {
                "action": "WRITE",
                "data": 81
            },
            {
                "action": "WRITE",
                "data": 82
            },
            {
                "action": "WRITE",
                "data": 83
            },
            {
                "action": "WRITE",
                "data": 84
            },
            {
                "action": "WRITE_FULL",
                "data": 85
            }
        ]
    },


    "COV_FIFO_010": {

        "description":
            "Drive successful writes across "
            "the write-pointer wrap boundary.",

        "actions": [
            {
                "action": "RESET"
            },
            {
                "action": "WRITE",
                "data": 97
            },
            {
                "action": "WRITE",
                "data": 98
            },
            {
                "action": "WRITE",
                "data": 99
            },
            {
                "action": "READ",
                "expected": 97
            },
            {
                "action": "WRITE",
                "data": 100
            }
        ]
    },
}


def main():

    if len(
        sys.argv
    ) != 3:

        print(
            "Usage: python "
            "coverage/fifo_target_generator.py "
            "<gaps.json> "
            "<targets.json>"
        )

        sys.exit(1)


    try:

        gaps = json.loads(

            Path(
                sys.argv[1]
            ).read_text()
        )


        targets = []


        for index, gap in enumerate(
            gaps[
                "gaps"
            ],
            start=1
        ):

            coverage_id = gap[
                "coverage_id"
            ]


            if (
                coverage_id
                not in TARGET_LIBRARY
            ):

                raise ValueError(
                    "No deterministic target "
                    f"for {coverage_id}"
                )


            template = (
                TARGET_LIBRARY[
                    coverage_id
                ]
            )


            targets.append({

                "target_id":
                    f"FIFO_TARGET_{index:03d}",

                "coverage_id":
                    coverage_id,

                "behavior":
                    gap[
                        "behavior"
                    ],

                "description":
                    template[
                        "description"
                    ],

                "actions":
                    template[
                        "actions"
                    ],

                "generation_method":
                    "deterministic_target_library",
            })


        report = {

            "dut":
                "fifo",

            "source_gap_status":
                gaps[
                    "gap_status"
                ],

            "target_count":
                len(targets),

            "targets":
                targets,

            "hermes_used":
                False,

            "generation_method":
                "deterministic_target_library",
        }


    except Exception as error:

        print(
            "FIFO TARGET GENERATION: FAIL"
        )

        print(
            "ERROR:",
            error
        )

        sys.exit(1)


    Path(
        sys.argv[2]
    ).write_text(

        json.dumps(
            report,
            indent=4
        )
    )


    print(
        "FIFO TARGET GENERATION: PASS"
    )

    print(
        "Targets generated:",
        len(targets)
    )


if __name__ == "__main__":
    main()
