#!/usr/bin/env python3

import json
import sys
from pathlib import Path
from typing import Any, Dict


# ============================================================
# JSON LOADING
# ============================================================

def load_json(path: str) -> Dict[str, Any]:

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
            "Functional coverage report must "
            "contain a JSON object."
        )

    return data


# ============================================================
# HELPER
# ============================================================

def line():
    print("=" * 55)


# ============================================================
# MAIN REPORT
# ============================================================

def main() -> int:

    if len(sys.argv) != 2:

        print(
            "Usage:\n"
            "  python coverage/print_coverage.py "
            "<functional_coverage.json>"
        )

        return 2

    coverage_path = sys.argv[1]

    try:
        data = load_json(
            coverage_path
        )

    except (
        FileNotFoundError,
        json.JSONDecodeError,
        ValueError,
    ) as error:

        print(
            "COVERAGE REPORT: FAIL"
        )

        print(
            f"ERROR: {error}"
        )

        return 1

    # --------------------------------------------------------
    # Read current Day-12 format
    # --------------------------------------------------------

    status = data.get(
        "status",
        "UNKNOWN",
    )

    validated_scenarios = data.get(
        "validated_scenario_count",
        0,
    )

    rtl_branch_count = data.get(
        "rtl_branch_count",
        0,
    )

    functional_operation_count = data.get(
        "functional_operation_count",
        0,
    )

    covered_operation_count = data.get(
        "covered_operation_count",
        0,
    )

    operation_coverage_percent = data.get(
        "operation_coverage_percent",
        0.0,
    )

    objective_count = data.get(
        "objective_count",
        0,
    )

    covered_objective_count = data.get(
        "covered_objective_count",
        0,
    )

    objective_coverage_percent = data.get(
        "objective_coverage_percent",
        0.0,
    )

    operations = data.get(
        "operations",
        {},
    )

    category_coverage = data.get(
        "category_coverage",
        {},
    )

    missing_operations = data.get(
        "missing_operations",
        [],
    ) or []

    missing_objectives = data.get(
        "missing_objectives",
        [],
    ) or []

    # --------------------------------------------------------
    # HEADER
    # --------------------------------------------------------

    print()
    print(
        "DAY 12 FUNCTIONAL COVERAGE REPORT"
    )

    line()

    print(
        f"Status                  : {status}"
    )

    print(
        f"Validated scenarios     : "
        f"{validated_scenarios}"
    )

    print(
        f"RTL branches            : "
        f"{rtl_branch_count}"
    )

    print(
        f"Functional operations   : "
        f"{functional_operation_count}"
    )

    print(
        f"Covered operations      : "
        f"{covered_operation_count}"
    )

    print(
        f"Operation coverage      : "
        f"{operation_coverage_percent}%"
    )

    print(
        f"Verification objectives : "
        f"{objective_count}"
    )

    print(
        f"Covered objectives      : "
        f"{covered_objective_count}"
    )

    print(
        f"Objective coverage      : "
        f"{objective_coverage_percent}%"
    )

    line()

    # --------------------------------------------------------
    # OPERATION COVERAGE
    # --------------------------------------------------------

    print()
    print("OPERATION COVERAGE")
    line()

    if isinstance(
        operations,
        dict,
    ) and operations:

        for operation in sorted(
            operations.keys()
        ):

            info = operations.get(
                operation,
                {},
            )

            covered = bool(
                info.get(
                    "covered",
                    False,
                )
            )

            hits = info.get(
                "hits",
                0,
            )

            state = (
                "COVERED"
                if covered
                else "MISSING"
            )

            print(
                f"{operation:<15} "
                f"{state:<8} "
                f"hits={hits}"
            )

    else:

        print(
            "No operation-detail data found."
        )

    line()

    # --------------------------------------------------------
    # CATEGORY COVERAGE
    # --------------------------------------------------------

    print()
    print("CATEGORY COVERAGE")
    line()

    if isinstance(
        category_coverage,
        dict,
    ) and category_coverage:

        for category in sorted(
            category_coverage.keys()
        ):

            info = category_coverage.get(
                category,
                {},
            )

            print(category)

            print(
                "  total objectives   :",
                info.get(
                    "total_objectives",
                    0,
                ),
            )

            print(
                "  covered objectives :",
                info.get(
                    "covered_objectives",
                    0,
                ),
            )

            print(
                "  scenario hits      :",
                info.get(
                    "scenario_hits",
                    0,
                ),
            )

            print(
                "  coverage           :",
                f"{info.get('coverage_percent', 0.0)}%",
            )

    else:

        print(
            "No category coverage data found."
        )

    line()

    # --------------------------------------------------------
    # MISSING COVERAGE
    # --------------------------------------------------------

    print()
    print("MISSING COVERAGE")
    line()

    if missing_operations:

        print(
            "Missing operations:"
        )

        for operation in missing_operations:

            print(
                " -",
                operation,
            )

    else:

        print(
            "Missing operations : None"
        )

    if missing_objectives:

        print()
        print(
            "Missing objectives:"
        )

        for objective_id in missing_objectives:

            print(
                " -",
                objective_id,
            )

    else:

        print(
            "Missing objectives : None"
        )

    line()

    # --------------------------------------------------------
    # DEFAULT BRANCH INFORMATION
    # --------------------------------------------------------

    default_branches = data.get(
        "default_branches_excluded_from_functional_targets",
        [],
    )

    if default_branches:

        print()
        print(
            "NOTE"
        )

        line()

        print(
            "Defensive default RTL branch is excluded "
            "from functional-operation coverage."
        )

        print(
            "The 3-bit selector already covers all "
            "valid values 000 through 111."
        )

        line()

    # --------------------------------------------------------
    # FINAL RESULT
    # --------------------------------------------------------

    print()

    if (
        str(status).upper() == "PASS"
        and not missing_operations
        and not missing_objectives
    ):

        print(
            "FUNCTIONAL COVERAGE RESULT: PASS"
        )

        print(
            "All executable RTL operations and "
            "verification objectives are covered."
        )

        return 0

    print(
        "FUNCTIONAL COVERAGE RESULT: INCOMPLETE"
    )

    return 1


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    sys.exit(
        main()
    )
