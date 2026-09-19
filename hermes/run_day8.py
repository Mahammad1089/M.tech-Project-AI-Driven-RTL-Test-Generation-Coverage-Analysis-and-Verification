import json
import sys
from pathlib import Path

from prompt_builder import (
    load_json,
    build_prompt
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
    "alu_day8_prompt.txt"
)


RESULT_FILE = Path(
    "results/alu/day8/"
    "day8_hermes_result.json"
)


def main():

    print(
        "================================"
    )

    print(
        "DAY 8 - HERMES INTEGRATION"
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
            f"INPUT LOAD: FAIL"
        )

        print(
            error
        )

        sys.exit(1)


    print(
        "Input load: PASS"
    )


    prompt = build_prompt(
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


    RESULT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )


    RESULT_FILE.write_text(

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
            "DAY 8: FAIL"
        )

        sys.exit(1)


    response = result.get(
        "response_text",
        ""
    )


    marker = (
        "HERMES RTL ANALYSIS COMPLETE"
    )


    if marker not in response:

        print(
            "Response marker: FAIL"
        )

        print(
            "DAY 8: FAIL"
        )

        sys.exit(1)


    print(
        "Response marker: PASS"
    )


    print()

    print(
        "DAY 8 HERMES "
        "INTEGRATION: PASS"
    )


if __name__ == "__main__":

    main()
