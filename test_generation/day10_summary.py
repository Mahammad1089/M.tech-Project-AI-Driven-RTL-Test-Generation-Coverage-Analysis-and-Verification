import json
from pathlib import Path


REPORT_FILE = Path(
    "results/alu/day10/"
    "validation_report.json"
)


REJECTION_FILE = Path(
    "results/alu/day10/"
    "rejection_report.json"
)


VALIDATED_FILE = Path(
    "results/alu/day10/"
    "validated_tests.json"
)


SUMMARY_FILE = Path(
    "results/alu/day10/"
    "day10_summary.json"
)


def load_json(path):

    if not path.exists():

        raise FileNotFoundError(
            f"Missing file: {path}"
        )

    return json.loads(
        path.read_text()
    )


def main():

    try:

        report = load_json(
            REPORT_FILE
        )

        rejection = load_json(
            REJECTION_FILE
        )

        validated = load_json(
            VALIDATED_FILE
        )

    except (
        FileNotFoundError,
        json.JSONDecodeError
    ) as error:

        print(
            "DAY 10 SUMMARY: FAIL"
        )

        print(
            error
        )

        raise SystemExit(1)

    summary = {

        "day":
            10,

        "dut":
            validated.get(
                "dut"
            ),

        "stage":
            (
                "Deterministic validation "
                "of Hermes-generated "
                "test scenarios"
            ),

        "total_candidates":
            report.get(
                "total_candidates"
            ),

        "validated_count":
            report.get(
                "validated_count"
            ),

        "rejected_count":
            report.get(
                "rejected_count"
            ),

        "all_candidates_valid":
            report.get(
                "all_candidates_valid"
            ),

        "rtl_operation_count":
            report.get(
                "rtl_operation_count"
            ),

        "input_widths":
            report.get(
                "input_widths"
            ),

        "validation_layer":
            "deterministic_python",

        "hermes_used_for_validation":
            False,

        "verilog_generated":
            False,

        "simulation_from_ai_tests":
            False,

        "coverage_measured":
            False,

        "next_stage":
            (
                "DAY_11_AUTOMATIC_"
                "VERILOG_TESTBENCH_"
                "GENERATION"
            ),

        "status":
            report.get(
                "status"
            )
    }

    SUMMARY_FILE.write_text(
        json.dumps(
            summary,
            indent=4
        )
    )

    print(
        json.dumps(
            summary,
            indent=4
        )
    )

    if summary.get(
        "status"
    ) != "PASS":

        raise SystemExit(1)


if __name__ == "__main__":
    main()
