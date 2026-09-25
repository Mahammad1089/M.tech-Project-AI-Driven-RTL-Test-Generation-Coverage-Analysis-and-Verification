import csv
import json
import sys

from pathlib import Path


COVERAGE_POINTS = {

    "COV_FIFO_001": "RESET",

    "COV_FIFO_002": "WRITE",

    "COV_FIFO_003": "READ",

    "COV_FIFO_004": "IDLE",

    "COV_FIFO_005":
        "SIMULTANEOUS_WRITE_READ",

    "COV_FIFO_006":
        "EMPTY_STATE",

    "COV_FIFO_007":
        "FULL_STATE",

    "COV_FIFO_008":
        "READ_WHEN_EMPTY",

    "COV_FIFO_009":
        "WRITE_WHEN_FULL",

    "COV_FIFO_010":
        "POINTER_WRAPAROUND",
}


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


def load_trace(
    path
):

    trace_path = Path(
        path
    )

    if not trace_path.exists():

        raise FileNotFoundError(
            f"Trace not found: {path}"
        )


    with trace_path.open(
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
                "Unexpected FIFO trace columns."
            )

        rows = list(
            reader
        )


    if not rows:

        raise ValueError(
            "FIFO execution trace is empty."
        )


    return rows


def as_int(
    row,
    key
):

    return int(
        row[key]
    )


def main():

    if len(
        sys.argv
    ) != 3:

        print(
            "Usage: python "
            "coverage/fifo_coverage.py "
            "<trace.csv> "
            "<coverage.json>"
        )

        sys.exit(1)


    try:

        rows = load_trace(
            sys.argv[1]
        )


        hits = {

            coverage_id: 0

            for coverage_id
            in COVERAGE_POINTS
        }


        for row in rows:

            rst = as_int(
                row,
                "rst"
            )

            wr_en = as_int(
                row,
                "wr_en"
            )

            rd_en = as_int(
                row,
                "rd_en"
            )

            count_before = as_int(
                row,
                "count_before"
            )

            count_after = as_int(
                row,
                "count_after"
            )

            write_ptr_before = as_int(
                row,
                "write_ptr_before"
            )

            write_ptr_after = as_int(
                row,
                "write_ptr_after"
            )

            read_ptr_before = as_int(
                row,
                "read_ptr_before"
            )

            read_ptr_after = as_int(
                row,
                "read_ptr_after"
            )


            if rst == 1:

                hits[
                    "COV_FIFO_001"
                ] += 1


            if (
                rst == 0
                and wr_en == 1
                and rd_en == 0
                and count_before < 4
            ):

                hits[
                    "COV_FIFO_002"
                ] += 1


            if (
                rst == 0
                and rd_en == 1
                and wr_en == 0
                and count_before > 0
            ):

                hits[
                    "COV_FIFO_003"
                ] += 1


            if (
                rst == 0
                and wr_en == 0
                and rd_en == 0
            ):

                hits[
                    "COV_FIFO_004"
                ] += 1


            if (
                rst == 0
                and wr_en == 1
                and rd_en == 1
                and count_before > 0
                and count_before < 4
            ):

                hits[
                    "COV_FIFO_005"
                ] += 1


            if (
                count_before == 0
                or count_after == 0
            ):

                hits[
                    "COV_FIFO_006"
                ] += 1


            if (
                count_before == 4
                or count_after == 4
            ):

                hits[
                    "COV_FIFO_007"
                ] += 1


            if (
                rst == 0
                and rd_en == 1
                and count_before == 0
            ):

                hits[
                    "COV_FIFO_008"
                ] += 1


            if (
                rst == 0
                and wr_en == 1
                and count_before == 4
            ):

                hits[
                    "COV_FIFO_009"
                ] += 1


            write_wrap = (

                wr_en == 1
                and count_before < 4
                and write_ptr_before == 3
                and write_ptr_after == 0
            )


            read_wrap = (

                rd_en == 1
                and count_before > 0
                and read_ptr_before == 3
                and read_ptr_after == 0
            )


            if (
                write_wrap
                or read_wrap
            ):

                hits[
                    "COV_FIFO_010"
                ] += 1


        covered = [

            coverage_id

            for coverage_id,
            hit_count
            in hits.items()

            if hit_count > 0
        ]


        missing = [

            coverage_id

            for coverage_id,
            hit_count
            in hits.items()

            if hit_count == 0
        ]


        total_points = len(
            COVERAGE_POINTS
        )

        covered_points = len(
            covered
        )


        coverage_percent = round(

            (
                covered_points
                / total_points
            )
            * 100,

            2
        )


        report = {

            "dut":
                "fifo",

            "coverage_type":
                "fifo_functional_coverage",

            "measurement_source":
                "executed_fifo_trace",

            "trace_rows":
                len(rows),

            "total_coverage_points":
                total_points,

            "covered_coverage_points":
                covered_points,

            "coverage_percent":
                coverage_percent,

            "covered_points":
                covered,

            "missing_points":
                missing,

            "point_hits":
                hits,

            "point_definitions":
                COVERAGE_POINTS,

            "coverage_complete":
                len(missing) == 0,
        }


    except Exception as error:

        print(
            "FIFO COVERAGE ANALYSIS: FAIL"
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
        "FIFO COVERAGE ANALYSIS: PASS"
    )

    print(
        "Trace rows       :",
        report[
            "trace_rows"
        ]
    )

    print(
        "Covered points   :",
        covered_points,
        "/",
        total_points
    )

    print(
        "Coverage percent :",
        coverage_percent
    )

    print(
        "Missing points   :",
        len(missing)
    )


if __name__ == "__main__":
    main()
