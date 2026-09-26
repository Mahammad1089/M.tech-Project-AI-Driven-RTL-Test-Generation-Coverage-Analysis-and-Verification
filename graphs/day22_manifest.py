#!/usr/bin/env python3

"""
Day 22 - Graph Manifest
=======================

Purpose:
- Verify all six Day-22 graph PNG files.
- Record file names, sizes and result-copy locations.
- Generate a final Day-22 manifest JSON.
- Use the CURRENT graph filenames.

Outputs:
    results/fifo/day22/day22_manifest.json
"""

import json
import sys
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

GRAPH_DIR = ROOT / "graphs"

DAY22_DIR = (
    ROOT
    / "results"
    / "fifo"
    / "day22"
)

OUTPUT_FILE = (
    DAY22_DIR
    / "day22_manifest.json"
)


# ============================================================
# CURRENT DAY-22 GRAPH FILES
# ============================================================

GRAPH_FILES = [

    {
        "graph_number": 1,
        "name": "Strategy Coverage",
        "graph_path":
            GRAPH_DIR
            / "day22_graph1_strategy_coverage.png",
        "result_path":
            DAY22_DIR
            / "graph1_strategy_coverage.png",
    },

    {
        "graph_number": 2,
        "name": "Seed Coverage",
        "graph_path":
            GRAPH_DIR
            / "day22_graph2_seed_coverage.png",
        "result_path":
            DAY22_DIR
            / "graph2_seed_coverage.png",
    },

    {
        "graph_number": 3,
        "name": "Coverage Distribution",
        "graph_path":
            GRAPH_DIR
            / "day22_graph3_coverage_distribution.png",
        "result_path":
            DAY22_DIR
            / "graph3_coverage_distribution.png",
    },

    {
        "graph_number": 4,
        "name": "Verification Effort",
        "graph_path":
            GRAPH_DIR
            / "day22_graph4_verification_effort.png",
        "result_path":
            DAY22_DIR
            / "graph4_verification_effort.png",
    },

    {
        "graph_number": 5,
        "name": "Random Redundancy",
        "graph_path":
            GRAPH_DIR
            / "day22_graph5_random_redundancy.png",
        "result_path":
            DAY22_DIR
            / "graph5_random_redundancy.png",
    },

    {
        "graph_number": 6,
        "name": "Random Coverage Range",
        "graph_path":
            GRAPH_DIR
            / "day22_graph6_random_range.png",
        "result_path":
            DAY22_DIR
            / "graph6_random_range.png",
    },
]


# ============================================================
# CHECK PNG
# ============================================================

def validate_png(path):

    if not path.exists():

        return {
            "exists": False,
            "valid_png": False,
            "size_bytes": 0,
            "error":
                f"File not found: {path}"
        }


    if not path.is_file():

        return {
            "exists": False,
            "valid_png": False,
            "size_bytes": 0,
            "error":
                f"Not a regular file: {path}"
        }


    size_bytes = (
        path.stat().st_size
    )


    if size_bytes <= 0:

        return {
            "exists": True,
            "valid_png": False,
            "size_bytes": size_bytes,
            "error":
                "PNG file is empty."
        }


    with path.open(
        "rb"
    ) as file:

        signature = file.read(
            8
        )


    expected_signature = (
        b"\x89PNG\r\n\x1a\n"
    )


    valid_png = (
        signature
        == expected_signature
    )


    return {
        "exists": True,
        "valid_png": valid_png,
        "size_bytes": size_bytes,
        "error":
            None
            if valid_png
            else "Invalid PNG signature."
    }


# ============================================================
# RELATIVE PATH
# ============================================================

def relative_path(path):

    try:

        return path.relative_to(
            ROOT
        ).as_posix()

    except ValueError:

        return str(
            path
        )


# ============================================================
# MAIN
# ============================================================

def main():

    try:

        DAY22_DIR.mkdir(
            parents=True,
            exist_ok=True
        )


        manifest_graphs = []

        graph_failures = 0

        copy_failures = 0


        print(
            "=" * 72
        )

        print(
            "DAY 22 GRAPH MANIFEST"
        )

        print(
            "=" * 72
        )


        for graph in GRAPH_FILES:

            number = graph[
                "graph_number"
            ]

            name = graph[
                "name"
            ]

            graph_path = graph[
                "graph_path"
            ]

            result_path = graph[
                "result_path"
            ]


            main_result = (
                validate_png(
                    graph_path
                )
            )


            copy_result = (
                validate_png(
                    result_path
                )
            )


            if not (
                main_result[
                    "exists"
                ]
                and main_result[
                    "valid_png"
                ]
            ):

                graph_failures += 1


            if not (
                copy_result[
                    "exists"
                ]
                and copy_result[
                    "valid_png"
                ]
            ):

                copy_failures += 1


            graph_record = {

                "graph_number":
                    number,

                "name":
                    name,

                "graph_file":
                    relative_path(
                        graph_path
                    ),

                "graph_exists":
                    main_result[
                        "exists"
                    ],

                "graph_valid_png":
                    main_result[
                        "valid_png"
                    ],

                "graph_size_bytes":
                    main_result[
                        "size_bytes"
                    ],

                "result_copy":
                    relative_path(
                        result_path
                    ),

                "result_copy_exists":
                    copy_result[
                        "exists"
                    ],

                "result_copy_valid_png":
                    copy_result[
                        "valid_png"
                    ],

                "result_copy_size_bytes":
                    copy_result[
                        "size_bytes"
                    ],
            }


            manifest_graphs.append(
                graph_record
            )


            status = (
                "PASS"
                if (
                    main_result[
                        "valid_png"
                    ]
                    and copy_result[
                        "valid_png"
                    ]
                )
                else "FAIL"
            )


            print(
                f"Graph {number} "
                f"{name:24s}: "
                f"{status}"
            )


            print(
                "  Main file :",
                relative_path(
                    graph_path
                )
            )


            print(
                "  Copy file :",
                relative_path(
                    result_path
                )
            )


            if main_result[
                "exists"
            ]:

                print(
                    "  Main size :",
                    f"{main_result['size_bytes'] / 1024.0:.1f} KB"
                )


            if copy_result[
                "exists"
            ]:

                print(
                    "  Copy size :",
                    f"{copy_result['size_bytes'] / 1024.0:.1f} KB"
                )


            print(
                "-" * 72
            )


        all_graphs_valid = (
            graph_failures == 0
        )


        all_copies_valid = (
            copy_failures == 0
        )


        manifest_status = (
            "PASS"
            if (
                all_graphs_valid
                and all_copies_valid
            )
            else "FAIL"
        )


        manifest = {

            "day":
                22,

            "artifact_type":
                "graph_manifest",

            "expected_graph_count":
                6,

            "generated_graph_count":
                sum(
                    1
                    for item
                    in manifest_graphs
                    if item[
                        "graph_valid_png"
                    ]
                ),

            "valid_result_copy_count":
                sum(
                    1
                    for item
                    in manifest_graphs
                    if item[
                        "result_copy_valid_png"
                    ]
                ),

            "all_graphs_valid":
                all_graphs_valid,

            "all_result_copies_valid":
                all_copies_valid,

            "graphs":
                manifest_graphs,

            "status":
                manifest_status,
        }


        with OUTPUT_FILE.open(
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                manifest,
                file,
                indent=2
            )

            file.write(
                "\n"
            )


        print(
            "Valid main graphs           :",
            manifest[
                "generated_graph_count"
            ],
            "/ 6"
        )


        print(
            "Valid result copies         :",
            manifest[
                "valid_result_copy_count"
            ],
            "/ 6"
        )


        print(
            "Manifest output             :",
            relative_path(
                OUTPUT_FILE
            )
        )


        print(
            "DAY 22 MANIFEST STATUS      :",
            manifest_status
        )


        print(
            "=" * 72
        )


        if manifest_status == "PASS":

            print(
                "DAY 22 MANIFEST: PASS"
            )

            return 0


        print(
            "DAY 22 MANIFEST: FAIL"
        )

        return 1


    except (
        FileNotFoundError,
        ValueError,
        KeyError,
        TypeError,
        OSError
    ) as exc:

        print(
            "DAY 22 MANIFEST: FAIL"
        )

        print(
            f"ERROR: {exc}"
        )

        return 1


# ============================================================
# ENTRY
# ============================================================

if __name__ == "__main__":

    sys.exit(
        main()
    )
