import json
import sys

from pathlib import Path


BASE = Path(
    "results/final/day24"
)


REQUIRED_FILES = [

    BASE / "tool_versions.json",

    BASE / "rtl_sha256.txt",

    BASE / "final_artifact_manifest.json",

    BASE / "final_project_summary.json",

    Path(
        "results/integration/day23/"
        "day23_summary.json"
    )
]


def load_json(path):

    return json.loads(
        path.read_text()
    )


def main():

    errors = []

    for path in REQUIRED_FILES:

        if not path.exists():

            errors.append(
                f"Missing file: {path}"
            )

    if not errors:

        summary = load_json(
            BASE
            / "final_project_summary.json"
        )

        manifest = load_json(
            BASE
            / "final_artifact_manifest.json"
        )

        day23 = load_json(
            Path(
                "results/integration/day23/"
                "day23_summary.json"
            )
        )

        if (
            summary.get("status")
            != "PASS"
        ):

            errors.append(
                "Final summary is not PASS."
            )

        if (
            manifest.get("status")
            != "PASS"
        ):

            errors.append(
                "Artifact manifest is not PASS."
            )

        if (
            day23.get("status")
            != "PASS"
        ):

            errors.append(
                "Day-23 integration is not PASS."
            )

        if (
            summary.get("rtl_frozen")
            is not True
        ):

            errors.append(
                "RTL is not marked frozen."
            )

        if (
            summary.get(
                "results_frozen"
            )
            is not True
        ):

            errors.append(
                "Results are not marked frozen."
            )

        if (
            summary.get(
                "new_tests_generated_day24"
            )
            is not False
        ):

            errors.append(
                "Unexpected Day-24 test generation."
            )

        if (
            summary.get(
                "coverage_remeasured_day24"
            )
            is not False
        ):

            errors.append(
                "Unexpected Day-24 coverage measurement."
            )

    if errors:

        print(
            "DAY 24 FINAL PROJECT VALIDATION: FAIL"
        )

        for error in errors:

            print(
                " -",
                error
            )

        sys.exit(1)

    print(
        "DAY 24 FINAL PROJECT VALIDATION: PASS"
    )

    print(
        "Final required files:",
        len(REQUIRED_FILES)
    )

    print(
        "Project freeze status: VALID"
    )


if __name__ == "__main__":

    main()
