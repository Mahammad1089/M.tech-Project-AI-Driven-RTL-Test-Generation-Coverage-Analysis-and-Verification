import subprocess
import sys


STEPS = [

    (
        "Build graph dataset",
        [
            sys.executable,
            "graphs/day22_data_builder.py",
        ],
    ),

    (
        "Export graph CSV files",
        [
            sys.executable,
            "graphs/day22_csv_export.py",
        ],
    ),

    (
        "Generate strategy coverage graph",
        [
            sys.executable,
            "graphs/"
            "day22_graph1_strategy_coverage.py",
        ],
    ),

    (
        "Generate random seed coverage graph",
        [
            sys.executable,
            "graphs/"
            "day22_graph2_seed_coverage.py",
        ],
    ),

    (
        "Generate coverage distribution graph",
        [
            sys.executable,
            "graphs/"
            "day22_graph3_coverage_distribution.py",
        ],
    ),

    (
        "Generate verification effort graph",
        [
            sys.executable,
            "graphs/"
            "day22_graph4_verification_effort.py",
        ],
    ),

    (
        "Generate random redundancy graph",
        [
            sys.executable,
            "graphs/"
            "day22_graph5_random_redundancy.py",
        ],
    ),

    (
        "Generate random coverage range graph",
        [
            sys.executable,
            "graphs/"
            "day22_graph6_random_range.py",
        ],
    ),

    (
        "Validate generated graphs",
        [
            sys.executable,
            "graphs/validate_day22_graphs.py",
        ],
    ),

    (
        "Generate graph manifest",
        [
            sys.executable,
            "graphs/day22_manifest.py",
        ],
    ),
]


def main():

    for (
        description,
        command
    ) in STEPS:

        print()
        print("=" * 72)

        print(
            description
        )

        print("=" * 72)

        result = subprocess.run(
            command
        )

        if (
            result.returncode
            != 0
        ):

            print()
            print(
                "DAY 22 VISUALIZATION "
                "PIPELINE: FAIL"
            )

            print(
                "Failed stage:",
                description
            )

            sys.exit(
                result.returncode
            )

    print()
    print("=" * 72)

    print(
        "DAY 22 VISUALIZATION PIPELINE: PASS"
    )

    print("=" * 72)


if __name__ == "__main__":

    main()
