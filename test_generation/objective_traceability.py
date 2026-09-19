#!/usr/bin/env python3

import json
import sys
from pathlib import Path


# ============================================================
# JSON LOADING
# ============================================================

def load_json(path):
    """
    Load a JSON file safely.
    """

    file_path = Path(path)

    if not file_path.exists():
        raise FileNotFoundError(
            f"File not found: {path}"
        )

    return json.loads(
        file_path.read_text(
            encoding="utf-8"
        )
    )


# ============================================================
# OBJECTIVE FILE HANDLING
# ============================================================

def get_objectives(data):
    """
    Extract the objective list from verification_objectives.json.

    Supported structures:

        [...]
        {"objectives": [...]}
        {"verification_objectives": [...]}
    """

    if isinstance(data, list):
        return data

    if isinstance(data, dict):

        for key in (
            "objectives",
            "verification_objectives",
        ):

            value = data.get(key)

            if isinstance(value, list):
                return value

    return []


def get_defined_objective_ids(objective_data):
    """
    Collect all objective IDs defined in Day 7.
    """

    objectives = get_objectives(
        objective_data
    )

    objective_ids = set()

    for item in objectives:

        if not isinstance(item, dict):
            continue

        objective_id = item.get(
            "objective_id"
        )

        if objective_id:
            objective_ids.add(
                str(objective_id)
            )

    return objective_ids


# ============================================================
# RECURSIVE OBJECTIVE-ID EXTRACTION
# ============================================================

def collect_objective_ids(value):
    """
    Recursively search a dictionary/list for:

        objective_id
        objective_ids

    This makes the traceability checker compatible with
    different Day-9 / Day-10 JSON layouts.
    """

    found = set()

    if isinstance(value, dict):

        # Singular objective ID
        objective_id = value.get(
            "objective_id"
        )

        if objective_id:

            if isinstance(
                objective_id,
                (str, int)
            ):
                found.add(
                    str(objective_id)
                )

        # Multiple objective IDs
        objective_ids = value.get(
            "objective_ids"
        )

        if isinstance(
            objective_ids,
            list
        ):

            for item in objective_ids:

                if item:
                    found.add(
                        str(item)
                    )

        elif objective_ids:

            found.add(
                str(objective_ids)
            )

        # Search nested structures
        for nested_value in value.values():

            if isinstance(
                nested_value,
                (dict, list)
            ):

                found.update(
                    collect_objective_ids(
                        nested_value
                    )
                )

    elif isinstance(value, list):

        for item in value:

            found.update(
                collect_objective_ids(
                    item
                )
            )

    return found


# ============================================================
# VALIDATED TEST HANDLING
# ============================================================

def get_validated_tests(test_data):
    """
    Return validated tests from the Day-10 output.

    Supported keys:

        validated_tests
        scenarios
        tests
        test_cases
    """

    if isinstance(test_data, list):
        return test_data

    if not isinstance(
        test_data,
        dict
    ):
        return []

    preferred_keys = (
        "validated_tests",
        "scenarios",
        "tests",
        "test_cases",
    )

    for key in preferred_keys:

        value = test_data.get(key)

        if isinstance(value, list):
            return value

    return []


# ============================================================
# MAIN TRACEABILITY CHECK
# ============================================================

def main():

    if len(sys.argv) != 3:

        print(
            "Usage:\n"
            "  python "
            "test_generation/"
            "objective_traceability.py "
            "<objectives_json> "
            "<validated_tests_json>"
        )

        return 2

    objective_path = sys.argv[1]
    validated_path = sys.argv[2]

    try:

        objective_data = load_json(
            objective_path
        )

        test_data = load_json(
            validated_path
        )

    except (
        FileNotFoundError,
        json.JSONDecodeError,
    ) as error:

        print(
            "OBJECTIVE TRACEABILITY: FAIL"
        )

        print(error)

        return 1

    # --------------------------------------------------------
    # Day-7 objective IDs
    # --------------------------------------------------------

    objective_ids = (
        get_defined_objective_ids(
            objective_data
        )
    )

    # --------------------------------------------------------
    # Day-10 validated tests
    # --------------------------------------------------------

    validated_tests = (
        get_validated_tests(
            test_data
        )
    )

    # Search all validated tests recursively.
    exercised_ids = (
        collect_objective_ids(
            validated_tests
        )
    )

    # Only count IDs that actually belong to Day-7 objectives.
    covered = (
        objective_ids
        & exercised_ids
    )

    missing = (
        objective_ids
        - exercised_ids
    )

    unknown = (
        exercised_ids
        - objective_ids
    )

    # --------------------------------------------------------
    # Terminal report
    # --------------------------------------------------------

    print(
        "Total objectives      :",
        len(objective_ids)
    )

    print(
        "Validated scenarios   :",
        len(validated_tests)
    )

    print(
        "Objectives exercised  :",
        len(covered)
    )

    print(
        "Objectives missing    :",
        len(missing)
    )

    if missing:

        print()
        print(
            "Missing objective IDs:"
        )

        for objective_id in sorted(
            missing
        ):

            print(
                " -",
                objective_id
            )

    if unknown:

        print()
        print(
            "Warning: validated tests contain "
            "unknown objective IDs:"
        )

        for objective_id in sorted(
            unknown
        ):

            print(
                " -",
                objective_id
            )

    print()

    if not missing:

        print(
            "OBJECTIVE TRACEABILITY: PASS"
        )

        return 0

    print(
        "OBJECTIVE TRACEABILITY: "
        "INCOMPLETE"
    )

    return 1


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    sys.exit(
        main()
    )
