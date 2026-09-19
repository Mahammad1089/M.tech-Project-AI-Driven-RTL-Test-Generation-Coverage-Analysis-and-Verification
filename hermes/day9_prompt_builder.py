import json
import sys
from pathlib import Path


def load_json(file_path):

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    return json.loads(
        path.read_text()
    )


def build_day9_prompt(
    knowledge,
    objectives
):

    knowledge_text = json.dumps(
        knowledge,
        indent=2
    )

    objectives_text = json.dumps(
        objectives,
        indent=2
    )

    prompt = f"""
You are the test-scenario reasoning component
of an AI-assisted RTL verification framework.

RTL language:
Verilog

DUT:
4-bit ALU

Your task is to generate STRUCTURED TEST
SCENARIOS from the supplied RTL knowledge
and verification objectives.

IMPORTANT RULES:

1. Do NOT generate Verilog.
2. Do NOT generate a testbench.
3. Do NOT modify the RTL.
4. Do NOT claim simulation results.
5. Do NOT claim coverage results.
6. Do NOT invent new RTL operations.
7. Use only operations supported by the
   supplied RTL knowledge.
8. Use the supplied verification objective IDs.
9. Each scenario must be traceable to one
   verification objective.
10. Inputs a and b are unsigned 4-bit values,
    therefore each must be between 0 and 15.
11. Do NOT calculate or provide expected_y.
12. Python will calculate expected results later.
13. Return JSON only.
14. Do not use Markdown code fences.
15. Do not add explanatory text before or
    after the JSON.

RTL KNOWLEDGE:

{knowledge_text}

VERIFICATION OBJECTIVES:

{objectives_text}

Generate test scenarios that address the
supplied verification objectives.

For functional objectives, provide representative
normal-operation input combinations.

For corner-case objectives, choose input values
that specifically exercise the stated corner case.

Use exactly this JSON structure:

{{
  "dut": "alu",
  "scenario_count": <number>,
  "scenarios": [
    {{
      "scenario_id": "TEST_001",
      "objective_id": "<objective ID>",
      "category": "functional or corner_case",
      "operation": "<operation>",
      "selector": "<selector value>",
      "inputs": {{
        "a": <integer 0 to 15>,
        "b": <integer 0 to 15>
      }},
      "rationale": "<short reason>"
    }}
  ],
  "generation_status":
    "HERMES TEST SCENARIO GENERATION COMPLETE"
}}

Generate at least one meaningful scenario for
each supplied verification objective.

Scenario IDs must be unique.

Return valid JSON only.
"""

    return prompt.strip()


def main():

    if len(sys.argv) != 4:

        print("Usage:")

        print(
            "python hermes/"
            "day9_prompt_builder.py "
            "<knowledge_json> "
            "<objectives_json> "
            "<output_prompt>"
        )

        sys.exit(1)

    knowledge_file = sys.argv[1]
    objectives_file = sys.argv[2]
    output_file = sys.argv[3]

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

    prompt = build_day9_prompt(
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
        "DAY 9 PROMPT BUILD: PASS"
    )

    print(
        f"Prompt saved to: {output_file}"
    )


if __name__ == "__main__":
    main()
