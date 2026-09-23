import json
import sys
from pathlib import Path


def load_json(path):

    file_path = Path(path)

    if not file_path.exists():

        raise FileNotFoundError(
            f"File not found: {path}"
        )

    return json.loads(
        file_path.read_text()
    )


def get_percentage(
    report,
    section
):

    value = report.get(
        section,
        {}
    ).get(
        "coverage_percent"
    )


    if not isinstance(
        value,
        (int, float)
    ):

        raise ValueError(
            f"Missing percentage: {section}"
        )


    return float(
        value
    )


def main():

    if len(sys.argv) != 4:

        print(
            "Usage: python "
            "coverage/"
            "compare_fsm_coverage.py "
            "<before_json> "
            "<after_json> "
            "<output_json>"
        )

        sys.exit(1)


    try:

        before = load_json(
            sys.argv[1]
        )

        after = load_json(
            sys.argv[2]
        )


        before_state = (
            get_percentage(
                before,
                "state_coverage"
            )
        )

        after_state = (
            get_percentage(
                after,
                "state_coverage"
            )
        )


        before_transition = (
            get_percentage(
                before,
                "transition_coverage"
            )
        )

        after_transition = (
            get_percentage(
                after,
                "transition_coverage"
            )
        )


        state_delta = round(
            after_state
            - before_state,
            2
        )


        transition_delta = round(
            after_transition
            - before_transition,
            2
        )


        if (
            state_delta < 0
            or transition_delta < 0
        ):

            trend = "REGRESSION"

        elif (
            state_delta > 0
            or transition_delta > 0
        ):

            trend = "IMPROVED"

        else:

            trend = "UNCHANGED"


        report = {

            "before": {

                "state_coverage":
                    before_state,

                "transition_coverage":
                    before_transition
            },


            "after": {

                "state_coverage":
                    after_state,

                "transition_coverage":
                    after_transition
            },


            "delta": {

                "state_coverage":
                    state_delta,

                "transition_coverage":
                    transition_delta
            },


            "trend":
                trend
        }


    except (
        FileNotFoundError,
        json.JSONDecodeError,
        ValueError
    ) as error:

        print(
            "FSM COVERAGE COMPARISON: FAIL"
        )

        print(
            f"ERROR: {error}"
        )

        sys.exit(1)


    output = Path(
        sys.argv[3]
    )

    output.write_text(
        json.dumps(
            report,
            indent=4
        )
    )


    print(
        "FSM COVERAGE COMPARISON: PASS"
    )

    print(
        "State:",
        before_state,
        "->",
        after_state
    )

    print(
        "Transition:",
        before_transition,
        "->",
        after_transition
    )

    print(
        "Trend:",
        trend
    )


if __name__ == "__main__":

    main()
