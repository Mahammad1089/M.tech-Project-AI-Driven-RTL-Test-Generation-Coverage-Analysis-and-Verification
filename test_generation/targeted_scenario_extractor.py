#!/usr/bin/env python3

import json
import sys
from pathlib import Path


TARGETED_MARKER = (
    "HERMES_TARGETED_TEST_GENERATION_COMPLETE"
)

NO_GAP_MARKER = (
    "NO_TARGETED_GENERATION_REQUIRED"
)


# ============================================================
# JSON UTILITIES
# ============================================================

def load_json(path):
    file_path = Path(path)

    if not file_path.exists():
        raise FileNotFoundError(
            f"File not found: {path}"
        )

    with file_path.open(
        "r",
        encoding="utf-8",
    ) as f:
        return json.load(f)


def save_json(path, data):
    file_path = Path(path)

    file_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with file_path.open(
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            data,
            f,
            indent=2,
            ensure_ascii=False,
        )


# ============================================================
# EMBEDDED JSON HANDLING
# ============================================================

def parse_json_string(text):
    """
    Try to parse JSON contained inside a string.

    Supports:
      raw JSON text
      ```json ... ```
      surrounding text containing {...}
    """

    if not isinstance(text, str):
        return None

    cleaned = text.strip()

    if cleaned.startswith("```"):
        lines = cleaned.splitlines()

        if lines:
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        cleaned = "\n".join(lines).strip()

    try:
        value = json.loads(cleaned)

        if isinstance(value, dict):
            return value

    except json.JSONDecodeError:
        pass

    start = cleaned.find("{")
    end = cleaned.rfind("}")

    if (
        start != -1
        and end != -1
        and end > start
    ):
        candidate = cleaned[
            start:end + 1
        ]

        try:
            value = json.loads(
                candidate
            )

            if isinstance(
                value,
                dict,
            ):
                return value

        except json.JSONDecodeError:
            pass

    return None


# ============================================================
# FIND HERMES PAYLOAD
# ============================================================

def find_payload(value):
    """
    Recursively locate the Day-14 response payload.

    Handles direct JSON as well as wrappers returned by
    Hermes interfaces.
    """

    if isinstance(value, dict):

        if (
            "generation_status" in value
            or "generation_type" in value
            or "scenarios" in value
        ):
            return value

        preferred_keys = (
            "result",
            "response",
            "output",
            "final",
            "content",
            "message",
            "text",
            "answer",
        )

        for key in preferred_keys:

            if key not in value:
                continue

            found = find_payload(
                value[key]
            )

            if found is not None:
                return found

        for nested in value.values():

            found = find_payload(
                nested
            )

            if found is not None:
                return found

    elif isinstance(value, list):

        for item in value:

            found = find_payload(
                item
            )

            if found is not None:
                return found

    elif isinstance(value, str):

        parsed = parse_json_string(
            value
        )

        if parsed is not None:
            return find_payload(
                parsed
            )

    return None


# ============================================================
# STATUS NORMALIZATION
# ============================================================

def normalize_status(value):
    if value is None:
        return ""

    return (
        str(value)
        .strip()
        .upper()
        .replace("-", "_")
        .replace(" ", "_")
    )


# ============================================================
# EXTRACT DAY-14 RESULT
# ============================================================

def extract_targeted_result(data):
    payload = find_payload(
        data
    )

    if payload is None:
        raise ValueError(
            "Could not locate Day-14 Hermes "
            "result payload."
        )

    generation_status = normalize_status(
        payload.get(
            "generation_status"
        )
    )

    generation_type = normalize_status(
        payload.get(
            "generation_type"
        )
    )

    scenarios = payload.get(
        "scenarios",
        []
    )

    if scenarios is None:
        scenarios = []

    if not isinstance(
        scenarios,
        list,
    ):
        raise ValueError(
            "'scenarios' must be a list."
        )

    # ========================================================
    # NO-GAP PATH
    # ========================================================

    no_gap_detected = (
        generation_status
        == NO_GAP_MARKER
        or generation_type
        == "NO_GAP_NO_REGENERATION"
    )

    if no_gap_detected:

        if scenarios:
            raise ValueError(
                "NO_TARGETED_GENERATION_REQUIRED "
                "was reported, but scenarios are present."
            )

        return {
            "status":
                "PASS",

            "mode":
                "NO_GAPS",

            "generation_type":
                "no_gap_no_regeneration",

            "generation_status":
                NO_GAP_MARKER,

            "scenario_count":
                0,

            "scenarios":
                [],

            "reason":
                payload.get(
                    "reason",
                    "No verified coverage gaps are present.",
                ),
        }

    # ========================================================
    # TARGETED-GENERATION PATH
    # ========================================================

    if (
        generation_status
        != TARGETED_MARKER
    ):
        raise ValueError(
            "Generation marker missing. "
            "Expected either "
            f"{TARGETED_MARKER} or "
            f"{NO_GAP_MARKER}."
        )

    if not scenarios:
        raise ValueError(
            "Targeted-generation marker was present "
            "but no scenarios were generated."
        )

    declared_count = payload.get(
        "scenario_count"
    )

    if declared_count is not None:

        try:
            declared_count = int(
                declared_count
            )

        except (
            TypeError,
            ValueError,
        ):
            raise ValueError(
                "scenario_count is not an integer."
            )

        if declared_count != len(
            scenarios
        ):
            raise ValueError(
                "scenario_count does not match "
                "the number of scenarios."
            )

    validated_scenarios = []

    for index, scenario in enumerate(
        scenarios,
        start=1,
    ):

        if not isinstance(
            scenario,
            dict,
        ):
            raise ValueError(
                f"Scenario {index} is not "
                "a JSON object."
            )

        required = (
            "scenario_id",
            "objective_id",
            "operation",
            "inputs",
        )

        missing = [
            key
            for key in required
            if key not in scenario
        ]

        if missing:
            raise ValueError(
                f"Scenario {index} is missing: "
                + ", ".join(missing)
            )

        validated_scenarios.append(
            scenario
        )

    return {
        "status":
            "PASS",

        "mode":
            "TARGETED_GENERATION",

        "generation_type":
            payload.get(
                "generation_type",
                "coverage_targeted",
            ),

        "generation_status":
            TARGETED_MARKER,

        "scenario_count":
            len(
                validated_scenarios
            ),

        "scenarios":
            validated_scenarios,
    }


# ============================================================
# MAIN
# ============================================================

def main():
    if len(sys.argv) != 3:

        print(
            "Usage:\n"
            "  python "
            "test_generation/"
            "targeted_scenario_extractor.py "
            "<day14_hermes_result.json> "
            "<targeted_candidate_tests.json>"
        )

        return 2

    input_path = sys.argv[1]
    output_path = sys.argv[2]

    try:

        raw_data = load_json(
            input_path
        )

        result = extract_targeted_result(
            raw_data
        )

        save_json(
            output_path,
            result
        )

    except (
        FileNotFoundError,
        json.JSONDecodeError,
        ValueError,
    ) as error:

        print(
            "TARGETED EXTRACTION: FAIL"
        )

        print(
            f"ERROR: {error}"
        )

        return 1

    print(
        "TARGETED EXTRACTION: PASS"
    )

    print(
        "Mode:",
        result["mode"]
    )

    print(
        "Scenario count:",
        result[
            "scenario_count"
        ]
    )

    print(
        "Generation status:",
        result[
            "generation_status"
        ]
    )

    print(
        "Output:",
        output_path
    )

    if result["mode"] == "NO_GAPS":

        print(
            "No targeted candidate tests "
            "are required."
        )

    return 0


if __name__ == "__main__":
    sys.exit(
        main()
    )
