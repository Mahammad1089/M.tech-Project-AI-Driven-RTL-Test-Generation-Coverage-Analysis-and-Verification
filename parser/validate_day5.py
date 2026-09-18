import json
import sys
from pathlib import Path


EXPECTED_PORTS = {

    "a": {
        "direction": "input",
        "bits": 4
    },

    "b": {
        "direction": "input",
        "bits": 4
    },

    "sel": {
        "direction": "input",
        "bits": 3
    },

    "y": {
        "direction": "output",
        "bits": 4
    }
}


def main():

    if len(sys.argv) != 2:

        print(
            "Usage: python parser/validate_day5.py "
            "<json_file>"
        )

        sys.exit(1)


    json_file = Path(
        sys.argv[1]
    )


    if not json_file.exists():

        print(
            "VALIDATION: FAIL"
        )

        print(
            "JSON file not found."
        )

        sys.exit(1)


    data = json.loads(
        json_file.read_text()
    )


    modules = data.get(
        "modules",
        []
    )


    if len(modules) != 1:

        print(
            "VALIDATION: FAIL"
        )

        print(
            "Expected exactly one module."
        )

        sys.exit(1)


    module = modules[0]


    if module.get(
        "name"
    ) != "alu":

        print(
            "VALIDATION: FAIL"
        )

        print(
            "Module name is not alu."
        )

        sys.exit(1)


    ports = module.get(
        "ports",
        []
    )


    port_map = {

        port["name"]:
            port

        for port in ports

    }


    if len(port_map) != len(ports):

        print(
            "VALIDATION: FAIL"
        )

        print(
            "Duplicate ports detected."
        )

        sys.exit(1)


    for name, expected in EXPECTED_PORTS.items():

        if name not in port_map:

            print(
                f"VALIDATION: FAIL"
            )

            print(
                f"Missing port: {name}"
            )

            sys.exit(1)


        actual = port_map[
            name
        ]


        if (
            actual[
                "direction"
            ]
            != expected[
                "direction"
            ]
        ):

            print(
                "VALIDATION: FAIL"
            )

            print(
                f"Wrong direction for {name}"
            )

            sys.exit(1)


        if (
            actual[
                "width"
            ][
                "bits"
            ]
            != expected[
                "bits"
            ]
        ):

            print(
                "VALIDATION: FAIL"
            )

            print(
                f"Wrong width for {name}"
            )

            sys.exit(1)


    if module.get(
        "case_statements"
    ) != 1:

        print(
            "VALIDATION: FAIL"
        )

        print(
            "Expected one case statement."
        )

        sys.exit(1)


    print(
        "Module name       : PASS"
    )

    print(
        "Port names        : PASS"
    )

    print(
        "Port directions   : PASS"
    )

    print(
        "Port widths       : PASS"
    )

    print(
        "Duplicate check   : PASS"
    )

    print(
        "Case detection    : PASS"
    )

    print()

    print(
        "DAY 5 RTL STRUCTURE VALIDATION: PASS"
    )


if __name__ == "__main__":

    main()
