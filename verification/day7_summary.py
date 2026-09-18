import json
from pathlib import Path


OBJECTIVE_FILE = Path(
    "results/alu/day7/"
    "verification_objectives.json"
)


SUMMARY_FILE = Path(
    "results/alu/day7/"
    "day7_summary.json"
)


def main():

    if not OBJECTIVE_FILE.exists():

        print(
            "DAY 7 SUMMARY: FAIL"
        )

        raise SystemExit(1)


    data = json.loads(
        OBJECTIVE_FILE.read_text()
    )


    objectives = data.get(
        "objectives",
        []
    )


    high_priority = sum(

        1

        for objective in objectives

        if objective.get(
            "priority"
        ) == "high"
    )


    medium_priority = sum(

        1

        for objective in objectives

        if objective.get(
            "priority"
        ) == "medium"
    )


    summary = {

        "day":
            7,

        "dut":
            "alu",

        "input":
            (
                "results/alu/day6/"
                "alu_knowledge.json"
            ),

        "output":
            str(
                OBJECTIVE_FILE
            ),

        "functional_objectives":
            data.get(
                "functional_objective_count"
            ),

        "corner_case_objectives":
            data.get(
                "corner_case_objective_count"
            ),

        "total_objectives":
            data.get(
                "total_objective_count"
            ),

        "high_priority_objectives":
            high_priority,

        "medium_priority_objectives":
            medium_priority,

        "status":
            "PASS"
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


if __name__ == "__main__":

    main()
