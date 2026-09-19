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
        encoding="utf-8"
    ) as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError(
            f"{path} must contain a JSON object."
        )

    return data


def normalize(value):
    if value is None:
        return ""

    return (
        str(value)
        .strip()
        .upper()
        .replace("-", "_")
        .replace(" ", "_")
    )


def get_list(data, *keys):
    for key in keys:
        value = data.get(key)

        if isinstance(value, list):
            return value

    return []


def main():
    if len(sys.argv) != 4:
        print(
            "Usage:\n"
            "  python "
            "test_generation/validate_targeted_gaps.py "
            "<coverage_gaps.json> "
            "<targeted_tests.json> "
            "<validation_report.json>"
        )
        return 2

    gap_path = sys.argv[1]
    targeted_path = sys.argv[2]
    output_path = sys.argv[3]

    try:
        gaps = load_json(
            gap_path
        )

        targeted = load_json(
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

    # ========================================================
    # DAY-13 DATA
    # ========================================================

    gap_status = normalize(
        gaps.get("status")
    )

    gaps_detected = gaps.get(
        "gaps_detected"
    )

    operation_gaps = get_list(
        gaps,
        "missing_operations",
        "operation_gaps",
    )

    objective_gaps = get_list(
        gaps,
        "missing_objectives",
        "objective_gaps",
    )

    operation_gap_count = len(
        operation_gaps
    )

    objective_gap_count = len(
        objective_gaps
    )

    total_gap_count = (
        operation_gap_count
        + objective_gap_count
    )

    # ========================================================
    # TARGETED TEST DATA
    # ========================================================

    scenarios = get_list(
        targeted,
        "scenarios",
        "targeted_tests",
        "tests",
    )

    scenario_count = len(
        scenarios
    )

    declared_count = targeted.get(
        "scenario_count"
    )

    if declared_count is None:
        declared_count = scenario_count

    try:
        declared_count = int(
            declared_count
        )

    except (
        TypeError,
        ValueError,
    ):
        declared_count = -1

    mode = normalize(
        targeted.get("mode")
    )

    generation_status = normalize(
        targeted.get(
            "generation_status"
        )
    )

    # ========================================================
    # DETERMINE DAY-13 STATE
    # ========================================================

    no_gap_state = (
        total_gap_count == 0
        and (
            gap_status in (
                "NO_GAPS",
                "PASS",
                "COMPLETE",
            )
            or gaps_detected is False
        )
    )

    gaps_found_state = (
        total_gap_count > 0
        or gap_status in (
            "GAPS_FOUND",
            "INCOMPLETE",
        )
        or gaps_detected is True
    )

    errors = []

    passed_tests = 0
    failed_tests = 0

    # ========================================================
    # NO-GAPS PATH
    # ========================================================

    if no_gap_state:

        if scenario_count == 0:

            # Correct normal NO_GAPS execution.
            passed_tests = 0
            failed_tests = 0

        else:

            # Any targeted scenario is invalid because
            # Day 13 explicitly reported no gaps.
            passed_tests = 0
            failed_tests = scenario_count

            errors.append(
                "Targeted scenarios were generated even "
                "though Day 13 reported no coverage gaps."
            )

        if declared_count != scenario_count:
            errors.append(
                "scenario_count does not match the "
                "number of scenarios."
            )

        if declared_count != 0:
            errors.append(
                "scenario_count must be 0 when "
                "no coverage gaps exist."
            )

        if mode not in (
            "",
            "NO_GAPS",
        ):
            errors.append(
                f"Unexpected targeted mode: {mode}"
            )

        if generation_status not in (
            "",
            "NO_TARGETED_GENERATION_REQUIRED",
        ):
            errors.append(
                "Unexpected generation status "
                "for the no-gap path."
            )

        validation_mode = "NO_GAPS"

    # ========================================================
    # GAPS-FOUND PATH
    # ========================================================

    elif gaps_found_state:

        validation_mode = "TARGETED_GENERATION"

        valid_objectives = {
            str(item)
            for item in objective_gaps
        }

        valid_operations = {
            normalize(item)
            for item in operation_gaps
        }

        for index, scenario in enumerate(
            scenarios,
            start=1,
        ):

            scenario_errors = []

            if not isinstance(
                scenario,
                dict,
            ):
                scenario_errors.append(
                    "Scenario is not a JSON object."
                )

            else:
                objective_id = scenario.get(
                    "objective_id"
                )

                operation = normalize(
                    scenario.get(
                        "operation"
                    )
                )

                targeted_gap = scenario.get(
                    "targeted_gap"
                )

                if (
                    valid_objectives
                    and str(objective_id)
                    not in valid_objectives
                ):
                    scenario_errors.append(
                        f"Objective {objective_id} is not "
                        "a reported Day-13 objective gap."
                    )

                if (
                    valid_operations
                    and operation
                    not in valid_operations
                ):
                    scenario_errors.append(
                        f"Operation {operation} is not "
                        "a reported Day-13 operation gap."
                    )

                if (
                    valid_objectives
                    and targeted_gap is not None
                    and str(targeted_gap)
                    not in valid_objectives
                ):
                    scenario_errors.append(
                        f"targeted_gap {targeted_gap} is not "
                        "a reported Day-13 gap."
                    )

            if scenario_errors:
                failed_tests += 1

                for error in scenario_errors:
                    errors.append(
                        f"Scenario {index}: {error}"
                    )

            else:
                passed_tests += 1

        if scenario_count == 0:
            errors.append(
                "No targeted scenarios found."
            )

        if declared_count != scenario_count:
            errors.append(
                "scenario_count does not match the "
                "number of scenarios."
            )

    else:

        validation_mode = "UNKNOWN"

        errors.append(
            "Unable to determine Day-13 gap state."
        )

        failed_tests = scenario_count

    # ========================================================
    # FINAL STATUS
    # ========================================================

    status = (
        "PASS"
        if not errors
        else "FAIL"
    )

    report = {
        "status":
            status,

        "mode":
            validation_mode,

        "day13_gap_status":
            gap_status,

        "operation_gap_count":
            operation_gap_count,

        "objective_gap_count":
            objective_gap_count,

        "total_gap_count":
            total_gap_count,

        "targeted_scenario_count":
            scenario_count,

        "passed_tests":
            passed_tests,

        "failed_tests":
            failed_tests,

        "generation_status":
            generation_status,
    }

    if errors:
        report["errors"] = errors

    # ========================================================
    # SAVE REPORT
    # ========================================================

    output = Path(
        output_path
    )

    output.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with output.open(
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            report,
            f,
            indent=2
        )

    # ========================================================
    # TERMINAL OUTPUT
    # ========================================================

    print(
        "TARGET GAP VALIDATION"
    )

    print(
        "=" * 52
    )

    print(
        "Day-13 gap status       :",
        gap_status
    )

    print(
        "Operation gaps          :",
        operation_gap_count
    )

    print(
        "Objective gaps          :",
        objective_gap_count
    )

    print(
        "Total gaps              :",
        total_gap_count
    )

    print(
        "Targeted scenarios      :",
        scenario_count
    )

    print(
        "Passed tests            :",
        passed_tests
    )

    print(
        "Failed tests            :",
        failed_tests
    )

    print(
        "Generation status       :",
        generation_status
    )

    print(
        "=" * 52
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
            "All targeted scenarios correctly map "
            "to verified Day-13 coverage gaps."
        )

    return 0


if __name__ == "__main__":
    sys.exit(
        main()
    )
