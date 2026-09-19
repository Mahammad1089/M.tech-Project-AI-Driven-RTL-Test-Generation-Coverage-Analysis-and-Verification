#!/usr/bin/env python3

import csv
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
            "Coverage report must be a JSON object."
        )

    return data


def main():

    if len(sys.argv) != 3:
        print(
            "Usage:\n"
            "  python coverage/coverage_to_csv.py "
            "<functional_coverage.json> "
            "<output.csv>"
        )
        return 2

    input_path = sys.argv[1]
    output_path = sys.argv[2]

    try:
        data = load_json(
            input_path
        )

    except (
        FileNotFoundError,
        json.JSONDecodeError,
        ValueError,
    ) as error:
        print(
            "COVERAGE CSV EXPORT: FAIL"
        )
        print(
            f"ERROR: {error}"
        )
        return 1

    operations = data.get(
        "operations",
        {}
    )

    categories = data.get(
        "category_coverage",
        {}
    )

    output_file = Path(
        output_path
    )

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fieldnames = [
        "record_type",
        "name",
        "covered",
        "hits",
        "total_objectives",
        "covered_objectives",
        "scenario_hits",
        "coverage_percent",
        "value",
    ]

    with output_file.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as csvfile:

        writer = csv.DictWriter(
            csvfile,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        # ====================================================
        # OVERALL SUMMARY
        # ====================================================

        summary_items = [
            (
                "status",
                data.get("status")
            ),
            (
                "validated_scenarios",
                data.get(
                    "validated_scenario_count"
                )
            ),
            (
                "rtl_branches",
                data.get(
                    "rtl_branch_count"
                )
            ),
            (
                "functional_operations",
                data.get(
                    "functional_operation_count"
                )
            ),
            (
                "covered_operations",
                data.get(
                    "covered_operation_count"
                )
            ),
            (
                "operation_coverage_percent",
                data.get(
                    "operation_coverage_percent"
                )
            ),
            (
                "objective_count",
                data.get(
                    "objective_count"
                )
            ),
            (
                "covered_objectives",
                data.get(
                    "covered_objective_count"
                )
            ),
            (
                "objective_coverage_percent",
                data.get(
                    "objective_coverage_percent"
                )
            ),
        ]

        for name, value in summary_items:
            writer.writerow(
                {
                    "record_type": "summary",
                    "name": name,
                    "value": value,
                }
            )

        # ====================================================
        # OPERATION COVERAGE
        # ====================================================

        if isinstance(
            operations,
            dict,
        ):

            for operation in sorted(
                operations.keys()
            ):

                info = operations.get(
                    operation,
                    {}
                )

                writer.writerow(
                    {
                        "record_type":
                            "operation",

                        "name":
                            operation,

                        "covered":
                            info.get(
                                "covered",
                                False,
                            ),

                        "hits":
                            info.get(
                                "hits",
                                0,
                            ),
                    }
                )

        # ====================================================
        # CATEGORY COVERAGE
        # ====================================================

        if isinstance(
            categories,
            dict,
        ):

            for category in sorted(
                categories.keys()
            ):

                info = categories.get(
                    category,
                    {}
                )

                writer.writerow(
                    {
                        "record_type":
                            "category",

                        "name":
                            category,

                        "total_objectives":
                            info.get(
                                "total_objectives",
                                0,
                            ),

                        "covered_objectives":
                            info.get(
                                "covered_objectives",
                                0,
                            ),

                        "scenario_hits":
                            info.get(
                                "scenario_hits",
                                0,
                            ),

                        "coverage_percent":
                            info.get(
                                "coverage_percent",
                                0.0,
                            ),
                    }
                )

        # ====================================================
        # MISSING COVERAGE
        # ====================================================

        for operation in data.get(
            "missing_operations",
            []
        ) or []:

            writer.writerow(
                {
                    "record_type":
                        "missing_operation",

                    "name":
                        operation,
                }
            )

        for objective in data.get(
            "missing_objectives",
            []
        ) or []:

            writer.writerow(
                {
                    "record_type":
                        "missing_objective",

                    "name":
                        objective,
                }
            )

    print(
        "COVERAGE CSV EXPORT: PASS"
    )

    print(
        "Input :",
        input_path
    )

    print(
        "Output:",
        output_path
    )

    print(
        "Operations exported:",
        len(operations)
        if isinstance(
            operations,
            dict,
        )
        else 0
    )

    print(
        "Categories exported:",
        len(categories)
        if isinstance(
            categories,
            dict,
        )
        else 0
    )

    return 0


if __name__ == "__main__":
    sys.exit(
        main()
    )
