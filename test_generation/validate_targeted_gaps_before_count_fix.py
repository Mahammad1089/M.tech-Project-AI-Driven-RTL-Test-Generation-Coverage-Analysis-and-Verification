#!/usr/bin/env python3

import json
import sys
from pathlib import Path


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
        data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError(
            f"{path} must contain a JSON object."
        )

    return data


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


def get_gap_operations(gap_data):
    value = (
        gap_data.get("missing_operations")
        or gap_data.get("operation_gaps")
        or []
    )

    if not isinstance(value, list):
        return []

    return [
        normalize_text(item)
        for item in value
        if item
    ]


def get_gap_objectives(gap_data):
    value = (
        gap_data.get("missing_objectives")
        or gap_data.get("objective_gaps")
        or []
    )

    if not isinstance(value, list):
        return []

    return [
        str(item)
        for item in value
        if item
    ]


def get_targeted_scenarios(targeted_data):
    value = targeted_data.get(
        "scenarios",
        []
    )

    if not isinstance(value, list):
        return []

    return [
        item
        for item in value
        if isinstance(item, dict)
    ]


def main():
    if len(sys.argv) != 4:
        print(
            "Usage:\n"
            "  python "
            "test_generation/validate_targeted_gaps.py "
            "<coverage_gaps.json> "
            "<targeted_candidate_tests.json> "
            "<target_gap_validation.json>"
        )

        return 2

    gap_path = sys.argv[1]
    targeted_path = sys.argv[2]
    output_path = sys.argv[3]

    try:
        gap_data = load_json(
            gap_path
        )

        targeted_data = load_json(
            targeted_path
        )

    except (
        FileNotFoundError,
        json.JSONDecodeError,
        ValueError,
    ) as error:

        print(
            "TARGET GAP VALIDATION: FAIL"
        )

        print(
            f"ERROR: {error}"
        )

        return 1

    gap_status = normalize_text(
        gap_data.get(
            "status"
        )
    )

    gaps_detected = gap_data.get(
        "gaps_detected"
    )

    missing_operations = get_gap_operations(
        gap_data
    )

    missing_objectives = get_gap_objectives(
        gap_data
    )

    scenarios = get_targeted_scenarios(
        targeted_data
    )

    targeted_mode = normalize_text(
        targeted_data.get(
            "mode"
        )
    )

    generation_status = normalize_text(
        targeted_data.get(
            "generation_status"
        )
    )

    declared_count = targeted_data.get(
        "scenario_count"
    )

    if declared_count is None:
        declared_count = len(
            scenarios
        )

    try:
        declared_count = int(
            declared_count
        )

    except (
        TypeError,
        ValueError,
    ):
        print(
            "TARGET GAP VALIDATION: FAIL"
        )

        print(
            "ERROR: scenario_count is not an integer."
        )

        return 1

    total_gap_count = (
        len(missing_operations)
        + len(missing_objectives)
    )

    no_gap_state = (
        total_gap_count == 0
        and not missing_operations
        and not missing_objectives
        and (
            gap_status
            in (
                "NO_GAPS",
                "PASS",
                "COMPLETE",
            )
            or gaps_detected is False
        )
    )

    errors = []

    # ========================================================
    # NO-GAP PATH
    # ========================================================

    if no_gap_state:

        if scenarios:
            errors.append(
                "Targeted scenarios were generated even "
                "though Day 13 reported no coverage gaps."
            )

        if declared_count != 0:
            errors.append(
                "scenario_count must be 0 when "
                "no coverage gaps exist."
            )

        if targeted_mode not in (
            "",
            "NO_GAPS",
        ):
            errors.append(
                f"Unexpected targeted mode: "
                f"{targeted_mode}"
            )

        if generation_status not in (
            "",
            "NO_TARGETED_GENERATION_REQUIRED",
        ):
            errors.append(
                "Unexpected generation status for "
                "the no-gap path."
            )

        report = {
            "status": (
                "PASS"
                if not errors
                else "FAIL"
            ),

            "mode":
                "NO_GAPS",

            "day13_gap_status":
                gap_status,

            "operation_gap_count":
                0,

            "objective_gap_count":
                0,

            "total_gap_count":
                0,

            "targeted_scenario_count":
                len(scenarios),

            "generation_status":
                generation_status,

            "message":
                (
                    "No targeted scenarios are required "
                    "because Day 13 reported no coverage gaps."
                ),
        }

    # ========================================================
    # TARGETED-GAP PATH
    # ========================================================

    else:

        if not scenarios:
            errors.append(
                "No targeted scenarios found."
            )

        if declared_count != len(
            scenarios
        ):
            errors.append(
                "scenario_count does not match "
                "the number of targeted scenarios."
            )

        valid_operations = set(
            missing_operations
        )

        valid_objectives = set(
            missing_objectives
        )

        covered_operations = set()
        covered_objectives = set()

        for index, scenario in enumerate(
            scenarios,
            start=1,
        ):

            objective_id = scenario.get(
                "objective_id"
            )

            operation = normalize_text(
                scenario.get(
                    "operation"
                )
            )

            if objective_id:
                covered_objectives.add(
                    str(objective_id)
                )

            if operation:
                covered_operations.add(
                    operation
                )

            if (
                valid_objectives
                and objective_id
                and str(objective_id)
                not in valid_objectives
            ):
                errors.append(
                    f"Scenario {index} targets objective "
                    f"{objective_id}, which is not a "
                    f"reported Day-13 gap."
                )

            if (
                valid_operations
                and operation
                and operation
                not in valid_operations
            ):
                errors.append(
                    f"Scenario {index} targets operation "
                    f"{operation}, which is not a "
                    f"reported Day-13 gap."
                )

        missing_targeted_objectives = sorted(
            valid_objectives
            - covered_objectives
        )

        missing_targeted_operations = sorted(
            valid_operations
            - covered_operations
        )

        if missing_targeted_objectives:
            errors.append(
                "Targeted tests do not cover all missing "
                "objectives: "
                + ", ".join(
                    missing_targeted_objectives
                )
            )

        if missing_targeted_operations:
            errors.append(
                "Targeted tests do not cover all missing "
                "operations: "
                + ", ".join(
                    missing_targeted_operations
                )
            )

        report = {
            "status": (
                "PASS"
                if not errors
                else "FAIL"
            ),

            "mode":
                "TARGETED_GENERATION",

            "day13_gap_status":
                gap_status,

            "operation_gap_count":
                len(
                    missing_operations
                ),

            "objective_gap_count":
                len(
                    missing_objectives
                ),

            "total_gap_count":
                total_gap_count,

            "targeted_scenario_count":
                len(
                    scenarios
                ),

            "generation_status":
                generation_status,

            "missing_targeted_operations":
                missing_targeted_operations,

            "missing_targeted_objectives":
                missing_targeted_objectives,
        }

    if errors:
        report[
            "errors"
        ] = errors

    output = Path(
        output_path
    )

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.write_text(
        json.dumps(
            report,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(
        "TARGET GAP VALIDATION"
    )

    print(
        "=" * 50
    )

    print(
        "Day-13 gap status       :",
        gap_status
    )

    print(
        "Operation gaps          :",
        len(
            missing_operations
        )
    )

    print(
        "Objective gaps          :",
        len(
            missing_objectives
        )
    )

    print(
        "Total gaps              :",
        total_gap_count
    )

    print(
        "Targeted scenarios      :",
        len(
            scenarios
        )
    )

    print(
        "Generation status       :",
        generation_status
    )

    print(
        "=" * 50
    )

    if errors:

        print(
            "TARGET GAP VALIDATION: FAIL"
        )

        for error in errors:
            print(
                " -",
                error
            )

        return 1

    print(
        "TARGET GAP VALIDATION: PASS"
    )

    if no_gap_state:
        print(
            "No targeted scenarios are required "
            "because no Day-13 gaps exist."
        )

    else:
        print(
            "Targeted scenarios correctly map "
            "to the Day-13 coverage gaps."
        )

    return 0


if __name__ == "__main__":
    sys.exit(
        main()
    )
