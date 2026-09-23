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


def check_section(
    section,
    total_key,
    covered_key
):

    total = section.get(
        total_key
    )

    covered = section.get(
        covered_key
    )

    percentage = section.get(
        "coverage_percent"
    )


    if not isinstance(
        total,
        int
    ):

        raise ValueError(
            f"{total_key} is invalid."
        )


    if not isinstance(
        covered,
        int
    ):

        raise ValueError(
            f"{covered_key} is invalid."
        )


    if total <= 0:

        raise ValueError(
            "Coverage denominator "
            "must be positive."
        )


    if (
        covered < 0
        or covered > total
    ):

        raise ValueError(
            "Covered count is invalid."
        )


    expected = round(
        covered
        / total
        * 100,
        2
    )


    if percentage != expected:

        raise ValueError(
            "Coverage percentage mismatch. "
            f"Expected {expected}, "
            f"found {percentage}."
        )


def main():

    if len(sys.argv) != 2:

        print(
            "Usage: python "
            "coverage/"
            "validate_fsm_coverage.py "
            "<coverage_json>"
        )

        sys.exit(1)


    try:

        report = load_json(
            sys.argv[1]
        )


        if report.get(
            "coverage_type"
        ) != (
            "fsm_state_"
            "transition_coverage"
        ):

            raise ValueError(
                "Unexpected coverage type."
            )


        check_section(
            report.get(
                "state_coverage",
                {}
            ),
            "total_states",
            "covered_states"
        )


        check_section(
            report.get(
                "transition_coverage",
                {}
            ),
            "total_transitions",
            "covered_transitions"
        )


        state = report[
            "state_coverage"
        ]

        transition = report[
            "transition_coverage"
        ]


        if (
            state["covered_states"]
            + len(
                state[
                    "missing_states"
                ]
            )
            != state["total_states"]
        ):

            raise ValueError(
                "State accounting mismatch."
            )


        if (
            transition[
                "covered_transitions"
            ]
            + len(
                transition[
                    "missing_transition_ids"
                ]
            )
            != transition[
                "total_transitions"
            ]
        ):

            raise ValueError(
                "Transition accounting mismatch."
            )


        expected_complete = (
            len(
                state[
                    "missing_states"
                ]
            ) == 0
            and
            len(
                transition[
                    "missing_transition_ids"
                ]
            ) == 0
        )


        if (
            report.get(
                "coverage_complete"
            )
            != expected_complete
        ):

            raise ValueError(
                "coverage_complete mismatch."
            )


    except (
        FileNotFoundError,
        json.JSONDecodeError,
        ValueError,
        KeyError
    ) as error:

        print(
            "FSM COVERAGE VALIDATION: FAIL"
        )

        print(
            f"ERROR: {error}"
        )

        sys.exit(1)


    print(
        "FSM COVERAGE VALIDATION: PASS"
    )


if __name__ == "__main__":

    main()
