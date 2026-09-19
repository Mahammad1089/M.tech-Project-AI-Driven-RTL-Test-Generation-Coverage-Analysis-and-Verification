import json
import sys
from pathlib import Path


def main():
    if len(sys.argv) != 3:
        print(
            "Usage: python "
            "coverage/prepare_feedback_input.py "
            "<coverage_gaps_json> "
            "<feedback_input_json>"
        )

        sys.exit(1)

    source = Path(
        sys.argv[1]
    )

    output = Path(
        sys.argv[2]
    )

    if not source.exists():
        print(
            "FEEDBACK INPUT: FAIL"
        )

        print(
            "Gap report does not exist."
        )

        sys.exit(1)

    try:
        gaps = json.loads(
            source.read_text()
        )

    except json.JSONDecodeError:
        print(
            "FEEDBACK INPUT: FAIL"
        )

        print(
            "Gap report is invalid JSON."
        )

        sys.exit(1)

    feedback_input = {
        "dut":
            gaps.get("dut"),

        "source_stage":
            "DAY_13_COVERAGE_GAP_ANALYSIS",

        "gap_status":
            gaps.get("gap_status"),

        "operation_gaps":
            gaps.get(
                "operation_gaps",
                []
            ),

        "objective_gaps":
            gaps.get(
                "objective_gaps",
                []
            ),

        "category_summary":
            gaps.get(
                "category_summary",
                {}
            ),

        "instruction":
            (
                "Use only these verified "
                "coverage gaps for targeted "
                "test reasoning."
            ),

        "hermes_execution":
            "PENDING_DAY_14"
    }

    output.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    output.write_text(
        json.dumps(
            feedback_input,
            indent=4
        )
    )

    print(
        "FEEDBACK INPUT: PASS"
    )

    print(
        "Saved:",
        output
    )


if __name__ == "__main__":
    main()
