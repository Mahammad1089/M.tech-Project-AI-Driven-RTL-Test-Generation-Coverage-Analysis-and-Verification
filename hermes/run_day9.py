import json
import sys
from pathlib import Path

from day9_prompt_builder import (
    load_json,
    build_day9_prompt
)

from hermes_interface import (
    run_hermes
)


KNOWLEDGE_FILE = Path(
    "results/alu/day6/"
    "alu_knowledge.json"
)


OBJECTIVES_FILE = Path(
    "results/alu/day7/"
    "verification_objectives.json"
)


PROMPT_FILE = Path(
    "hermes/prompts/"
    "alu_day9_prompt.txt"
)


INTERFACE_RESULT = Path(
    "results/alu/day9/"
    "day9_hermes_result.json"
)


CANDIDATE_FILE = Path(
    "results/alu/day9/"
    "candidate_tests.json"
)


def clean_response_text(
    response_text
):

    text = response_text.strip()

    if text.startswith(
        "```json"
    ):

        text = text[
            len("```json"):
        ]

    elif text.startswith(
        "```"
    ):

        text = text[3:]

    if text.endswith(
        "```"
    ):

        text = text[:-3]

    return text.strip()


def main():

    print(
        "================================"
    )

    print(
        "DAY 9 - HERMES TEST "
        "SCENARIO GENERATION"
    )

    print(
        "================================"
    )

    print()

    try:

        knowledge = load_json(
            KNOWLEDGE_FILE
        )

        objectives = load_json(
            OBJECTIVES_FILE
        )

    except Exception as error:

        print(
            "Input load: FAIL"
        )

        print(
            error
        )

        sys.exit(1)

    print(
        "Input load: PASS"
    )

    prompt = build_day9_prompt(
        knowledge,
        objectives
    )

    PROMPT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    PROMPT_FILE.write_text(
        prompt
    )

    print(
        "Prompt build: PASS"
    )

    result = run_hermes(
        PROMPT_FILE
    )

    INTERFACE_RESULT.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    INTERFACE_RESULT.write_text(
        json.dumps(
            result,
            indent=4
        )
    )

    print(
        "Hermes status:",
        result.get(
            "status"
        )
    )

    if result.get(
        "status"
    ) != "PASS":

        print(
            "DAY 9: FAIL"
        )

        sys.exit(1)

    response_text = result.get(
        "response_text",
        ""
    )

    cleaned_text = clean_response_text(
        response_text
    )

    try:

        candidate_data = json.loads(
            cleaned_text
        )

    except json.JSONDecodeError as error:

        print(
            "Scenario JSON parse: FAIL"
        )

        print(
            error
        )

        sys.exit(1)

    print(
        "Scenario JSON parse: PASS"
    )

    CANDIDATE_FILE.write_text(
        json.dumps(
            candidate_data,
            indent=4
        )
    )

    print(
        "Candidate scenario save: PASS"
    )

    print(
        "Scenario count:",
        len(
            candidate_data.get(
                "scenarios",
                []
            )
        )
    )

    print()

    print(
        "DAY 9 HERMES TEST "
        "GENERATION: PASS"
    )


if __name__ == "__main__":
    main()
