#!/usr/bin/env python3

"""
Day 17 - FSM Trace Merger

Project:
AI-Driven RTL Test Generation, Coverage Analysis and Verification

Purpose:
1. Read the Day-17 baseline FSM execution trace.
2. Read the Day-17 targeted closure trace.
3. Accept the different CSV column formats used by both traces.
4. Normalize both files to one common format.
5. Produce fsm_combined_trace.csv for final coverage analysis.

Expected baseline trace:
    from_state,input,to_state,detected

Expected targeted trace:
    from_state,input,to_state,detected,result

Output:
    from_state,input,to_state,detected
"""

import argparse
import csv
import sys
from pathlib import Path


# ============================================================
# PROJECT ROOT
# ============================================================

ROOT = Path(__file__).resolve().parents[1]


# ============================================================
# CANONICAL TRACE FORMAT
# ============================================================

CANONICAL_COLUMNS = [
    "from_state",
    "input",
    "to_state",
    "detected",
]


# ============================================================
# COLUMN ALIASES
# ============================================================

COLUMN_ALIASES = {

    "from_state": [
        "from_state",
        "source_state",
        "current_state",
        "from",
    ],

    "input": [
        "input",
        "din",
        "input_bit",
        "symbol",
    ],

    "to_state": [
        "to_state",
        "next_state",
        "destination_state",
        "to",
    ],

    "detected": [
        "detected",
        "detect",
        "output",
        "expected_detect",
    ],
}


# ============================================================
# RESOLVE PATH
# ============================================================

def resolve_path(path):

    path = Path(path)

    if path.is_absolute():
        return path

    return ROOT / path


# ============================================================
# CLEAN HEADER NAME
# ============================================================

def clean_header(value):

    if value is None:
        return ""

    return (
        str(value)
        .replace("\ufeff", "")
        .strip()
        .lower()
    )


# ============================================================
# BUILD COLUMN MAP
# ============================================================

def build_column_map(fieldnames):

    if not fieldnames:

        raise ValueError(
            "Trace file has no CSV header."
        )

    cleaned_headers = {

        clean_header(name): name
        for name in fieldnames
        if name is not None
    }

    column_map = {}


    for canonical_name in CANONICAL_COLUMNS:

        aliases = COLUMN_ALIASES[
            canonical_name
        ]

        matched_column = None


        for alias in aliases:

            if alias in cleaned_headers:

                matched_column = (
                    cleaned_headers[
                        alias
                    ]
                )

                break


        if matched_column is None:

            raise ValueError(
                "Missing required trace column "
                f"'{canonical_name}'. "
                f"Found columns: {fieldnames}"
            )


        column_map[
            canonical_name
        ] = matched_column


    return column_map


# ============================================================
# NORMALIZE STATE
# ============================================================

def normalize_state(value):

    text = str(
        value
    ).strip()

    aliases = {

        "s0": "00",
        "s1": "01",
        "s2": "10",
        "s3": "11",

        "2'b00": "00",
        "2'b01": "01",
        "2'b10": "10",
        "2'b11": "11",
    }

    lowered = text.lower()

    if lowered in aliases:

        return aliases[
            lowered
        ]

    return text


# ============================================================
# NORMALIZE BIT
# ============================================================

def normalize_bit(value):

    text = str(
        value
    ).strip().lower()

    if text in {
        "0",
        "1'b0",
        "false",
        "low",
    }:

        return "0"

    if text in {
        "1",
        "1'b1",
        "true",
        "high",
    }:

        return "1"

    return str(
        value
    ).strip()


# ============================================================
# READ TRACE FILE
# ============================================================

def read_trace(path, trace_name):

    if not path.exists():

        raise FileNotFoundError(
            f"{trace_name} trace not found: {path}"
        )


    rows = []


    with path.open(
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        reader = csv.DictReader(
            file
        )


        column_map = build_column_map(
            reader.fieldnames
        )


        for line_number, row in enumerate(
            reader,
            start=2
        ):

            if row is None:

                continue


            # -----------------------------------------------
            # Skip completely blank rows
            # -----------------------------------------------

            values = [

                str(value).strip()

                for value in row.values()

                if value is not None
            ]


            if not any(values):

                continue


            from_state = normalize_state(
                row.get(
                    column_map[
                        "from_state"
                    ],
                    ""
                )
            )


            input_bit = normalize_bit(
                row.get(
                    column_map[
                        "input"
                    ],
                    ""
                )
            )


            to_state = normalize_state(
                row.get(
                    column_map[
                        "to_state"
                    ],
                    ""
                )
            )


            detected = normalize_bit(
                row.get(
                    column_map[
                        "detected"
                    ],
                    ""
                )
            )


            # -----------------------------------------------
            # Validate required values
            # -----------------------------------------------

            if (
                from_state == ""
                or input_bit == ""
                or to_state == ""
                or detected == ""
            ):

                raise ValueError(
                    f"{trace_name} trace line "
                    f"{line_number} contains "
                    "missing required values."
                )


            rows.append(

                {
                    "from_state":
                        from_state,

                    "input":
                        input_bit,

                    "to_state":
                        to_state,

                    "detected":
                        detected,
                }
            )


    return rows


# ============================================================
# WRITE COMBINED TRACE
# ============================================================

def write_combined_trace(
    output_path,
    rows
):

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )


    with output_path.open(
        "w",
        encoding="utf-8",
        newline=""
    ) as file:

        writer = csv.DictWriter(

            file,

            fieldnames=
                CANONICAL_COLUMNS
        )


        writer.writeheader()


        for row in rows:

            writer.writerow(
                row
            )


# ============================================================
# ARGUMENT PARSER
# ============================================================

def parse_arguments():

    parser = argparse.ArgumentParser(

        description=(
            "Merge Day-17 baseline and targeted "
            "FSM execution traces."
        )
    )


    parser.add_argument(

        "baseline_trace",

        type=Path,

        help=(
            "Baseline FSM execution trace CSV."
        )
    )


    parser.add_argument(

        "targeted_trace",

        type=Path,

        help=(
            "Targeted FSM closure trace CSV."
        )
    )


    parser.add_argument(

        "output_trace",

        type=Path,

        help=(
            "Combined FSM execution trace CSV."
        )
    )


    return parser.parse_args()


# ============================================================
# MAIN
# ============================================================

def main():

    args = parse_arguments()


    baseline_path = resolve_path(
        args.baseline_trace
    )


    targeted_path = resolve_path(
        args.targeted_trace
    )


    output_path = resolve_path(
        args.output_trace
    )


    try:

        # ----------------------------------------------------
        # Read baseline
        # ----------------------------------------------------

        baseline_rows = read_trace(

            baseline_path,

            "Baseline"
        )


        # ----------------------------------------------------
        # Read targeted closure trace
        #
        # Extra columns such as "result" are intentionally
        # accepted and ignored.
        # ----------------------------------------------------

        targeted_rows = read_trace(

            targeted_path,

            "Targeted"
        )


        # ----------------------------------------------------
        # Combine traces
        # ----------------------------------------------------

        combined_rows = (
            baseline_rows
            + targeted_rows
        )


        if not combined_rows:

            raise ValueError(
                "No FSM trace records were found."
            )


        # ----------------------------------------------------
        # Write canonical combined trace
        # ----------------------------------------------------

        write_combined_trace(

            output_path,

            combined_rows
        )


    except (
        FileNotFoundError,
        ValueError,
        OSError
    ) as exc:

        print(
            "FSM TRACE MERGE: FAIL"
        )

        print(
            f"ERROR: {exc}"
        )

        return 1


    # --------------------------------------------------------
    # Success information
    # --------------------------------------------------------

    try:

        display_output = (
            output_path.relative_to(
                ROOT
            )
        )

    except ValueError:

        display_output = output_path


    print(
        "FSM TRACE MERGE: PASS"
    )

    print(
        f"Baseline records : {len(baseline_rows)}"
    )

    print(
        f"Targeted records : {len(targeted_rows)}"
    )

    print(
        f"Combined records : {len(combined_rows)}"
    )

    print(
        f"Output           : {display_output}"
    )


    return 0


# ============================================================
# PROGRAM ENTRY
# ============================================================

if __name__ == "__main__":

    sys.exit(
        main()
    )
