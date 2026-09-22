import json
from pathlib import Path


BASE = Path(
    "results/fsm/day16"
)

SIM_REPORT = (
    BASE
    / "fsm_baseline_report.json"
)

KNOWLEDGE = (
    BASE
    / "fsm_knowledge.json"
)

SUMMARY = (
    BASE
    / "day16_summary.json"
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

        simulation = load_json(
            SIM_REPORT
        )

        knowledge = load_json(
            KNOWLEDGE
        )

        states = knowledge.get(
            "states",
            []
        )

        transitions = knowledge.get(
            "transitions",
            []
        )

        if simulation.get(
            "status"
        ) != "PASS":

            raise ValueError(
                "FSM simulation did not pass."
            )

        if simulation.get(
            "failed_checks"
        ) != 0:

            raise ValueError(
                "FSM has failed checks."
            )

        if len(states) != 4:

            raise ValueError(
                "Unexpected state count."
            )

        if len(transitions) != 8:

            raise ValueError(
                "Unexpected transition count."
            )

        if knowledge.get(
            "coverage_measured"
        ) is not False:

            raise ValueError(
                "Day 16 must not claim "
                "coverage measurement."
            )

        summary = {

            "day":
                16,

            "dut":
                "fsm_1011",

            "stage":
                "FSM benchmark integration "
                "and baseline verification",

            "design_type":
                "sequential_fsm",

            "sequence":
                "1011",

            "overlap_enabled":
                True,

            "state_count":
                len(states),

            "legal_transition_count":
                len(transitions),

            "total_checks":
                simulation.get(
                    "total_checks"
                ),

            "passed_checks":
                simulation.get(
                    "passed_checks"
                ),

            "failed_checks":
                simulation.get(
                    "failed_checks"
                ),

            "baseline_simulation":
                "PASS",

            "fsm_knowledge_generated":
                True,

            "fsm_knowledge_validated":
                True,

            "hermes_used":
                False,

            "ai_tests_generated":
                False,

            "state_coverage_measured":
                False,

            "transition_coverage_measured":
                False,

            "coverage_closure_performed":
                False,

            "next_stage":
                "DAY_17_FSM_STATE_"
                "TRANSITION_COVERAGE",

            "status":
                "PASS"
        }

    except (
        FileNotFoundError,
        json.JSONDecodeError,
        ValueError
    ) as error:

        print(
            "DAY 16 SUMMARY: FAIL"
        )

        print(
            f"ERROR: {error}"
        )

        raise SystemExit(1)

    SUMMARY.write_text(
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
        "DAY 16 SUMMARY: PASS"
    )


if __name__ == "__main__":
    main()
