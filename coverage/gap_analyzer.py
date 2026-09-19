#!/usr/bin/env python3

import json
import sys
from collections import Counter
from pathlib import Path


# ============================================================
# JSON UTILITIES
# ============================================================

def load_json(path):
    """
    Load a JSON file.
    """

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
    """
    Save a JSON file and create its parent directory.
    """

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
# OPERATION NORMALIZATION
# ============================================================

def normalize_operation(value):
    """
    Normalize operation names.
    """

    if value is None:
        return None

    text = (
        str(value)
        .strip()
        .upper()
        .replace("-", "_")
        .replace(" ", "_")
    )

    aliases = {
        "ADDITION": "ADD",
        "+": "ADD",

        "SUBTRACT": "SUB",
        "SUBTRACTION": "SUB",
        "-": "SUB",

        "&": "AND",
        "|": "OR",
        "^": "XOR",
        "~": "NOT",

        "SHL": "SHIFT_LEFT",
        "LEFT_SHIFT": "SHIFT_LEFT",
        "<<": "SHIFT_LEFT",

        "SHR": "SHIFT_RIGHT",
        "RIGHT_SHIFT": "SHIFT_RIGHT",
        ">>": "SHIFT_RIGHT",
    }

    return aliases.get(
        text,
        text,
    )


# ============================================================
# DAY-6 RTL KNOWLEDGE PARSER
# ============================================================

def extract_rtl_branches(knowledge):
    """
    Extract branches from:

        modules[]
          -> case_logic[]
             -> branches[]
    """

    branches_found = []

    if not isinstance(
        knowledge,
        dict,
    ):
        return branches_found

    modules = knowledge.get(
        "modules",
        [],
    )

    if not isinstance(
        modules,
        list,
    ):
        return branches_found

    for module in modules:

        if not isinstance(
            module,
            dict,
        ):
            continue

        module_name = module.get(
            "module_name"
        )

        case_logic = module.get(
            "case_logic",
            [],
        )

        if not isinstance(
            case_logic,
            list,
        ):
            continue

        for case_block in case_logic:

            if not isinstance(
                case_block,
                dict,
            ):
                continue

            selector = case_block.get(
                "selector"
            )

            branches = case_block.get(
                "branches",
                [],
            )

            if not isinstance(
                branches,
                list,
            ):
                continue

            for branch in branches:

                if not isinstance(
                    branch,
                    dict,
                ):
                    continue

                operation = normalize_operation(
                    branch.get(
                        "operator"
                    )
                )

                if not operation:
                    continue

                branches_found.append(
                    {
                        "module":
                            module_name,

                        "selector":
                            selector,

                        "case_value":
                            branch.get(
                                "case_value"
                            ),

                        "operation":
                            operation,

                        "expression":
                            branch.get(
                                "expression"
                            ),

                        "destination":
                            branch.get(
                                "destination"
                            ),
                    }
                )

    return branches_found


def get_functional_operations(
    rtl_branches,
):
    """
    Return executable ALU operations.

    The defensive default case is excluded because
    the 3-bit selector already defines 000 through 111.
    """

    operations = set()

    for branch in rtl_branches:

        case_value = str(
            branch.get(
                "case_value",
                "",
            )
        ).strip().lower()

        operation = branch.get(
            "operation"
        )

        if not operation:
            continue

        if case_value == "default":
            continue

        operations.add(
            operation
        )

    return operations


# ============================================================
# DAY-7 OBJECTIVE PARSER
# ============================================================

def get_objectives(data):
    """
    Extract objective list from current or compatible formats.
    """

    if isinstance(
        data,
        list,
    ):
        return [
            item
            for item in data
            if isinstance(
                item,
                dict,
            )
        ]

    if not isinstance(
        data,
        dict,
    ):
        return []

    for key in (
        "objectives",
        "verification_objectives",
    ):

        value = data.get(
            key
        )

        if isinstance(
            value,
            list,
        ):
            return [
                item
                for item in value
                if isinstance(
                    item,
                    dict,
                )
            ]

    return []


# ============================================================
# NUMERIC HELPER
# ============================================================

def get_float(
    data,
    key,
    default=0.0,
):
    value = data.get(
        key,
        default,
    )

    try:
        return float(
            value
        )

    except (
        TypeError,
        ValueError,
    ):
        return default


# ============================================================
# GAP ANALYSIS
# ============================================================

def analyze_gaps(
    knowledge,
    objective_data,
    coverage,
):

    if not isinstance(
        coverage,
        dict,
    ):
        raise ValueError(
            "Functional coverage JSON must "
            "contain a JSON object."
        )

    # --------------------------------------------------------
    # RTL OPERATIONS
    # --------------------------------------------------------

    rtl_branches = extract_rtl_branches(
        knowledge
    )

    if not rtl_branches:
        raise ValueError(
            "No RTL operations found."
        )

    rtl_operations = (
        get_functional_operations(
            rtl_branches
        )
    )

    if not rtl_operations:
        raise ValueError(
            "No executable RTL operations found."
        )

    # --------------------------------------------------------
    # VERIFICATION OBJECTIVES
    # --------------------------------------------------------

    objectives = get_objectives(
        objective_data
    )

    if not objectives:
        raise ValueError(
            "No verification objectives found."
        )

    objective_ids = set()
    objective_categories = {}

    for objective in objectives:

        objective_id = objective.get(
            "objective_id"
        )

        if not objective_id:
            continue

        objective_id = str(
            objective_id
        )

        category = str(
            objective.get(
                "category",
                "unknown",
            )
        )

        objective_ids.add(
            objective_id
        )

        objective_categories[
            objective_id
        ] = category

    if not objective_ids:
        raise ValueError(
            "Verification objectives contain "
            "no objective_id values."
        )

    # --------------------------------------------------------
    # DAY-12 OPERATION COVERAGE
    # --------------------------------------------------------

    operations_info = coverage.get(
        "operations",
        {},
    )

    covered_operations = set()

    if isinstance(
        operations_info,
        dict,
    ):

        for operation, info in (
            operations_info.items()
        ):

            if not isinstance(
                info,
                dict,
            ):
                continue

            if info.get(
                "covered",
                False,
            ):

                normalized = normalize_operation(
                    operation
                )

                if normalized:
                    covered_operations.add(
                        normalized
                    )

    # --------------------------------------------------------
    # REPORTED MISSING OPERATIONS
    # --------------------------------------------------------

    reported_missing_operations = (
        coverage.get(
            "missing_operations",
            [],
        )
        or []
    )

    normalized_reported_operations = set()

    for item in reported_missing_operations:

        normalized = normalize_operation(
            item
        )

        if normalized:
            normalized_reported_operations.add(
                normalized
            )

    # --------------------------------------------------------
    # IMPORTANT CORRUPTION CHECK:
    # unknown operation names must cause FAIL
    # --------------------------------------------------------

    unknown_missing_operations = sorted(
        normalized_reported_operations
        - rtl_operations
    )

    if unknown_missing_operations:
        raise ValueError(
            "Coverage contains unknown missing operations:\n"
            + "\n".join(
                unknown_missing_operations
            )
        )

    # Derive gaps independently as well.
    derived_missing_operations = (
        rtl_operations
        - covered_operations
    )

    missing_operations = set(
        normalized_reported_operations
    )

    missing_operations.update(
        derived_missing_operations
    )

    # --------------------------------------------------------
    # REPORTED MISSING OBJECTIVES
    # --------------------------------------------------------

    reported_missing_objectives = (
        coverage.get(
            "missing_objectives",
            [],
        )
        or []
    )

    reported_missing_objectives = [
        str(item)
        for item in (
            reported_missing_objectives
        )
    ]

    # --------------------------------------------------------
    # IMPORTANT NEGATIVE-TEST CHECK:
    # unknown objective IDs must cause FAIL
    # --------------------------------------------------------

    unknown_missing_objectives = sorted(
        {
            objective_id
            for objective_id
            in reported_missing_objectives
            if objective_id
            not in objective_ids
        }
    )

    if unknown_missing_objectives:
        raise ValueError(
            "Coverage contains unknown missing objectives:\n"
            + "\n".join(
                unknown_missing_objectives
            )
        )

    missing_objectives = set(
        reported_missing_objectives
    )

    # --------------------------------------------------------
    # CROSS-CHECK OBJECTIVE COUNTS
    # --------------------------------------------------------

    reported_objective_count = coverage.get(
        "objective_count"
    )

    reported_covered_objectives = coverage.get(
        "covered_objective_count"
    )

    if reported_objective_count is not None:

        try:
            reported_objective_count = int(
                reported_objective_count
            )

        except (
            TypeError,
            ValueError,
        ):
            raise ValueError(
                "objective_count is not a valid integer."
            )

        if (
            reported_objective_count
            != len(objective_ids)
        ):
            raise ValueError(
                "Coverage objective_count does not match "
                "the Day-7 verification objective count."
            )

    if reported_covered_objectives is not None:

        try:
            reported_covered_objectives = int(
                reported_covered_objectives
            )

        except (
            TypeError,
            ValueError,
        ):
            raise ValueError(
                "covered_objective_count is not "
                "a valid integer."
            )

        expected_covered = (
            len(objective_ids)
            - len(
                missing_objectives
            )
        )

        if (
            reported_covered_objectives
            != expected_covered
        ):
            raise ValueError(
                "covered_objective_count is inconsistent "
                "with missing_objectives."
            )

    # --------------------------------------------------------
    # CATEGORY GAP COUNTS
    # --------------------------------------------------------

    missing_by_category = Counter()

    for objective_id in (
        missing_objectives
    ):

        category = (
            objective_categories.get(
                objective_id,
                "unknown",
            )
        )

        missing_by_category[
            category
        ] += 1

    # --------------------------------------------------------
    # COVERAGE VALUES
    # --------------------------------------------------------

    operation_coverage = get_float(
        coverage,
        "operation_coverage_percent",
        0.0,
    )

    objective_coverage = get_float(
        coverage,
        "objective_coverage_percent",
        0.0,
    )

    validated_scenarios = coverage.get(
        "validated_scenario_count",
        0,
    )

    try:
        validated_scenarios = int(
            validated_scenarios
        )

    except (
        TypeError,
        ValueError,
    ):
        validated_scenarios = 0

    # --------------------------------------------------------
    # GAP STATUS
    # --------------------------------------------------------

    gaps_detected = bool(
        missing_operations
        or missing_objectives
    )

    if gaps_detected:
        status = "GAPS_FOUND"
    else:
        status = "NO_GAPS"

    # --------------------------------------------------------
    # FINAL REPORT
    # --------------------------------------------------------

    report = {
        "status":
            status,

        "gaps_detected":
            gaps_detected,

        "validated_scenarios":
            validated_scenarios,

        "rtl_branch_count":
            len(
                rtl_branches
            ),

        "functional_operation_count":
            len(
                rtl_operations
            ),

        "covered_operation_count":
            len(
                rtl_operations
                - missing_operations
            ),

        "operation_coverage_percent":
            operation_coverage,

        "objective_count":
            len(
                objective_ids
            ),

        "covered_objective_count":
            len(
                objective_ids
                - missing_objectives
            ),

        "objective_coverage_percent":
            objective_coverage,

        "missing_operations":
            sorted(
                missing_operations
            ),

        "missing_objectives":
            sorted(
                missing_objectives
            ),

        "missing_objectives_by_category":
            dict(
                sorted(
                    missing_by_category.items()
                )
            ),

        "functional_operations":
            sorted(
                rtl_operations
            ),

        "coverage_source":
            (
                "Day-12 functional coverage generated "
                "from validated Day-10 scenarios "
                "executed in Day 11."
            ),

        "recommendation":
            (
                "No additional targeted tests are required."
                if not gaps_detected
                else
                "Generate targeted tests for the reported "
                "missing operations and verification objectives."
            ),
    }

    return report


# ============================================================
# TERMINAL REPORT
# ============================================================

def print_report(report):

    print(
        "COVERAGE GAP ANALYSIS"
    )

    print(
        "=" * 50
    )

    print(
        "Validated scenarios :",
        report[
            "validated_scenarios"
        ],
    )

    print(
        "RTL branches        :",
        report[
            "rtl_branch_count"
        ],
    )

    print(
        "Functional ops      :",
        report[
            "functional_operation_count"
        ],
    )

    print(
        "Covered ops         :",
        report[
            "covered_operation_count"
        ],
    )

    print(
        "Operation coverage  :",
        f"{report['operation_coverage_percent']}%",
    )

    print(
        "Objectives          :",
        report[
            "objective_count"
        ],
    )

    print(
        "Covered objectives  :",
        report[
            "covered_objective_count"
        ],
    )

    print(
        "Objective coverage  :",
        f"{report['objective_coverage_percent']}%",
    )

    print(
        "Missing operations  :",
        report[
            "missing_operations"
        ],
    )

    print(
        "Missing objectives  :",
        report[
            "missing_objectives"
        ],
    )

    print(
        "=" * 50
    )

    if report[
        "gaps_detected"
    ]:

        print(
            "COVERAGE GAP ANALYSIS: GAPS FOUND"
        )

    else:

        print(
            "COVERAGE GAP ANALYSIS: PASS"
        )

        print(
            "No functional coverage gaps detected."
        )


# ============================================================
# MAIN
# ============================================================

def main():

    if len(sys.argv) != 5:

        print(
            "Usage:\n"
            "  python coverage/gap_analyzer.py "
            "<rtl_knowledge.json> "
            "<verification_objectives.json> "
            "<functional_coverage.json> "
            "<coverage_gaps.json>"
        )

        return 2

    try:

        knowledge = load_json(
            sys.argv[1]
        )

        objective_data = load_json(
            sys.argv[2]
        )

        coverage = load_json(
            sys.argv[3]
        )

        report = analyze_gaps(
            knowledge,
            objective_data,
            coverage,
        )

        save_json(
            sys.argv[4],
            report,
        )

        print_report(
            report
        )

        # A legitimate coverage gap is analysis data,
        # so the analyzer itself still completed successfully.
        return 0

    except (
        FileNotFoundError,
        json.JSONDecodeError,
        ValueError,
    ) as error:

        print(
            "COVERAGE GAP ANALYSIS: FAIL"
        )

        print(
            f"ERROR: {error}"
        )

        # Important for the Day-13 negative test.
        return 1

    except Exception as error:

        print(
            "COVERAGE GAP ANALYSIS: FAIL"
        )

        print(
            f"UNEXPECTED ERROR: {error}"
        )

        return 1


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    sys.exit(
        main()
    )
