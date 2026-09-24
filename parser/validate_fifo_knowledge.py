import json
import sys
from pathlib import Path


EXPECTED_PORTS = {
    "clk": ("input", 1),
    "rst": ("input", 1),
    "wr_en": ("input", 1),
    "rd_en": ("input", 1),
    "data_in": ("input", 8),
    "data_out": ("output", 8),
    "full": ("output", 1),
    "empty": ("output", 1),
}


EXPECTED_OPERATIONS = {
    "IDLE",
    "WRITE",
    "READ",
    "SIMULTANEOUS_WRITE_READ",
}


EXPECTED_BLOCKED_OPERATIONS = {
    "WRITE_WHEN_FULL",
    "READ_WHEN_EMPTY",
}


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

    if len(sys.argv) != 2:

        print(
            "Usage: python "
            "parser/validate_fifo_knowledge.py "
            "<fifo_knowledge_json>"
        )

        sys.exit(1)

    try:

        data = load_json(
            sys.argv[1]
        )

        if data.get("dut") != "fifo":

            raise ValueError(
                "Unexpected DUT."
            )


        parameters = data.get(
            "parameters",
            {}
        )

        if parameters.get(
            "data_width"
        ) != 8:

            raise ValueError(
                "DATA_WIDTH must be 8."
            )

        if parameters.get(
            "depth"
        ) != 4:

            raise ValueError(
                "DEPTH must be 4."
            )

        if parameters.get(
            "address_width"
        ) != 2:

            raise ValueError(
                "ADDR_WIDTH must be 2."
            )


        ports = {}

        for port in data.get(
            "ports",
            []
        ):

            name = port.get(
                "name"
            )

            if name in ports:

                raise ValueError(
                    f"Duplicate port: {name}"
                )

            ports[name] = (
                port.get("direction"),
                port.get("width")
            )


        if ports != EXPECTED_PORTS:

            raise ValueError(
                "FIFO port definition mismatch."
            )


        storage = data.get(
            "storage",
            {}
        )

        if storage.get(
            "entries"
        ) != 4:

            raise ValueError(
                "Storage entry count mismatch."
            )

        if storage.get(
            "entry_width"
        ) != 8:

            raise ValueError(
                "Storage width mismatch."
            )


        internal = data.get(
            "internal_state",
            {}
        )

        occupancy = internal.get(
            "occupancy_counter",
            {}
        )

        if occupancy.get(
            "minimum"
        ) != 0:

            raise ValueError(
                "Invalid minimum occupancy."
            )

        if occupancy.get(
            "maximum"
        ) != 4:

            raise ValueError(
                "Invalid maximum occupancy."
            )


        operation_names = {

            item.get("name")

            for item in data.get(
                "operations",
                []
            )
        }

        if operation_names != EXPECTED_OPERATIONS:

            raise ValueError(
                "FIFO operation set mismatch."
            )


        blocked_names = {

            item.get("name")

            for item in data.get(
                "blocked_operations",
                []
            )
        }

        if (
            blocked_names
            != EXPECTED_BLOCKED_OPERATIONS
        ):

            raise ValueError(
                "Blocked-operation set mismatch."
            )


        status = data.get(
            "status_conditions",
            {}
        )

        if (
            status.get(
                "empty",
                {}
            ).get(
                "condition"
            )
            != "count == 0"
        ):

            raise ValueError(
                "Empty condition mismatch."
            )


        if (
            status.get(
                "full",
                {}
            ).get(
                "condition"
            )
            != "count == DEPTH"
        ):

            raise ValueError(
                "Full condition mismatch."
            )


        if (
            data.get(
                "knowledge_status"
            )
            !=
            "FIFO KNOWLEDGE MODEL COMPLETE"
        ):

            raise ValueError(
                "Knowledge status mismatch."
            )


    except (
        FileNotFoundError,
        json.JSONDecodeError,
        ValueError,
        KeyError
    ) as error:

        print(
            "FIFO KNOWLEDGE VALIDATION: FAIL"
        )

        print(
            "ERROR:",
            error
        )

        sys.exit(1)


    print(
        "FIFO KNOWLEDGE VALIDATION: PASS"
    )

    print(
        "DUT              : fifo"
    )

    print(
        "DATA WIDTH       : 8"
    )

    print(
        "DEPTH            : 4"
    )

    print(
        "OPERATIONS       : 4"
    )

    print(
        "BLOCKED CASES    : 2"
    )


if __name__ == "__main__":
    main()
