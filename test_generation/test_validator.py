#!/usr/bin/env python3

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ============================================================
# JSON UTILITIES
# ============================================================

def load_json(path: str) -> Any:
    """Load a JSON file."""

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: str, data: Any) -> None:
    """Write JSON data and create the parent directory if needed."""

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            indent=2,
            ensure_ascii=False,
        )


# ============================================================
# DAY-6 RTL KNOWLEDGE PARSER
# ============================================================

def load_rtl_operations(knowledge: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract RTL operations from Day-6 RTL knowledge.

    Expected structure:

    {
        "modules": [
            {
                "module_name": "alu",
                "ports": [...],
                "case_logic": [
                    {
                        "selector": "sel",
                        "branches": [...]
                    }
                ]
            }
        ]
    }
    """

    rtl_operations: List[Dict[str, Any]] = []

    if not isinstance(knowledge, dict):
        return rtl_operations

    modules = knowledge.get("modules", [])

    if not isinstance(modules, list):
        return rtl_operations

    for module in modules:

        if not isinstance(module, dict):
            continue

        module_name = module.get("module_name")
        case_logic = module.get("case_logic", [])

        if not isinstance(case_logic, list):
            continue

        for case_block in case_logic:

            if not isinstance(case_block, dict):
                continue

            selector = case_block.get("selector")
            branches = case_block.get("branches", [])

            if not isinstance(branches, list):
                continue

            for branch in branches:

                if not isinstance(branch, dict):
                    continue

                operator = branch.get("operator")

                if not operator:
                    continue

                rtl_operations.append(
                    {
                        "module": module_name,
                        "selector": selector,
                        "case_value": branch.get("case_value"),
                        "operation": operator,
                        "operator": operator,
                        "destination": branch.get("destination"),
                        "expression": branch.get("expression"),
                        "left_operand": branch.get("left_operand"),
                        "right_operand": branch.get("right_operand"),
                    }
                )

    return rtl_operations


def detect_port_width(
    knowledge: Dict[str, Any],
    port_name: str,
) -> Optional[int]:
    """
    Determine the bit width of a port from modules[].ports[].

    Supports:

        "width": 4

    and:

        "width": {
            "msb": 3,
            "lsb": 0,
            "bits": 4
        }
    """

    if not isinstance(knowledge, dict):
        return None

    modules = knowledge.get("modules", [])

    if not isinstance(modules, list):
        return None

    for module in modules:

        if not isinstance(module, dict):
            continue

        ports = module.get("ports", [])

        if not isinstance(ports, list):
            continue

        for port in ports:

            if not isinstance(port, dict):
                continue

            if port.get("name") != port_name:
                continue

            width = port.get("width")

            # Example: "width": 4
            if isinstance(width, int):
                return width

            # Example:
            # "width": {"msb": 3, "lsb": 0, "bits": 4}
            if isinstance(width, dict):

                bits = width.get("bits")

                if bits is not None:
                    try:
                        return int(bits)
                    except (TypeError, ValueError):
                        pass

                msb = width.get("msb")
                lsb = width.get("lsb")

                if msb is not None and lsb is not None:
                    try:
                        return abs(int(msb) - int(lsb)) + 1
                    except (TypeError, ValueError):
                        pass

    return None


# ============================================================
# OBJECTIVE PARSER
# ============================================================

def extract_objectives(data: Any) -> List[Any]:
    """
    Extract verification objectives from common Day-7 JSON layouts.
    """

    if isinstance(data, list):
        return data

    if not isinstance(data, dict):
        return []

    possible_keys = [
        "objectives",
        "verification_objectives",
        "coverage_objectives",
        "items",
    ]

    for key in possible_keys:

        value = data.get(key)

        if isinstance(value, list):
            return value

    # Last fallback:
    # collect dictionary/list entries that appear to be objectives.
    collected: List[Any] = []

    for value in data.values():

        if isinstance(value, list):
            collected.extend(value)

    return collected


# ============================================================
# CANDIDATE TEST PARSER
# ============================================================

def extract_candidate_tests(data: Any) -> List[Dict[str, Any]]:
    """
    Extract tests from common candidate_tests.json structures.
    """

    if isinstance(data, list):
        return [
            item
            for item in data
            if isinstance(item, dict)
        ]

    if not isinstance(data, dict):
        return []

    possible_keys = [
        "candidate_tests",
        "tests",
        "test_cases",
        "generated_tests",
        "cases",
        "candidates",
    ]

    for key in possible_keys:

        value = data.get(key)

        if isinstance(value, list):
            return [
                item
                for item in value
                if isinstance(item, dict)
            ]

    # If the entire dictionary itself looks like one test.
    if any(
        key in data
        for key in [
            "operation",
            "operator",
            "op",
            "a",
            "b",
            "sel",
            "inputs",
        ]
    ):
        return [data]

    # Recursive fallback for nested generator output.
    collected: List[Dict[str, Any]] = []

    for value in data.values():

        if isinstance(value, dict):

            nested = extract_candidate_tests(value)

            if nested:
                collected.extend(nested)

        elif isinstance(value, list):

            dictionary_items = [
                item
                for item in value
                if isinstance(item, dict)
            ]

            if dictionary_items:
                collected.extend(dictionary_items)

    return collected


# ============================================================
# OPERATION NORMALIZATION
# ============================================================

OPERATION_ALIASES = {
    "ADD": "ADD",
    "ADDITION": "ADD",
    "+": "ADD",

    "SUB": "SUB",
    "SUBTRACT": "SUB",
    "SUBTRACTION": "SUB",
    "-": "SUB",

    "AND": "AND",
    "&": "AND",

    "OR": "OR",
    "|": "OR",

    "XOR": "XOR",
    "^": "XOR",

    "NOT": "NOT",
    "~": "NOT",

    "SHIFT_LEFT": "SHIFT_LEFT",
    "SHL": "SHIFT_LEFT",
    "LEFT_SHIFT": "SHIFT_LEFT",
    "<<": "SHIFT_LEFT",

    "SHIFT_RIGHT": "SHIFT_RIGHT",
    "SHR": "SHIFT_RIGHT",
    "RIGHT_SHIFT": "SHIFT_RIGHT",
    ">>": "SHIFT_RIGHT",

    "CONSTANT": "CONSTANT",
    "DEFAULT": "CONSTANT",
}


def normalize_operation(value: Any) -> Optional[str]:
    """Normalize operation names."""

    if value is None:
        return None

    text = str(value).strip().upper()

    text = text.replace("-", "_")
    text = text.replace(" ", "_")

    return OPERATION_ALIASES.get(text, text)


def get_test_operation(test: Dict[str, Any]) -> Optional[str]:
    """
    Try several common locations for the operation associated with a test.
    """

    direct_keys = [
        "operation",
        "operator",
        "op",
        "alu_operation",
        "expected_operation",
        "operation_name",
    ]

    for key in direct_keys:

        if key in test:
            operation = normalize_operation(test.get(key))

            if operation:
                return operation

    inputs = test.get("inputs")

    if isinstance(inputs, dict):

        for key in direct_keys:

            if key in inputs:
                operation = normalize_operation(inputs.get(key))

                if operation:
                    return operation

    return None


# ============================================================
# SELECTOR SUPPORT
# ============================================================

def normalize_binary_selector(value: Any) -> Optional[int]:
    """
    Convert values such as:

        0
        "0"
        "3'b000"
        "3'b101"

    to integer selector values.
    """

    if value is None:
        return None

    if isinstance(value, bool):
        return int(value)

    if isinstance(value, int):
        return value

    text = str(value).strip().lower()

    if not text:
        return None

    if text == "default":
        return None

    try:
        if "'b" in text:
            binary_part = text.split("'b", 1)[1]
            return int(binary_part, 2)

        if text.startswith("0b"):
            return int(text, 2)

        return int(text, 0)

    except ValueError:
        return None


def build_selector_map(
    rtl_operations: List[Dict[str, Any]],
) -> Dict[int, str]:
    """Build selector-value -> operation mapping."""

    selector_map: Dict[int, str] = {}

    for operation in rtl_operations:

        selector_value = normalize_binary_selector(
            operation.get("case_value")
        )

        operator = normalize_operation(
            operation.get("operator")
        )

        if selector_value is None or operator is None:
            continue

        selector_map[selector_value] = operator

    return selector_map


def get_test_selector(test: Dict[str, Any]) -> Optional[int]:
    """Extract ALU selector from a candidate test."""

    selector_keys = [
        "sel",
        "selector",
        "opcode",
        "op_code",
    ]

    for key in selector_keys:

        if key in test:
            value = normalize_binary_selector(test.get(key))

            if value is not None:
                return value

    inputs = test.get("inputs")

    if isinstance(inputs, dict):

        for key in selector_keys:

            if key in inputs:
                value = normalize_binary_selector(inputs.get(key))

                if value is not None:
                    return value

    return None


# ============================================================
# OPERAND HELPERS
# ============================================================

def extract_input_value(
    test: Dict[str, Any],
    signal_name: str,
) -> Any:
    """Extract an input such as a or b."""

    if signal_name in test:
        return test.get(signal_name)

    inputs = test.get("inputs")

    if isinstance(inputs, dict):
        return inputs.get(signal_name)

    return None


def parse_numeric_value(value: Any) -> Optional[int]:
    """
    Parse basic integer and Verilog-style literal values.
    """

    if value is None:
        return None

    if isinstance(value, bool):
        return int(value)

    if isinstance(value, int):
        return value

    text = str(value).strip().lower()

    try:
        if "'b" in text:
            return int(text.split("'b", 1)[1], 2)

        if "'h" in text:
            return int(text.split("'h", 1)[1], 16)

        if "'d" in text:
            return int(text.split("'d", 1)[1], 10)

        if text.startswith("0b"):
            return int(text, 2)

        if text.startswith("0x"):
            return int(text, 16)

        return int(text)

    except ValueError:
        return None


def value_fits_width(
    value: Any,
    width: Optional[int],
) -> bool:
    """Check whether an unsigned value fits inside width bits."""

    if width is None:
        return True

    parsed = parse_numeric_value(value)

    # Unknown symbolic values are not rejected here.
    if parsed is None:
        return True

    minimum = 0
    maximum = (1 << width) - 1

    return minimum <= parsed <= maximum


# ============================================================
# TEST VALIDATION
# ============================================================

def validate_candidate_test(
    test: Dict[str, Any],
    rtl_operations: List[Dict[str, Any]],
    selector_map: Dict[int, str],
    a_width: Optional[int],
    b_width: Optional[int],
) -> Tuple[bool, List[str], Optional[str]]:
    """
    Validate one candidate test.

    Returns:
        valid
        reasons
        resolved_operation
    """

    reasons: List[str] = []

    known_operations = {
        normalize_operation(item.get("operator"))
        for item in rtl_operations
        if normalize_operation(item.get("operator"))
    }

    requested_operation = get_test_operation(test)
    selector = get_test_selector(test)

    selector_operation = None

    if selector is not None:
        selector_operation = selector_map.get(selector)

    resolved_operation = requested_operation or selector_operation

    # --------------------------------------------------------
    # Validate operation
    # --------------------------------------------------------

    if requested_operation:

        if requested_operation not in known_operations:
            reasons.append(
                f"Unknown RTL operation: {requested_operation}"
            )

    elif selector_operation:

        resolved_operation = selector_operation

    elif selector is not None:

        reasons.append(
            f"Selector {selector} does not map to a known RTL operation."
        )

    else:
        reasons.append(
            "No recognizable RTL operation or selector was found."
        )

    # --------------------------------------------------------
    # Check operation-selector consistency
    # --------------------------------------------------------

    if (
        requested_operation
        and selector_operation
        and requested_operation != selector_operation
    ):
        reasons.append(
            "Operation/selector mismatch: "
            f"operation={requested_operation}, "
            f"selector resolves to {selector_operation}."
        )

    # --------------------------------------------------------
    # Check operand widths
    # --------------------------------------------------------

    a_value = extract_input_value(test, "a")
    b_value = extract_input_value(test, "b")

    if a_value is not None and not value_fits_width(
        a_value,
        a_width,
    ):
        reasons.append(
            f"Input a={a_value} exceeds {a_width}-bit width."
        )

    if b_value is not None and not value_fits_width(
        b_value,
        b_width,
    ):
        reasons.append(
            f"Input b={b_value} exceeds {b_width}-bit width."
        )

    return (
        len(reasons) == 0,
        reasons,
        resolved_operation,
    )


# ============================================================
# MAIN VALIDATOR
# ============================================================

def run_validator(
    candidate_tests_path: str,
    rtl_knowledge_path: str,
    objectives_path: str,
    validated_output_path: str,
    rejection_output_path: str,
    report_output_path: str,
) -> int:

    candidate_data = load_json(candidate_tests_path)
    rtl_knowledge = load_json(rtl_knowledge_path)
    objective_data = load_json(objectives_path)

    candidate_tests = extract_candidate_tests(candidate_data)
    objectives = extract_objectives(objective_data)

    # IMPORTANT:
    # This reads modules -> case_logic -> branches.
    # It does NOT recursively call itself.
    rtl_operations = load_rtl_operations(rtl_knowledge)

    a_width = detect_port_width(
        rtl_knowledge,
        "a",
    )

    b_width = detect_port_width(
        rtl_knowledge,
        "b",
    )

    selector_map = build_selector_map(rtl_operations)

    print(f"Objective count: {len(objectives)}")
    print(f"Candidate test count: {len(candidate_tests)}")
    print(f"RTL operation count: {len(rtl_operations)}")
    print(f"Detected a width: {a_width}")
    print(f"Detected b width: {b_width}")

    # --------------------------------------------------------
    # Critical RTL extraction check
    # --------------------------------------------------------

    if not rtl_operations:

        report = {
            "status": "FAIL",
            "reason": "No RTL operations could be loaded.",
            "objective_count": len(objectives),
            "candidate_test_count": len(candidate_tests),
            "rtl_operation_count": 0,
            "a_width": a_width,
            "b_width": b_width,
        }

        save_json(
            validated_output_path,
            {
                "validated_tests": []
            },
        )

        save_json(
            rejection_output_path,
            {
                "rejected_tests": [],
                "global_error": (
                    "No RTL operations could be loaded."
                ),
            },
        )

        save_json(
            report_output_path,
            report,
        )

        print("DAY 10 VALIDATOR: FAIL")
        print("No RTL operations could be loaded.")

        return 1

    # --------------------------------------------------------
    # Print discovered RTL operations
    # --------------------------------------------------------

    print("\nLoaded RTL operations:")

    for operation in rtl_operations:

        print(
            "  "
            f"{operation.get('case_value')} "
            f"-> {operation.get('operator')} "
            f"-> {operation.get('expression')}"
        )

    # --------------------------------------------------------
    # Validate candidates
    # --------------------------------------------------------

    validated_tests: List[Dict[str, Any]] = []
    rejected_tests: List[Dict[str, Any]] = []

    operation_coverage = {
        normalize_operation(item.get("operator")): 0
        for item in rtl_operations
        if normalize_operation(item.get("operator"))
    }

    for index, test in enumerate(
        candidate_tests,
        start=1,
    ):

        valid, reasons, resolved_operation = validate_candidate_test(
            test=test,
            rtl_operations=rtl_operations,
            selector_map=selector_map,
            a_width=a_width,
            b_width=b_width,
        )

        test_copy = dict(test)

        test_copy["_validator"] = {
            "index": index,
            "resolved_operation": resolved_operation,
        }

        if valid:

            test_copy["_validator"]["status"] = "VALID"

            validated_tests.append(test_copy)

            if resolved_operation in operation_coverage:
                operation_coverage[resolved_operation] += 1

        else:

            test_copy["_validator"]["status"] = "REJECTED"
            test_copy["_validator"]["reasons"] = reasons

            rejected_tests.append(test_copy)

    # --------------------------------------------------------
    # Coverage summary
    # --------------------------------------------------------

    covered_operations = [
        operation
        for operation, count in operation_coverage.items()
        if count > 0
    ]

    uncovered_operations = [
        operation
        for operation, count in operation_coverage.items()
        if count == 0
    ]

    total_operations = len(operation_coverage)
    covered_count = len(covered_operations)

    if total_operations:
        operation_coverage_percent = round(
            (covered_count / total_operations) * 100.0,
            2,
        )
    else:
        operation_coverage_percent = 0.0

    # --------------------------------------------------------
    # Write validated tests
    # --------------------------------------------------------

    validated_output = {
        "source": candidate_tests_path,
        "validated_test_count": len(validated_tests),
        "validated_tests": validated_tests,
    }

    save_json(
        validated_output_path,
        validated_output,
    )

    # --------------------------------------------------------
    # Write rejection report
    # --------------------------------------------------------

    rejection_output = {
    "source": candidate_tests_path,

    # Main Day-10 format
    "rejected_test_count": len(rejected_tests),
    "rejected_tests": rejected_tests,

    # Compatibility with later Day-10 steps
    "rejected_count": len(rejected_tests),
    "rejected_scenarios": rejected_tests,
    }

    save_json(
        rejection_output_path,
        rejection_output,
    )

    # --------------------------------------------------------
    # Main Day-10 report
    # --------------------------------------------------------

    report = {
        "status": (
            "PASS"
            if len(validated_tests) > 0
            else "FAIL"
        ),
        "objective_count": len(objectives),
        "candidate_test_count": len(candidate_tests),
        "validated_test_count": len(validated_tests),
        "rejected_test_count": len(rejected_tests),
        "rtl_operation_count": len(rtl_operations),
        "input_widths": {
            "a": a_width,
            "b": b_width,
        },
        "rtl_operations": [
            {
                "case_value": item.get("case_value"),
                "operator": item.get("operator"),
                "expression": item.get("expression"),
            }
            for item in rtl_operations
        ],
        "operation_coverage": operation_coverage,
        "covered_operations": covered_operations,
        "uncovered_operations": uncovered_operations,
        "operation_coverage_percent": operation_coverage_percent,
    }

    save_json(
        report_output_path,
        report,
    )

    # --------------------------------------------------------
    # Terminal summary
    # --------------------------------------------------------

    print()
    print(f"Validated tests: {len(validated_tests)}")
    print(f"Rejected tests: {len(rejected_tests)}")
    print(
        "Operation coverage: "
        f"{covered_count}/{total_operations} "
        f"({operation_coverage_percent}%)"
    )

    if uncovered_operations:
        print(
            "Uncovered operations:",
            ", ".join(uncovered_operations),
        )

    if validated_tests:
        print("DAY 10 VALIDATOR: PASS")
        return 0

    print("DAY 10 VALIDATOR: FAIL")
    print("No candidate tests passed validation.")

    return 1


# ============================================================
# COMMAND-LINE ENTRY POINT
# ============================================================

def main() -> int:

    if len(sys.argv) != 7:

        print(
            "Usage:\n"
            "  python test_generation/test_validator.py "
            "<candidate_tests.json> "
            "<rtl_knowledge.json> "
            "<verification_objectives.json> "
            "<validated_tests.json> "
            "<rejection_report.json> "
            "<validation_report.json>"
        )

        return 2

    return run_validator(
        candidate_tests_path=sys.argv[1],
        rtl_knowledge_path=sys.argv[2],
        objectives_path=sys.argv[3],
        validated_output_path=sys.argv[4],
        rejection_output_path=sys.argv[5],
        report_output_path=sys.argv[6],
    )


if __name__ == "__main__":
    sys.exit(main())
