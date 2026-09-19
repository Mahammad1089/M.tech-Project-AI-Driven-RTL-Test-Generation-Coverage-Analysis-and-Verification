import json
from pathlib import Path


RESULT_FILE = Path(
    "results/alu/day8/"
    "day8_hermes_result.json"
)


SUMMARY_FILE = Path(
    "results/alu/day8/"
    "day8_summary.json"
)


def main():

    if not RESULT_FILE.exists():

        print(
            "DAY 8 SUMMARY: FAIL"
        )

        print(
            "Hermes result "
            "file not found."
        )

        raise SystemExit(1)


    result = json.loads(
        RESULT_FILE.read_text()
    )


    response = result.get(
        "response_text",
        ""
    )


    required_operations = [

        "ADD",
        "SUB",
        "AND",
        "OR",
        "XOR",
        "NOT",
        "SHIFT_LEFT",
        "SHIFT_RIGHT"
    ]


    detected_operations = [

        operation

        for operation in (
            required_operations
        )

        if operation in response
    ]


    marker_found = (

        "HERMES RTL ANALYSIS COMPLETE"
        in response

    )


    summary = {

        "day":
            8,

        "dut":
            "alu",

        "integration":
            "Hermes Agent",

        "input_knowledge":
            (
                "results/alu/day6/"
                "alu_knowledge.json"
            ),

        "input_objectives":
            (
                "results/alu/day7/"
                "verification_objectives.json"
            ),

        "prompt_file":
            (
                "hermes/prompts/"
                "alu_day8_prompt.txt"
            ),

        "interface_status":
            result.get(
                "status"
            ),

        "hermes_exit_code":
            result.get(
                "hermes_exit_code"
            ),

        "detected_operations":
            detected_operations,

        "operation_count":
            len(
                detected_operations
            ),

        "completion_marker":
            marker_found,

        "status":
            (
                "PASS"

                if (
                    result.get(
                        "status"
                    ) == "PASS"
                    and marker_found
                    and len(
                        detected_operations
                    ) == 8
                )

                else "FAIL"
            )
    }


    SUMMARY_FILE.write_text(

        json.dumps(
            summary,
            indent=4
        )

    )


    print(
        json.dumps(
            summary,
            indent=4
        )
    )


    if summary[
        "status"
    ] != "PASS":

        raise SystemExit(1)


if __name__ == "__main__":

    main()
