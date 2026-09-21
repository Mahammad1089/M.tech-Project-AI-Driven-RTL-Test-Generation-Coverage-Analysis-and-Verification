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
        return json.load(f)


def save_json(path, data):
    file_path = Path(path)

    file_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with file_path.open(
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            data,
            f,
            indent=2
        )


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


def extract_test_list(data):
    """
    Extract tests from supported project formats.
    """

    if isinstance(data, list):
        return data

    if not isinstance(data, dict):
        raise ValueError(
            "Test input must contain a JSON object or list."
        )

    for key in (
        "validated_tests",
        "scenarios",
        "tests",
        "test_cases",
        "targeted_tests",
    ):
        value = data.get(key)

        if isinstance(value, list):
            return value

    raise ValueError(
        "No valid test list found."
    )


def valid_no_gap_artifact(data):
    """
    Empty targeted tests are legitimate ONLY when the
    file explicitly proves this is the verified NO_GAPS path.
    """

    if not isinstance(data, dict):
        return False

    status = normalize(
        data.get("status")
    )

    mode = normalize(
        data.get("mode")
    )

    generation_status = normalize(
        data.get(
            "generation_status"
        )
    )

    count = data.get(
        "validated_test_count"
    )

    if count is None:
        count = data.get(
            "scenario_count"
        )

    if count is not None:
        try:
            count = int(count)
        except (
            TypeError,
            ValueError,
        ):
            return False

        if count != 0:
            return False

    return (
        status in (
            "PASS",
            "COMPLETE",
        )
        and mode == "NO_GAPS"
        and generation_status
        == "NO_TARGETED_GENERATION_REQUIRED"
    )


def identity(test, fallback_index):
    if not isinstance(test, dict):
        return (
            "RAW",
            fallback_index,
            repr(test),
        )

    scenario_id = test.get(
        "scenario_id"
    )

    if scenario_id:
        return (
            "SCENARIO_ID",
            str(scenario_id),
        )

    objective_id = test.get(
        "objective_id"
    )

    operation = test.get(
        "operation"
    )

    selector = test.get(
        "selector"
    )

    inputs = test.get(
        "inputs",
        {}
    )

    inputs_key = json.dumps(
        inputs,
        sort_keys=True
    )

    return (
        "CONTENT",
        str(objective_id),
        str(operation),
        str(selector),
        inputs_key,
    )


def main():

    if len(sys.argv) != 4:
        print(
            "Usage:\n"
            "  python test_generation/merge_test_sets.py "
            "<initial_tests.json> "
            "<targeted_tests.json> "
            "<combined_tests.json>"
        )
        return 2

    initial_path = sys.argv[1]
    targeted_path = sys.argv[2]
    output_path = sys.argv[3]

    try:
        initial_data = load_json(
            initial_path
        )

        targeted_data = load_json(
            targeted_path
        )

        initial_tests = extract_test_list(
            initial_data
        )

        targeted_tests = extract_test_list(
            targeted_data
        )

        # ----------------------------------------------------
        # Initial tests must never be empty.
        # ----------------------------------------------------

        if not initial_tests:
            raise ValueError(
                "Initial validated test set is empty."
            )

        # ----------------------------------------------------
        # Empty targeted set is permitted ONLY for a
        # verified NO_GAPS artifact.
        # ----------------------------------------------------

        if not targeted_tests:

            if not valid_no_gap_artifact(
                targeted_data
            ):
                raise ValueError(
                    "Targeted test set is empty and does not "
                    "contain valid NO_GAPS metadata."
                )

        # ----------------------------------------------------
        # Merge
        # ----------------------------------------------------

        combined = []
        seen = set()

        initial_added = 0
        targeted_added = 0
        duplicates_removed = 0

        # Initial tests
        for index, test in enumerate(
            initial_tests,
            start=1
        ):

            if not isinstance(
                test,
                dict
            ):
                raise ValueError(
                    f"Initial test {index} is not "
                    "a JSON object."
                )

            test_identity = identity(
                test,
                index
            )

            if test_identity in seen:
                duplicates_removed += 1
                continue

            seen.add(
                test_identity
            )

            combined.append(
                test
            )

            initial_added += 1

        # Targeted tests
        offset = len(
            initial_tests
        )

        for index, test in enumerate(
            targeted_tests,
            start=1
        ):

            if not isinstance(
                test,
                dict
            ):
                raise ValueError(
                    f"Targeted test {index} is not "
                    "a JSON object."
                )

            test_identity = identity(
                test,
                offset + index
            )

            if test_identity in seen:
                duplicates_removed += 1
                continue

            seen.add(
                test_identity
            )

            combined.append(
                test
            )

            targeted_added += 1

        # ----------------------------------------------------
        # Output
        # ----------------------------------------------------

        report = {
            "status":
                "PASS",

            "merge_mode":
                (
                    "BASE_ONLY_NO_GAPS"
                    if len(targeted_tests) == 0
                    else "BASE_PLUS_TARGETED"
                ),

            "initial_input_tests":
                len(initial_tests),

            "targeted_input_tests":
                len(targeted_tests),

            "initial_added":
                initial_added,

            "targeted_added":
                targeted_added,

            "duplicates_removed":
                duplicates_removed,

            "combined_tests":
                len(combined),

            # Compatibility fields for later scripts
            "base_validated_count":
                len(initial_tests),

            "targeted_validated_count":
                len(targeted_tests),

            "combined_validated_count":
                len(combined),

            "validated_tests":
                combined,

            "scenarios":
                combined,
        }

        save_json(
            output_path,
            report
        )

    except (
        FileNotFoundError,
        json.JSONDecodeError,
        ValueError,
    ) as error:

        print(
            "TEST SET MERGE: FAIL"
        )

        print(
            f"ERROR: {error}"
        )

        return 1

    # --------------------------------------------------------
    # Exact Step-12 output format
    # --------------------------------------------------------

    print(
        "TEST SET MERGE: PASS"
    )

    print()

    print(
        "Initial input tests :",
        len(initial_tests)
    )

    print(
        "Targeted input tests:",
        len(targeted_tests)
    )

    print(
        "Initial added       :",
        initial_added
    )

    print(
        "Targeted added      :",
        targeted_added
    )

    print(
        "Duplicates removed  :",
        duplicates_removed
    )

    print(
        "Combined tests      :",
        len(combined)
    )

    return 0


if __name__ == "__main__":
    sys.exit(
        main()
    )
