import json
import sys
from pathlib import Path


def load_json(
    file_path
):

    path = Path(
        file_path
    )

    if not path.exists():

        raise FileNotFoundError(
            f"File not found: "
            f"{file_path}"
        )

    return json.loads(
        path.read_text()
    )


def build_prompt(
    knowledge,
    objectives
):

    knowledge_text = json.dumps(
        knowledge,
        indent=2
    )

    objective_text = json.dumps(
        objectives,
        indent=2
    )


    prompt = f"""
You are assisting an RTL verification framework.

The RTL language is Verilog.

Your task for this stage is ONLY to understand
the supplied RTL knowledge and verification
objectives.

Do not generate Verilog code.
Do not generate a testbench.
Do not modify RTL.
Do not run simulation.
Do not invent coverage results.

RTL KNOWLEDGE:
{knowledge_text}

VERIFICATION OBJECTIVES:
{objective_text}

Analyze the supplied information.

Return a concise response containing:

1. DUT name
2. Detected operations
3. Number of functional objectives
4. Number of corner-case objectives
5. The highest-priority verification areas
6. A statement confirming whether the supplied
   objectives are consistent with the RTL
   knowledge.

End your response with exactly:

HERMES RTL ANALYSIS COMPLETE
"""

    return prompt.strip()


def main():

    if len(sys.argv) != 4:

        print(
            "Usage:"
        )

        print(
            "python hermes/"
            "prompt_builder.py "
            "<knowledge_json> "
            "<objectives_json> "
            "<output_prompt>"
        )

        sys.exit(1)


    knowledge_file = (
        sys.argv[1]
    )

    objectives_file = (
        sys.argv[2]
    )

    output_file = (
        sys.argv[3]
    )


    try:

        knowledge = load_json(
            knowledge_file
        )

        objectives = load_json(
            objectives_file
        )

    except (
        FileNotFoundError,
        json.JSONDecodeError
    ) as error:

        print(
            f"ERROR: {error}"
        )

        sys.exit(1)


    prompt = build_prompt(
        knowledge,
        objectives
    )


    output_path = Path(
        output_file
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    output_path.write_text(
        prompt
    )


    print(
        "PROMPT BUILD: PASS"
    )

    print(
        f"Prompt saved to: "
        f"{output_file}"
    )


if __name__ == "__main__":

    main()
