import json
import sys
from pathlib import Path


REQUIRED_OPERATIONS = {

    "ADD",
    "SUB",
    "AND",
    "OR",
    "XOR",
    "NOT",
    "SHIFT_LEFT",
    "SHIFT_RIGHT"
}


REQUIRED_MARKER = (
    "HERMES RTL ANALYSIS COMPLETE"
)


def fail(
    message
):

    print(
        "HERMES VALIDATION: FAIL"
    )

    print(
        message
    )

    sys.exit(1)


def main():

    if len(sys.argv) != 2:

        print(
            "Usage: python "
            "hermes/"
            "validate_hermes_response.py "
            "<interface_result_json>"
        )

        sys.exit(1)


    path = Path(
        sys.argv[1]
    )


    if not path.exists():

        fail(
            "Interface result "
            "file not found."
        )


    data = json.loads(
        path.read_text()
    )


    if data.get(
        "status"
    ) != "PASS":

        fail(
            "Hermes interface "
            "status is not PASS."
        )


    if data.get(
        "hermes_exit_code"
    ) != 0:

        fail(
            "Hermes exit code "
            "is not zero."
        )


    response = data.get(
        "response_text",
        ""
    )


    if not response.strip():

        fail(
            "Hermes response "
            "is empty."
        )


    missing_operations = [

        operation

        for operation in (
            REQUIRED_OPERATIONS
        )

        if operation not in response
    ]


    if missing_operations:

        fail(
            "Missing operations: "
            + ", ".join(
                missing_operations
            )
        )


    if REQUIRED_MARKER not in response:

        fail(
            "Completion marker "
            "not found."
        )


    print(
        "Hermes interface status : PASS"
    )

    print(
        "Hermes exit code        : PASS"
    )

    print(
        "Response non-empty      : PASS"
    )

    print(
        "Eight ALU operations    : PASS"
    )

    print(
        "Completion marker       : PASS"
    )

    print()

    print(
        "DAY 8 HERMES RESPONSE "
        "VALIDATION: PASS"
    )


if __name__ == "__main__":

    main()
