import csv
import sys

from pathlib import Path


FIELDS = [

    "rst",
    "wr_en",
    "rd_en",
    "count_before",
    "count_after",
    "write_ptr_before",
    "write_ptr_after",
    "read_ptr_before",
    "read_ptr_after",
    "full",
    "empty",
]


def read_trace(
    path
):

    with Path(
        path
    ).open(
        newline=""
    ) as file_handle:

        reader = csv.DictReader(
            file_handle
        )


        if (
            reader.fieldnames
            != FIELDS
        ):

            raise ValueError(
                "Unexpected FIFO trace columns."
            )


        return list(
            reader
        )


def main():

    if len(
        sys.argv
    ) != 4:

        print(
            "Usage: python "
            "coverage/merge_fifo_traces.py "
            "<baseline.csv> "
            "<targeted.csv> "
            "<combined.csv>"
        )

        sys.exit(1)


    try:

        baseline = read_trace(
            sys.argv[1]
        )

        targeted = read_trace(
            sys.argv[2]
        )


        with Path(
            sys.argv[3]
        ).open(
            "w",
            newline=""
        ) as file_handle:

            writer = csv.DictWriter(
                file_handle,
                fieldnames=FIELDS
            )

            writer.writeheader()

            writer.writerows(
                baseline
            )

            writer.writerows(
                targeted
            )


    except Exception as error:

        print(
            "FIFO TRACE MERGE: FAIL"
        )

        print(
            "ERROR:",
            error
        )

        sys.exit(1)


    print(
        "FIFO TRACE MERGE: PASS"
    )

    print(
        "Baseline rows:",
        len(baseline)
    )

    print(
        "Targeted rows:",
        len(targeted)
    )

    print(
        "Combined rows:",
        len(baseline)
        + len(targeted)
    )


if __name__ == "__main__":
    main()
