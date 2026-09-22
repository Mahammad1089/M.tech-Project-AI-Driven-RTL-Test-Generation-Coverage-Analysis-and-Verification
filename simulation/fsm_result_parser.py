import json
import re
import sys
from pathlib import Path


def extract_integer(
    text,
    pattern,
    field_name
):
    match = re.search(
        pattern,
        text
    )

    if not match:
        raise ValueError(
            f"Could not find {field_name}."
        )

    return int(
        match.group(1)
    )


def main():

    if len(sys.argv) != 3:

        print(
            "Usage: python "
            "simulation/fsm_result_parser.py "
            "<simulation_log> "
            "<output_json>"
        )

        sys.exit(1)

    log_path = Path(
        sys.argv[1]
    )

    output_path = Path(
        sys.argv[2]
    )

    try:

        if not log_path.exists():
            raise FileNotFoundError(
                f"Simulation log not found: "
                f"{log_path}"
            )

        text = log_path.read_text()

        total_checks = extract_integer(
            text,
            r"TOTAL CHECKS\s*[:=]\s*(\d+)",
            "TOTAL CHECKS"
        )

        passed_checks = extract_integer(
            text,
            r"PASSED CHECKS\s*[:=]\s*(\d+)",
            "PASSED CHECKS"
        )

        failed_checks = extract_integer(
            text,
            r"FAILED CHECKS\s*[:=]\s*(\d+)",
            "FAILED CHECKS"
        )

        pass_marker = (
            "DAY 16 FSM VERIFICATION PASS"
            in text
        )

        status = (
            "PASS"
            if (
                total_checks > 0
                and passed_checks
                == total_checks
                and failed_checks == 0
                and pass_marker
            )
            else "FAIL"
        )

        report = {
            "dut":
                "fsm_1011",

            "day":
                16,

            "verification_type":
                "deterministic_fsm_baseline",

            "total_checks":
                total_checks,

            "passed_checks":
                passed_checks,

            "failed_checks":
                failed_checks,

            "pass_marker_found":
                pass_marker,

            "status":
                status
        }

    except (
        FileNotFoundError,
        ValueError
    ) as error:

        print(
            "FSM RESULT PARSER: FAIL"
        )

        print(
            f"ERROR: {error}"
        )

        sys.exit(1)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    output_path.write_text(
        json.dumps(
            report,
            indent=4
        )
    )

    print(
        "FSM RESULT PARSER:",
        status
    )

    print(
        "Total checks :",
        total_checks
    )

    print(
        "Passed       :",
        passed_checks
    )

    print(
        "Failed       :",
        failed_checks
    )

    if status != "PASS":
        sys.exit(1)


if __name__ == "__main__":
    main()
