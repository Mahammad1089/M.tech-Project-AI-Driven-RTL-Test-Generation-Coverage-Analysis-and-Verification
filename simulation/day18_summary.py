import json
import re
import sys
from pathlib import Path


RESULT_DIR = Path(
    "results/fifo/day18"
)

LOG_FILE = (
    RESULT_DIR
    / "fifo_day18.log"
)

KNOWLEDGE_FILE = (
    RESULT_DIR
    / "fifo_knowledge.json"
)

SUMMARY_FILE = (
    RESULT_DIR
    / "day18_summary.json"
)


def extract_count(
    text,
    label
):

    pattern = (
        rf"{re.escape(label)}"
        rf"\s*=\s*(\d+)"
    )

    match = re.search(
        pattern,
        text
    )

    if not match:

        raise ValueError(
            f"Could not find {label}"
        )

    return int(
        match.group(1)
    )


def main():

    try:

        if not LOG_FILE.exists():

            raise FileNotFoundError(
                f"Missing file: {LOG_FILE}"
            )


        if not KNOWLEDGE_FILE.exists():

            raise FileNotFoundError(
                f"Missing file: "
                f"{KNOWLEDGE_FILE}"
            )


        log_text = (
            LOG_FILE.read_text()
        )

        knowledge = json.loads(
            KNOWLEDGE_FILE.read_text()
        )


        total_checks = extract_count(
            log_text,
            "TOTAL CHECKS"
        )

        passed_checks = extract_count(
            log_text,
            "PASSED CHECKS"
        )

        failed_checks = extract_count(
            log_text,
            "FAILED CHECKS"
        )


        if total_checks <= 0:

            raise ValueError(
                "No FIFO checks were executed."
            )


        if failed_checks != 0:

            raise ValueError(
                "FIFO has failed checks."
            )


        if (
            passed_checks
            != total_checks
        ):

            raise ValueError(
                "Pass-count mismatch."
            )


        if (
            "DAY 18 FIFO VERIFICATION PASS"
            not in log_text
        ):

            raise ValueError(
                "FIFO PASS marker missing."
            )


        if (
            knowledge.get(
                "knowledge_status"
            )
            !=
            "FIFO KNOWLEDGE MODEL COMPLETE"
        ):

            raise ValueError(
                "FIFO knowledge is incomplete."
            )


        summary = {

            "day": 18,

            "dut": "fifo",

            "stage":
                "FIFO RTL development "
                "and baseline verification",

            "fifo_type":
                "synchronous_fifo",

            "data_width": 8,

            "depth": 4,

            "total_checks":
                total_checks,

            "passed_checks":
                passed_checks,

            "failed_checks":
                failed_checks,

            "reset_verified": True,

            "single_write_verified": True,

            "single_read_verified": True,

            "fifo_ordering_verified": True,

            "empty_condition_verified": True,

            "full_condition_verified": True,

            "write_when_full_verified": True,

            "read_when_empty_verified": True,

            "simultaneous_write_read_verified":
                True,

            "fifo_knowledge_generated": True,

            "fifo_knowledge_validated": True,

            "hermes_used": False,

            "functional_coverage_measured":
                False,

            "fifo_gap_analysis_performed":
                False,

            "coverage_closure_performed":
                False,

            "rtl_modified_from_day18_baseline":
                False,

            "next_stage":
                "DAY_19_FIFO_COVERAGE_CLOSURE",

            "status": "PASS"
        }


    except (
        FileNotFoundError,
        json.JSONDecodeError,
        ValueError
    ) as error:

        print(
            "DAY 18 SUMMARY: FAIL"
        )

        print(
            "ERROR:",
            error
        )

        sys.exit(1)


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

    print()

    print(
        "DAY 18 SUMMARY: PASS"
    )


if __name__ == "__main__":
    main()
