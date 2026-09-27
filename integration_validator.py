import json
import sys

from pathlib import Path


CONFIG_FILE = Path(
    "config/day23_integration.json"
)

OUTPUT_FILE = Path(
    "results/integration/day23/"
    "structure_validation.json"
)


REQUIRED_FILES = [

    # Main RTL
    "rtl/alu.v",
    "rtl/fsm_1011.v",
    "rtl/fifo.v",

    # Parsing / knowledge
    "parser/rtl_parser.py",
    "parser/rtl_analyzer.py",

    # Hermes layer
    "hermes/hermes_interface.py",

    # Simulation infrastructure
    "simulation/core/simulator.py",
    "simulation/core/result_parser.py",
    "simulation/core/report_generator.py",

    # Coverage
    "coverage/functional_coverage.py",
    "coverage/fifo_coverage.py",
    "coverage/fifo_gap_analyzer.py",

    # Baseline experiments
    "baseline/validate_day20_comparison.py",
    "baseline/validate_day21_experiments.py",

    # Day 22
    "graphs/validate_day22_graphs.py",
    "graphs/day22_summary.py",
]


def main():

    missing_files = []

    try:

        if not CONFIG_FILE.exists():

            raise FileNotFoundError(
                CONFIG_FILE
            )

        config = json.loads(
            CONFIG_FILE.read_text()
        )

        for filename in REQUIRED_FILES:

            path = Path(
                filename
            )

            if not path.exists():

                missing_files.append(
                    filename
                )

        report = {

            "day": 23,

            "check":
                "project_structure",

            "required_file_count":
                len(REQUIRED_FILES),

            "existing_file_count":
                len(REQUIRED_FILES)
                - len(missing_files),

            "missing_files":
                missing_files,

            "rtl_files": [
                "rtl/alu.v",
                "rtl/fsm_1011.v",
                "rtl/fifo.v"
            ],

            "rtl_modification_permitted":
                config[
                    "boundaries"
                ][
                    "modify_rtl"
                ],

            "status":
                "PASS"
                if not missing_files
                else "FAIL"
        }

        OUTPUT_FILE.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        OUTPUT_FILE.write_text(
            json.dumps(
                report,
                indent=4
            )
        )

        if missing_files:

            print(
                "DAY 23 STRUCTURE VALIDATION: FAIL"
            )

            print(
                "Missing files:"
            )

            for filename in missing_files:

                print(
                    " -",
                    filename
                )

            sys.exit(1)

    except Exception as error:

        print(
            "DAY 23 STRUCTURE VALIDATION: FAIL"
        )

        print(
            "ERROR:",
            error
        )

        sys.exit(1)

    print(
        "DAY 23 STRUCTURE VALIDATION: PASS"
    )

    print(
        "Required files:",
        len(REQUIRED_FILES)
    )

    print(
        "Missing files: 0"
    )


if __name__ == "__main__":

    main()
