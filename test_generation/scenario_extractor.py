import json
import sys
from pathlib import Path


def load_interface_result(
    file_path
):

    path = Path(file_path)

    if not path.exists():

        raise FileNotFoundError(
            f"Interface result not found: "
            f"{file_path}"
        )

    return json.loads(
        path.read_text()
    )


def clean_response_text(
    response_text
):

    text = response_text.strip()

    if text.startswith("```json"):
        text = text[len("```json"):]

    elif text.startswith("```"):
        text = text[3:]

    if text.endswith("```"):
        text = text[:-3]

    return text.strip()


def extract_scenarios(
    interface_result
):

    if interface_result.get(
        "status"
    ) != "PASS":

        raise ValueError(
            "Hermes interface status "
            "is not PASS."
        )

    response_text = (
        interface_result.get(
            "response_text",
            ""
        )
    )

    if not response_text.strip():

        raise ValueError(
            "Hermes response_text "
            "is empty."
        )

    cleaned_text = clean_response_text(
        response_text
    )

    try:

        scenario_data = json.loads(
            cleaned_text
        )

    except json.JSONDecodeError as error:

        raise ValueError(
            "Hermes response is not "
            f"valid scenario JSON: {error}"
        )

    return scenario_data


def main():

    if len(sys.argv) != 3:

        print("Usage:")

        print(
            "python test_generation/"
            "scenario_extractor.py "
            "<interface_result_json> "
            "<candidate_tests_json>"
        )

        sys.exit(1)

    interface_file = sys.argv[1]
    output_file = sys.argv[2]

    try:

        interface_result = (
            load_interface_result(
                interface_file
            )
        )

        scenarios = extract_scenarios(
            interface_result
        )

    except (
        FileNotFoundError,
        json.JSONDecodeError,
        ValueError
    ) as error:

        print(
            "SCENARIO EXTRACTION: FAIL"
        )

        print(
            f"ERROR: {error}"
        )

        sys.exit(1)

    output_path = Path(
        output_file
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    output_path.write_text(
        json.dumps(
            scenarios,
            indent=4
        )
    )

    print(
        "SCENARIO EXTRACTION: PASS"
    )

    print(
        f"Saved to: {output_file}"
    )


if __name__ == "__main__":
    main()
