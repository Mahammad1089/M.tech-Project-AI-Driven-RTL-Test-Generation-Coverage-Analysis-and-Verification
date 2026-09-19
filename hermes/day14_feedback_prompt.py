#!/usr/bin/env python3

import json
import sys
from pathlib import Path


# ============================================================
# JSON LOADER
# ============================================================

def load_json(path):
    file_path = Path(path)

    if not file_path.exists():
        raise FileNotFoundError(
            f"File not found: {path}"
        )

    with file_path.open(
        "r",
        encoding="utf-8"
    ) as f:
        return json.load(f)


# ============================================================
# GAP STATUS HELPERS
# ============================================================

def normalize_text(value):
    if value is None:
        return ""

    return (
        str(value)
        .strip()
        .upper()
        .replace("-", "_")
        .replace(" ", "_")
    )


def get_gap_status(data):
    """
    Read Day-13 status from several compatible field names.
    """

    if not isinstance(data, dict):
        return ""

    for key in (
        "gap_status",
        "status",
        "coverage_gap_status",
        "analysis_status",
    ):
        value = data.get(key)

        if value is not None:
            return normalize_text(value)

    return ""


def get_operation_gaps(data):
    """
    Read operation gaps from old/current formats.
    """

    if not isinstance(data, dict):
        return []

    for key in (
        "operation_gaps",
        "missing_operations",
    ):
        value = data.get(key)

        if isinstance(value, list):
            return value

    return []


def get_objective_gaps(data):
    """
    Read objective gaps from old/current formats.
    """

    if not isinstance(data, dict):
        return []

    for key in (
        "objective_gaps",
        "missing_objectives",
    ):
        value = data.get(key)

        if isinstance(value, list):
            return value

    return []


def get_gap_count(data):
    """
    Determine total gap count using explicit counts
    where available, otherwise derive from lists.
    """

    if not isinstance(data, dict):
        return 0

    for key in (
        "total_gap_count",
        "gap_count",
    ):
        value = data.get(key)

        if value is not None:
            try:
                return int(value)
            except (TypeError, ValueError):
                pass

    return (
        len(get_operation_gaps(data))
        + len(get_objective_gaps(data))
    )


def is_no_gap_state(data):
    """
    Robustly determine whether Day 13 reported no gaps.
    """

    status = get_gap_status(data)

    operation_gaps = get_operation_gaps(data)
    objective_gaps = get_objective_gaps(data)

    total_gap_count = get_gap_count(data)

    gaps_detected = data.get(
        "gaps_detected"
    ) if isinstance(data, dict) else None

    no_gap_statuses = {
        "NO_GAPS",
        "NO_GAP",
        "NO_GAPS_FOUND",
        "NO_GAP_FOUND",
        "NO_GAPS_DETECTED",
        "PASS",
        "COMPLETE",
        "COMPLETED",
    }

    # Strongest indication:
    # explicit no-gap status.
    if status in no_gap_statuses:
        if (
            not operation_gaps
            and not objective_gaps
            and total_gap_count == 0
        ):
            return True

    # Current Day-13 format may explicitly say false.
    if gaps_detected is False:
        if (
            not operation_gaps
            and not objective_gaps
            and total_gap_count == 0
        ):
            return True

    # Even if status was omitted, an explicitly zero-gap
    # input is valid for the no-regeneration path.
    if (
        not operation_gaps
        and not objective_gaps
        and total_gap_count == 0
    ):
        return True

    return False


def is_gap_state(data):
    """
    Determine whether targeted regeneration is required.
    """

    status = get_gap_status(data)

    operation_gaps = get_operation_gaps(data)
    objective_gaps = get_objective_gaps(data)

    total_gap_count = get_gap_count(data)

    gap_statuses = {
        "GAPS_FOUND",
        "GAP_FOUND",
        "INCOMPLETE",
        "GAPS_DETECTED",
    }

    if status in gap_statuses:
        return (
            total_gap_count > 0
            or bool(operation_gaps)
            or bool(objective_gaps)
        )

    return (
        bool(operation_gaps)
        or bool(objective_gaps)
        or total_gap_count > 0
    )


# ============================================================
# DUT HELPER
# ============================================================

def get_dut(data):
    if not isinstance(data, dict):
        return "alu"

    return (
        data.get("dut")
        or data.get("module")
        or data.get("design")
        or "alu"
    )


# ============================================================
# NO-GAP PROMPT
# ============================================================

def build_no_gap_prompt(feedback_data):
    dut = get_dut(
        feedback_data
    )

    return f"""
You are the AI reasoning layer in an M.Tech RTL verification framework.

DUT: {dut}

DAY-13 COVERAGE GAP STATUS:
NO_GAPS

The verified Day-13 coverage analysis found no missing
functional operations and no missing verification objectives.

IMPORTANT RULES:

1. Return JSON only.
2. Do not use Markdown fences.
3. Do not invent coverage gaps.
4. Do not generate unnecessary tests.
5. Do not modify RTL.
6. Do not claim new simulation was executed.
7. Do not claim coverage improved.

RETURN EXACTLY THIS JSON STRUCTURE:

{{
  "dut": "{dut}",
  "generation_type": "no_gap_no_regeneration",
  "source_stage": "DAY_13_COVERAGE_GAPS",
  "scenario_count": 0,
  "scenarios": [],
  "reason": "No verified coverage gaps are present.",
  "generation_status": "NO_TARGETED_GENERATION_REQUIRED"
}}
""".strip()


# ============================================================
# TARGETED-GAP PROMPT
# ============================================================

def build_gap_prompt(
    feedback_data,
    knowledge,
    objectives,
):
    operation_gaps = get_operation_gaps(
        feedback_data
    )

    objective_gaps = get_objective_gaps(
        feedback_data
    )

    if (
        not operation_gaps
        and not objective_gaps
    ):
        raise ValueError(
            "Gap generation was requested, but no "
            "verified gap entries are present."
        )

    dut = get_dut(
        feedback_data
    )

    return f"""
You are the AI reasoning layer in an M.Tech RTL verification framework.

DUT:
{dut}

Your task is to generate targeted test scenarios ONLY for
the verified coverage gaps supplied below.

IMPORTANT RULES:

1. Return JSON only.
2. Do not use Markdown fences.
3. Do not write Verilog.
4. Do not write a testbench.
5. Do not modify RTL.
6. Do not claim simulation was executed.
7. Do not claim coverage improved.
8. Do not invent coverage gaps.
9. Use only supplied RTL operations.
10. Target only supplied missing objectives.
11. Use supplied objective IDs exactly.
12. Each test must map to one missing objective.
13. a and b must be unsigned 4-bit integers from 0 through 15.
14. Do not calculate expected_y.
15. Python will calculate expected_y later.
16. Generate the minimum meaningful number of scenarios.
17. Scenario IDs must be unique.
18. Do not repeat identical stimulus unless required.

VERIFIED COVERAGE GAPS:

{json.dumps(feedback_data, indent=2)}

RTL KNOWLEDGE:

{json.dumps(knowledge, indent=2)}

VERIFICATION OBJECTIVES:

{json.dumps(objectives, indent=2)}

RETURN JSON IN THIS STRUCTURE:

{{
  "dut": "{dut}",
  "generation_type": "coverage_targeted",
  "source_stage": "DAY_13_COVERAGE_GAPS",
  "scenario_count": 1,
  "scenarios": [
    {{
      "scenario_id": "TARGET_001",
      "objective_id": "OBJ_ALU_XXX",
      "category": "corner_case",
      "operation": "ADD",
      "selector": "3'b000",
      "inputs": {{
        "a": 0,
        "b": 0
      }},
      "targeted_gap": "OBJ_ALU_XXX",
      "rationale": "Explain why this stimulus targets the verified gap."
    }}
  ],
  "generation_status": "HERMES_TARGETED_TEST_GENERATION_COMPLETE"
}}
""".strip()


# ============================================================
# MAIN
# ============================================================

def main():
    if len(sys.argv) != 5:
        print(
            "Usage:\n"
            "  python hermes/day14_feedback_prompt.py "
            "<feedback_json> "
            "<knowledge_json> "
            "<objectives_json> "
            "<output_prompt>"
        )
        return 2

    try:
        feedback = load_json(
            sys.argv[1]
        )

        knowledge = load_json(
            sys.argv[2]
        )

        objectives = load_json(
            sys.argv[3]
        )

        gap_status = get_gap_status(
            feedback
        )

        operation_gaps = get_operation_gaps(
            feedback
        )

        objective_gaps = get_objective_gaps(
            feedback
        )

        total_gap_count = get_gap_count(
            feedback
        )

        print(
            "Detected Day-13 status:",
            gap_status or "<not explicitly stored>"
        )

        print(
            "Detected operation gaps:",
            len(operation_gaps)
        )

        print(
            "Detected objective gaps:",
            len(objective_gaps)
        )

        print(
            "Detected total gaps:",
            total_gap_count
        )

        if is_no_gap_state(
            feedback
        ):
            prompt = build_no_gap_prompt(
                feedback
            )

            mode = "NO_GAPS"

        elif is_gap_state(
            feedback
        ):
            prompt = build_gap_prompt(
                feedback,
                knowledge,
                objectives,
            )

            mode = "TARGETED_GENERATION"

        else:
            raise ValueError(
                "Unable to determine Day-13 gap state "
                "from feedback input."
            )

    except (
        FileNotFoundError,
        json.JSONDecodeError,
        ValueError,
    ) as error:
        print(
            "DAY 14 PROMPT BUILD: FAIL"
        )

        print(
            f"ERROR: {error}"
        )

        return 1

    output = Path(
        sys.argv[4]
    )

    output.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    output.write_text(
        prompt,
        encoding="utf-8"
    )

    print()
    print(
        "DAY 14 PROMPT BUILD: PASS"
    )

    print(
        "Mode:",
        mode
    )

    print(
        "Prompt:",
        output
    )

    if mode == "NO_GAPS":
        print(
            "No targeted regeneration is required."
        )

    return 0


if __name__ == "__main__":
    sys.exit(
        main()
    )
