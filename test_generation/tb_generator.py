#!/usr/bin/env python3

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


# ============================================================
# ALU OPERATION -> SELECTOR MAP
# ============================================================

OP_TO_SEL = {
    "ADD": 0,
    "SUB": 1,
    "AND": 2,
    "OR": 3,
    "XOR": 4,
    "NOT": 5,
    "SHIFT_LEFT": 6,
    "SHL": 6,
    "LEFT_SHIFT": 6,
    "SHIFT_RIGHT": 7,
    "SHR": 7,
    "RIGHT_SHIFT": 7,
}


# ============================================================
# JSON LOADING
# ============================================================

def load_json(path: str) -> Any:
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


# ============================================================
# VALIDATED SCENARIO EXTRACTION
# ============================================================

def get_validated_scenarios(
    data: Any,
) -> List[Dict[str, Any]]:
    """
    Extract validated tests from different supported
    Day-10 JSON structures.
    """

    if isinstance(data, list):
        return [
            item
            for item in data
            if isinstance(item, dict)
        ]

    if not isinstance(data, dict):
        return []

    for key in (
        "validated_scenarios",
        "scenarios",
        "validated_tests",
        "tests",
        "test_cases",
    ):

        value = data.get(key)

        if isinstance(value, list):
            return [
                item
                for item in value
                if isinstance(item, dict)
            ]

    return []


# ============================================================
# RECURSIVE VALUE SEARCH
# ============================================================

def recursive_find(
    data: Any,
    keys: List[str],
) -> Any:
    """
    Recursively search dictionaries/lists for one
    of the requested keys.
    """

    if isinstance(data, dict):

        for key in keys:

            if (
                key in data
                and data[key] is not None
            ):
                return data[key]

        for value in data.values():

            result = recursive_find(
                value,
                keys,
            )

            if result is not None:
                return result

    elif isinstance(data, list):

        for item in data:

            result = recursive_find(
                item,
                keys,
            )

            if result is not None:
                return result

    return None


# ============================================================
# NUMBER PARSING
# ============================================================

def parse_int(
    value: Any,
) -> Optional[int]:
    """
    Convert decimal, binary, hex and Verilog literals
    into Python integers.
    """

    if value is None:
        return None

    if isinstance(value, bool):
        return int(value)

    if isinstance(value, int):
        return value

    if isinstance(value, float):
        return int(value)

    text = (
        str(value)
        .strip()
        .lower()
        .replace("_", "")
    )

    if not text:
        return None

    try:

        if "'b" in text:
            return int(
                text.split("'b", 1)[1],
                2,
            )

        if "'h" in text:
            return int(
                text.split("'h", 1)[1],
                16,
            )

        if "'d" in text:
            return int(
                text.split("'d", 1)[1],
                10,
            )

        if "'o" in text:
            return int(
                text.split("'o", 1)[1],
                8,
            )

        if text.startswith("0b"):
            return int(text, 2)

        if text.startswith("0x"):
            return int(text, 16)

        return int(text, 10)

    except (
        TypeError,
        ValueError,
    ):
        return None


# ============================================================
# OPERATION HANDLING
# ============================================================

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

        "<<": "SHIFT_LEFT",
        ">>": "SHIFT_RIGHT",
    }

    return aliases.get(
        text,
        text,
    )


def extract_operation(
    test: Dict[str, Any],
) -> Optional[str]:

    value = recursive_find(
        test,
        [
            "operation",
            "operator",
            "op",
            "alu_operation",
            "operation_name",
            "expected_operation",
        ],
    )

    return normalize_operation(
        value
    )


# ============================================================
# SIGNAL EXTRACTION
# ============================================================

def extract_signal(
    test: Dict[str, Any],
    signal: str,
) -> Optional[int]:

    key_map = {

        "a": [
            "a",
            "input_a",
            "operand_a",
            "op_a",
        ],

        "b": [
            "b",
            "input_b",
            "operand_b",
            "op_b",
        ],

        "sel": [
            "sel",
            "selector",
            "opcode",
            "op_code",
        ],

        "y": [
            "expected_y",
            "expected",
            "expected_output",
            "result",
            "output_y",
        ],
    }

    value = recursive_find(
        test,
        key_map[signal],
    )

    return parse_int(
        value
    )


# ============================================================
# SELECTOR DETERMINATION
# ============================================================

def infer_selector(
    test: Dict[str, Any],
) -> Optional[int]:

    selector = extract_signal(
        test,
        "sel",
    )

    if selector is not None:
        return selector & 0x7

    operation = extract_operation(
        test
    )

    if operation is None:
        return None

    return OP_TO_SEL.get(
        operation
    )


# ============================================================
# EXPECTED ALU RESULT
# ============================================================

def expected_result(
    a: int,
    b: int,
    sel: int,
) -> int:

    a &= 0xF
    b &= 0xF
    sel &= 0x7

    if sel == 0:
        return (a + b) & 0xF

    if sel == 1:
        return (a - b) & 0xF

    if sel == 2:
        return a & b

    if sel == 3:
        return a | b

    if sel == 4:
        return a ^ b

    if sel == 5:
        return (~a) & 0xF

    if sel == 6:
        return (a << 1) & 0xF

    if sel == 7:
        return (a >> 1) & 0xF

    return 0


# ============================================================
# OBJECTIVE-ID HANDLING
# ============================================================

def get_objective_id(
    test: Dict[str, Any],
    index: int,
) -> str:

    value = recursive_find(
        test,
        ["objective_id"],
    )

    if value is not None:
        return str(value)

    return f"SCENARIO_{index:03d}"


# ============================================================
# TEST NORMALIZATION
# ============================================================

def normalize_test(
    test: Dict[str, Any],
    index: int,
) -> Dict[str, Any]:

    a = extract_signal(
        test,
        "a",
    )

    b = extract_signal(
        test,
        "b",
    )

    sel = infer_selector(
        test
    )

    expected = extract_signal(
        test,
        "y",
    )

    missing = []

    if a is None:
        missing.append("a")

    if b is None:
        missing.append("b")

    if sel is None:
        missing.append(
            "sel/operation"
        )

    if missing:

        raise ValueError(
            f"{get_objective_id(test, index)} "
            f"is missing: "
            + ", ".join(missing)
        )

    a &= 0xF
    b &= 0xF
    sel &= 0x7

    if expected is None:

        expected = expected_result(
            a,
            b,
            sel,
        )

    else:

        expected &= 0xF

    operation = (
        extract_operation(test)
        or f"SEL_{sel}"
    )

    return {
        "objective_id":
            get_objective_id(
                test,
                index,
            ),

        "a": a,
        "b": b,
        "sel": sel,
        "expected": expected,
        "operation": operation,
    }


# ============================================================
# VERILOG LITERAL
# ============================================================

def verilog_literal(
    width: int,
    value: int,
) -> str:

    digits = max(
        1,
        (width + 3) // 4,
    )

    mask = (
        1 << width
    ) - 1

    return (
        f"{width}'h"
        f"{value & mask:0{digits}X}"
    )


# ============================================================
# TESTBENCH GENERATION
# ============================================================

def generate_testbench(
    normalized_tests:
        List[Dict[str, Any]],
) -> str:

    lines: List[str] = []

    lines.extend(
        [
            "`timescale 1ns/1ps",
            "",
            "module tb_alu_hermes_generated;",
            "",
            "    reg  [3:0] a;",
            "    reg  [3:0] b;",
            "    reg  [2:0] sel;",
            "    wire [3:0] y;",
            "",
            "    integer pass_count;",
            "    integer fail_count;",
            "",
            "    alu dut (",
            "        .a(a),",
            "        .b(b),",
            "        .sel(sel),",
            "        .y(y)",
            "    );",
            "",
            "    task run_test;",
            "        input [3:0] test_a;",
            "        input [3:0] test_b;",
            "        input [2:0] test_sel;",
            "        input [3:0] expected_y;",
            "        input integer test_number;",
            "        begin",
            "            a   = test_a;",
            "            b   = test_b;",
            "            sel = test_sel;",
            "            #10;",
            "",
            "            if (y === expected_y) begin",
            "                pass_count = pass_count + 1;",
            '                $display("PASS test=%0d a=%h b=%h sel=%b y=%h",',
            "                         test_number, a, b, sel, y);",
            "            end",
            "            else begin",
            "                fail_count = fail_count + 1;",
            '                $display("FAIL test=%0d a=%h b=%h sel=%b expected=%h actual=%h",',
            "                         test_number, a, b, sel, expected_y, y);",
            "            end",
            "        end",
            "    endtask",
            "",
            "    initial begin",
            '        $dumpfile("results/alu/day11/alu_hermes_generated.vcd");',
            "        $dumpvars(0, tb_alu_hermes_generated);",
            "",
            "        pass_count = 0;",
            "        fail_count = 0;",
            "",
            "        a = 4'b0000;",
            "        b = 4'b0000;",
            "        sel = 3'b000;",
            "",
            "        #5;",
            "",
        ]
    )

    for index, test in enumerate(
        normalized_tests,
        start=1,
    ):

        objective = (
            test["objective_id"]
            .replace(
                "\n",
                " ",
            )
        )

        operation = (
            test["operation"]
            .replace(
                "\n",
                " ",
            )
        )

        lines.append(
            f"        // "
            f"{objective} | "
            f"{operation}"
        )

        lines.append(
            "        run_test("
            f"{verilog_literal(4, test['a'])}, "
            f"{verilog_literal(4, test['b'])}, "
            f"{verilog_literal(3, test['sel'])}, "
            f"{verilog_literal(4, test['expected'])}, "
            f"{index}"
            ");"
        )

        lines.append("")

    lines.extend(
        [
            '        $display("----------------------------------------");',
            '        $display("Generated ALU verification summary");',
            '        $display("PASS = %0d", pass_count);',
            '        $display("FAIL = %0d", fail_count);',
            '        $display("TOTAL = %0d", pass_count + fail_count);',
            '        $display("----------------------------------------");',
            "",
            "        if (fail_count == 0)",
            '            $display("TESTBENCH RESULT: PASS");',
            "        else",
            '            $display("TESTBENCH RESULT: FAIL");',
            "",
            "        $finish;",
            "    end",
            "",
            "endmodule",
            "",
        ]
    )

    return "\n".join(
        lines
    )


# ============================================================
# MAIN
# ============================================================

def main() -> int:

    if len(sys.argv) != 3:

        print(
            "Usage:\n"
            "  python "
            "test_generation/"
            "tb_generator.py "
            "<validated_tests.json> "
            "<output_testbench.v>"
        )

        return 2

    input_path = sys.argv[1]
    output_path = sys.argv[2]

    try:

        data = load_json(
            input_path
        )

        scenarios = (
            get_validated_scenarios(
                data
            )
        )

        if not scenarios:

            print(
                "TESTBENCH GENERATION: FAIL"
            )

            print(
                "ERROR: No validated "
                "scenarios were found."
            )

            return 1

        normalized_tests = []

        for index, scenario in enumerate(
            scenarios,
            start=1,
        ):

            normalized_tests.append(
                normalize_test(
                    scenario,
                    index,
                )
            )

        testbench = generate_testbench(
            normalized_tests
        )

        output_file = Path(
            output_path
        )

        output_file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_file.write_text(
            testbench,
            encoding="utf-8",
        )

        print(
            "TESTBENCH GENERATION: PASS"
        )

        print(
            "Validated scenarios loaded:",
            len(scenarios),
        )

        print(
            "Tests generated:",
            len(normalized_tests),
        )

        print(
            "Output file:",
            output_path,
        )

        return 0

    except (
        FileNotFoundError,
        json.JSONDecodeError,
        ValueError,
    ) as error:

        print(
            "TESTBENCH GENERATION: FAIL"
        )

        print(
            f"ERROR: {error}"
        )

        return 1

    except Exception as error:

        print(
            "TESTBENCH GENERATION: FAIL"
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
