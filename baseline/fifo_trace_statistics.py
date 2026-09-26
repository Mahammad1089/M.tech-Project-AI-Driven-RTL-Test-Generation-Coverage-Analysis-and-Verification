import csv
import json
import sys

from pathlib import Path


EXPECTED_COLUMNS = [

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


def main():

    if len(
        sys.argv
    ) != 4:

        print(
            "Usage: python "
            "baseline/fifo_trace_statistics.py "
            "<strategy> "
            "<trace.csv> "
            "<output.json>"
        )

        sys.exit(1)


    strategy = sys.argv[
        1
    ]


    try:

        with Path(
            sys.argv[2]
        ).open(
            newline=""
        ) as file_handle:

            reader = csv.DictReader(
                file_handle
            )


            if (
                reader.fieldnames
                != EXPECTED_COLUMNS
            ):

                raise ValueError(
                    "Unexpected trace columns."
                )


            rows = list(
                reader
            )


        if not rows:

            raise ValueError(
                "Trace is empty."
            )


        reset_cycles = 0

        stimulus_cycles = 0

        idle_cycles = 0

        write_requests = 0

        read_requests = 0

        simultaneous_requests = 0

        blocked_writes = 0

        blocked_reads = 0


        unique_signatures = set()


        for row in rows:

            rst = int(
                row[
                    "rst"
                ]
            )

            wr_en = int(
                row[
                    "wr_en"
                ]
            )

            rd_en = int(
                row[
                    "rd_en"
                ]
            )

            count_before = int(
                row[
                    "count_before"
                ]
            )


            if rst == 1:

                reset_cycles += 1

                continue


            stimulus_cycles += 1


            if (
                wr_en == 0
                and rd_en == 0
            ):

                idle_cycles += 1


            if wr_en == 1:

                write_requests += 1


            if rd_en == 1:

                read_requests += 1


            if (
                wr_en == 1
                and rd_en == 1
            ):

                simultaneous_requests += 1


            if (
                wr_en == 1
                and count_before == 4
            ):

                blocked_writes += 1


            if (
                rd_en == 1
                and count_before == 0
            ):

                blocked_reads += 1


            signature = (

                wr_en,

                rd_en,

                count_before,
            )


            unique_signatures.add(
                signature
            )


        unique_count = len(
            unique_signatures
        )


        redundant_cycles = max(

            0,

            stimulus_cycles
            - unique_count
        )


        if stimulus_cycles == 0:

            redundancy_percent = 0.0

        else:

            redundancy_percent = round(

                (
                    redundant_cycles
                    / stimulus_cycles
                )
                * 100,

                2
            )


        report = {

            "strategy":
                strategy,

            "trace_rows":
                len(rows),

            "reset_cycles":
                reset_cycles,

            "stimulus_cycles":
                stimulus_cycles,

            "idle_cycles":
                idle_cycles,

            "write_requests":
                write_requests,

            "read_requests":
                read_requests,

            "simultaneous_requests":
                simultaneous_requests,

            "blocked_writes":
                blocked_writes,

            "blocked_reads":
                blocked_reads,

            "unique_behavior_signatures":
                unique_count,

            "redundant_cycles":
                redundant_cycles,

            "redundancy_percent":
                redundancy_percent,

            "signature_definition":
                "(wr_en, rd_en, count_before)",
        }


    except Exception as error:

        print(
            "FIFO TRACE STATISTICS: FAIL"
        )

        print(
            "ERROR:",
            error
        )

        sys.exit(1)


    Path(
        sys.argv[3]
    ).write_text(

        json.dumps(
            report,
            indent=4
        )
    )


    print(
        "FIFO TRACE STATISTICS: PASS"
    )

    print(
        "Strategy          :",
        strategy
    )

    print(
        "Stimulus cycles   :",
        stimulus_cycles
    )

    print(
        "Unique signatures :",
        unique_count
    )

    print(
        "Redundant cycles  :",
        redundant_cycles
    )

    print(
        "Redundancy        :",
        redundancy_percent,
        "%"
    )


if __name__ == "__main__":
    main()
