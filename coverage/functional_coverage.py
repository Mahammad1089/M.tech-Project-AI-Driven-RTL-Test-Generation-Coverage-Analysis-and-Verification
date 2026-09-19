#!/usr/bin/env python3

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


# ============================================================
# JSON UTILITIES
# ============================================================

def load_json(file_path: str) -> Any:
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as f:
        return json.load(f)


def save_json(
    file_path: str,
    data: Any,
) -> None:
    path = Path(file_path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
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
# BASIC HELPERS
# ============================================================

def percentage(
    covered: int,
    total: int,
) -> float:
    if total == 0:
        return 0.0

    return round(
        (covered / total) * 100.0,
        2,
    )


def normalize_operation(
    value: Any,
) -> Optional[str]:
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
# DAY-6 RTL KNOWLEDGE
# ============================================================

def extract_rtl_operations(
    knowledge: Any,
) -> List[Dict[str, Any]]:
    """
    Read RTL operations from the real Day-6 structure:

        modules[]
          -> case_logic[]
             -> branches[]
    """

    operations: List[Dict[str, Any]] = []

    if not isinstance(
        knowledge,
        dict,
    ):
        return operations

    modules = knowledge.get(
        "modules",
        [],
    )

    if not isinstance(
        modules,
        list,
    ):
        return operations

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

                operations.append(
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

    return operations


def get_executable_operations(
    rtl_entries: List[Dict[str, Any]],
) -> Set[str]:
    """
    Return executable ALU operations.

    The ALU selector is 3 bits and explicitly defines
    all values 000 through 111. Therefore the Verilog
    'default' branch is defensive/unreachable for a
    valid 3-bit selector and is not counted as a
    functional-operation coverage target.
    """

    result: Set[str] = set()

    for entry in rtl_entries:

        case_value = str(
            entry.get(
                "case_value",
                ""
            )
        ).strip().lower()

        operation = entry.get(
            "operation"
        )

        if not operation:
            continue

        if case_value == "default":
            continue

        result.add(
            str(operation)
        )

    return result


def get_default_branches(
    rtl_entries: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    return [
        entry
        for entry in rtl_entries
        if str(
            entry.get(
                "case_value",
                ""
            )
        ).strip().lower()
        == "default"
    ]


# ============================================================
# DAY-7 OBJECTIVES
# ============================================================

def get_objective_list(
    objectives_data: Any,
) -> List[Dict[str, Any]]:
    if isinstance(
        objectives_data,
        list,
    ):
        return [
            item
            for item in objectives_data
            if isinstance(
                item,
                dict,
            )
        ]

    if not isinstance(
        objectives_data,
        dict,
    ):
        raise ValueError(
            "Verification objectives must "
            "be a JSON object or list."
        )

    for key in (
        "objectives",
        "verification_objectives",
    ):

        value = objectives_data.get(
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

    raise ValueError(
        "Could not find objective list "
        "in verification objectives JSON."
    )


# ============================================================
# DAY-10 VALIDATED TESTS
# ============================================================

def get_validated_scenarios(
    validated_data: Any,
) -> List[Dict[str, Any]]:
    """
    Supports all formats used during the project.
    """

    if isinstance(
        validated_data,
        list,
    ):
        return [
            item
            for item in validated_data
            if isinstance(
                item,
                dict,
            )
        ]

    if not isinstance(
        validated_data,
        dict,
    ):
        return []

    for key in (
        "validated_tests",
        "scenarios",
        "validated_scenarios",
        "tests",
        "test_cases",
    ):

        value = validated_data.get(
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
# COVERAGE ANALYSIS
# ============================================================

def analyze_coverage(
    knowledge: Any,
    objectives_data: Any,
    validated_tests: Any,
) -> Dict[str, Any]:

    # --------------------------------------------------------
    # RTL operations
    # --------------------------------------------------------

    rtl_entries = extract_rtl_operations(
        knowledge
    )

    if not rtl_entries:
        raise ValueError(
            "No RTL operations found."
        )

    rtl_operations = (
        get_executable_operations(
            rtl_entries
        )
    )

    if not rtl_operations:
        raise ValueError(
            "No executable RTL operations found."
        )

    default_branches = (
        get_default_branches(
            rtl_entries
        )
    )

    # --------------------------------------------------------
    # Objectives
    # --------------------------------------------------------

    objectives = get_objective_list(
        objectives_data
    )

    objective_ids: Set[str] = set()

    objective_categories: Dict[
        str,
        str
    ] = {}

    for objective in objectives:

        objective_id = objective.get(
            "objective_id"
        )

        category = objective.get(
            "category",
            "unknown",
        )

        if not objective_id:
            continue

        objective_id = str(
            objective_id
        )

        objective_ids.add(
            objective_id
        )

        objective_categories[
            objective_id
        ] = str(category)

    # --------------------------------------------------------
    # Validated scenarios
    # --------------------------------------------------------

    scenarios = get_validated_scenarios(
        validated_tests
    )

    if not scenarios:
        raise ValueError(
            "No validated scenarios found."
        )

    covered_operations: Set[str] = set()
    covered_objectives: Set[str] = set()

    operation_hits: Counter = Counter()
    category_hits: Counter = Counter()

    for scenario in scenarios:

        operation = normalize_operation(
            scenario.get(
                "operation"
            )
        )

        objective_id = scenario.get(
            "objective_id"
        )

        category = scenario.get(
            "category",
            "unknown",
        )

        if operation:

            covered_operations.add(
                operation
            )

            operation_hits[
                operation
            ] += 1

        if objective_id:

            objective_id = str(
                objective_id
            )

            covered_objectives.add(
                objective_id
            )

            category_hits[
                str(category)
            ] += 1

    # --------------------------------------------------------
    # Valid intersection
    # --------------------------------------------------------

    valid_covered_operations = (
        covered_operations
        & rtl_operations
    )

    valid_covered_objectives = (
        covered_objectives
        & objective_ids
    )

    missing_operations = sorted(
        rtl_operations
        - valid_covered_operations
    )

    missing_objectives = sorted(
        objective_ids
        - valid_covered_objectives
    )

    # --------------------------------------------------------
    # Operation details
    # --------------------------------------------------------

    operation_details = {}

    for operation in sorted(
        rtl_operations
    ):

        hits = operation_hits.get(
            operation,
            0,
        )

        operation_details[
            operation
        ] = {
            "covered":
                hits > 0,

            "hits":
                hits,
        }

    # --------------------------------------------------------
    # Objective-category coverage
    # --------------------------------------------------------

    category_totals = Counter(
        objective_categories.values()
    )

    covered_by_category = Counter()

    for objective_id in (
        valid_covered_objectives
    ):

        category = (
            objective_categories.get(
                objective_id,
                "unknown",
            )
        )

        covered_by_category[
            category
        ] += 1

    category_coverage = {}

    all_categories = sorted(
        set(
            category_totals.keys()
        )
        | set(
            category_hits.keys()
        )
    )

    for category in all_categories:

        total_objectives = (
            category_totals.get(
                category,
                0,
            )
        )

        covered_count = (
            covered_by_category.get(
                category,
                0,
            )
        )

        category_coverage[
            category
        ] = {
            "total_objectives":
                total_objectives,

            "covered_objectives":
                covered_count,

            "coverage_percent":
                percentage(
                    covered_count,
                    total_objectives,
                ),

            "scenario_hits":
                category_hits.get(
                    category,
                    0,
                ),
        }

    # --------------------------------------------------------
    # Percentages
    # --------------------------------------------------------

    operation_coverage_percent = (
        percentage(
            len(
                valid_covered_operations
            ),
            len(
                rtl_operations
            ),
        )
    )

    objective_coverage_percent = (
        percentage(
            len(
                valid_covered_objectives
            ),
            len(
                objective_ids
            ),
        )
    )

    # --------------------------------------------------------
    # Overall status
    # --------------------------------------------------------

    status = (
        "PASS"
        if (
            len(missing_operations) == 0
            and len(missing_objectives) == 0
        )
        else "INCOMPLETE"
    )

    return {
        "status":
            status,

        "validated_scenario_count":
            len(scenarios),

        "rtl_branch_count":
            len(rtl_entries),

        "functional_operation_count":
            len(rtl_operations),

        "covered_operation_count":
            len(
                valid_covered_operations
            ),

        "operation_coverage_percent":
            operation_coverage_percent,

        "objective_count":
            len(objective_ids),

        "covered_objective_count":
            len(
                valid_covered_objectives
            ),

        "objective_coverage_percent":
            objective_coverage_percent,

        "operations":
            operation_details,

        "missing_operations":
            missing_operations,

        "missing_objectives":
            missing_objectives,

        "category_coverage":
            category_coverage,

        "default_branches_excluded_from_functional_targets":
            default_branches,

        "coverage_method":
            (
                "Validated Day-10 scenarios mapped "
                "against Day-6 executable RTL operations "
                "and Day-7 verification objectives."
            ),
    }


# ============================================================
# TERMINAL REPORT
# ============================================================

def print_report(
    report: Dict[str, Any],
) -> None:

    print(
        "RTL branches             :",
        report[
            "rtl_branch_count"
        ],
    )

    print(
        "Functional operations    :",
        report[
            "functional_operation_count"
        ],
    )

    print(
        "Operations covered       :",
        report[
            "covered_operation_count"
        ],
    )

    print(
        "Operation coverage       :",
        f"{report['operation_coverage_percent']}%",
    )

    print(
        "Verification objectives  :",
        report[
            "objective_count"
        ],
    )

    print(
        "Objectives covered       :",
        report[
            "covered_objective_count"
        ],
    )

    print(
        "Objective coverage       :",
        f"{report['objective_coverage_percent']}%",
    )

    print(
        "Validated scenarios      :",
        report[
            "validated_scenario_count"
        ],
    )

    print()

    print("Operation details:")

    for operation, info in (
        report[
            "operations"
        ].items()
    ):

        marker = (
            "COVERED"
            if info[
                "covered"
            ]
            else "MISSING"
        )

        print(
            f"  {operation:<12} "
            f"{marker:<8} "
            f"hits={info['hits']}"
        )

    if report[
        "missing_operations"
    ]:

        print()
        print(
            "Missing operations:"
        )

        for operation in report[
            "missing_operations"
        ]:

            print(
                " -",
                operation,
            )

    if report[
        "missing_objectives"
    ]:

        print()
        print(
            "Missing objective IDs:"
        )

        for objective_id in report[
            "missing_objectives"
        ]:

            print(
                " -",
                objective_id,
            )

    print()
    print(
        "FUNCTIONAL COVERAGE:",
        report["status"],
    )


# ============================================================
# MAIN
# ============================================================

def main() -> int:

    if len(sys.argv) != 5:

        print(
            "Usage:\n"
            "  python "
            "coverage/functional_coverage.py "
            "<rtl_knowledge.json> "
            "<verification_objectives.json> "
            "<validated_tests.json> "
            "<functional_coverage.json>"
        )

        return 2

    knowledge_path = sys.argv[1]
    objectives_path = sys.argv[2]
    validated_path = sys.argv[3]
    output_path = sys.argv[4]

    try:

        knowledge = load_json(
            knowledge_path
        )

        objectives_data = load_json(
            objectives_path
        )

        validated_tests = load_json(
            validated_path
        )

        report = analyze_coverage(
            knowledge,
            objectives_data,
            validated_tests,
        )

        save_json(
            output_path,
            report,
        )

        print_report(
            report
        )

        return (
            0
            if report[
                "status"
            ] == "PASS"
            else 1
        )

    except (
        FileNotFoundError,
        json.JSONDecodeError,
        ValueError,
    ) as error:

        print(
            "FUNCTIONAL COVERAGE: FAIL"
        )

        print(
            f"ERROR: {error}"
        )

        return 1

    except Exception as error:

        print(
            "FUNCTIONAL COVERAGE: FAIL"
        )

        print(
            f"UNEXPECTED ERROR: {error}"
        )

        return 1


if __name__ == "__main__":
    sys.exit(
        main()
    )
