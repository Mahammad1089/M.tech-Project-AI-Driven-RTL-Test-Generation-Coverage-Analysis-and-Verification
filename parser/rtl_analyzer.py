import json

import sys
from pathlib import Path

from pyverilog.vparser.parser import parse

from pyverilog.vparser.ast import (
    ModuleDef,
    Input,
    Output,
    Inout,
    CaseStatement,
    Identifier,
    IntConst,
    BlockingSubstitution,
    Plus,
    Minus,
    And,
    Or,
    Xor,
    Unot,
    Sll,
    Srl
)


OPERATOR_NAMES = {

    Plus:
        "ADD",

    Minus:
        "SUB",

    And:
        "AND",

    Or:
        "OR",

    Xor:
        "XOR",

    Unot:
        "NOT",

    Sll:
        "SHIFT_LEFT",

    Srl:
        "SHIFT_RIGHT"
}


OPERATOR_SYMBOLS = {

    Plus:
        "+",

    Minus:
        "-",

    And:
        "&",

    Or:
        "|",

    Xor:
        "^",

    Unot:
        "~",

    Sll:
        "<<",

    Srl:
        ">>"
}


def walk(node):

    yield node

    for child in node.children():

        yield from walk(child)


def width_to_dict(width):

    if width is None:

        return {
            "msb": 0,
            "lsb": 0,
            "bits": 1
        }


    try:

        msb = int(
            width.msb.value
        )

        lsb = int(
            width.lsb.value
        )


        return {
            "msb": msb,
            "lsb": lsb,
            "bits": abs(
                msb - lsb
            ) + 1
        }


    except Exception:

        return {
            "msb": None,
            "lsb": None,
            "bits": None
        }


def node_to_text(node):

    if node is None:

        return None


    if isinstance(
        node,
        Identifier
    ):

        return node.name


    if isinstance(
        node,
        IntConst
    ):

        return node.value


    node_type = type(node)


    if node_type in OPERATOR_SYMBOLS:

        symbol = OPERATOR_SYMBOLS[
            node_type
        ]


        children = list(
            node.children()
        )


        if isinstance(
            node,
            Unot
        ):

            if len(children) == 1:

                return (
                    f"{symbol}"
                    f"{node_to_text(children[0])}"
                )


        if len(children) == 2:

            left = node_to_text(
                children[0]
            )

            right = node_to_text(
                children[1]
            )


            return (
                f"{left} "
                f"{symbol} "
                f"{right}"
            )


    return node.__class__.__name__


def get_identifier(node):

    if node is None:

        return None


    if isinstance(
        node,
        Identifier
    ):

        return node.name


    for child in node.children():

        result = get_identifier(
            child
        )

        if result is not None:

            return result


    return None


def analyze_expression(node):

    if isinstance(
        node,
        Identifier
    ):

        return {

            "operator":
                "DIRECT",

            "expression":
                node.name,

            "left_operand":
                node.name,

            "right_operand":
                None
        }


    if isinstance(
        node,
        IntConst
    ):

        return {

            "operator":
                "CONSTANT",

            "expression":
                node.value,

            "left_operand":
                node.value,

            "right_operand":
                None
        }


    node_type = type(node)


    operator = OPERATOR_NAMES.get(
        node_type,
        "UNKNOWN"
    )


    children = list(
        node.children()
    )


    result = {

        "operator":
            operator,

        "expression":
            node_to_text(
                node
            ),

        "left_operand":
            None,

        "right_operand":
            None
    }


    if isinstance(
        node,
        Unot
    ):

        if len(children) == 1:

            result[
                "left_operand"
            ] = node_to_text(
                children[0]
            )


        return result


    if len(children) >= 1:

        result[
            "left_operand"
        ] = node_to_text(
            children[0]
        )


    if len(children) >= 2:

        result[
            "right_operand"
        ] = node_to_text(
            children[1]
        )


    return result


def analyze_case_statement(
    case_node
):

    selector = node_to_text(
        case_node.comp
    )


    case_data = {

        "selector":
            selector,

        "branches":
            []
    }


    for case_item in case_node.caselist:

        conditions = (
            case_item.cond
        )


        if conditions is None:

            case_value = (
                "default"
            )

        else:

            values = []

            for condition in conditions:

                values.append(
                    node_to_text(
                        condition
                    )
                )


            case_value = ", ".join(
                values
            )


        assignment = None


        for node in walk(
            case_item.statement
        ):

            if isinstance(
                node,
                BlockingSubstitution
            ):

                assignment = node

                break


        if assignment is None:

            case_data[
                "branches"
            ].append({

                "case_value":
                    case_value,

                "assignment":
                    None
            })

            continue


        destination = (
            get_identifier(
                assignment.left
            )
        )


        expression_node = None


        children = list(
            assignment.right.children()
        )


        if children:

            expression_node = (
                children[0]
            )

        else:

            expression_node = (
                assignment.right
            )


        expression_data = (
            analyze_expression(
                expression_node
            )
        )


        branch = {

            "case_value":
                case_value,

            "destination":
                destination,

            **expression_data
        }


        case_data[
            "branches"
        ].append(
            branch
        )


    return case_data


def analyze_module(
    module_node
):

    module_data = {

        "module_name":
            module_node.name,

        "ports":
            [],

        "case_logic":
            []
    }


    seen_ports = set()


    for node in walk(
        module_node
    ):

        direction = None


        if isinstance(
            node,
            Input
        ):

            direction = "input"


        elif isinstance(
            node,
            Output
        ):

            direction = "output"


        elif isinstance(
            node,
            Inout
        ):

            direction = "inout"


        if direction is not None:

            if node.name not in seen_ports:

                module_data[
                    "ports"
                ].append({

                    "name":
                        node.name,

                    "direction":
                        direction,

                    "width":
                        width_to_dict(
                            node.width
                        )
                })


                seen_ports.add(
                    node.name
                )


        if isinstance(
            node,
            CaseStatement
        ):

            module_data[
                "case_logic"
            ].append(

                analyze_case_statement(
                    node
                )

            )


    return module_data


def analyze_rtl(ast):

    knowledge = {

        "rtl_language":
            "Verilog",

        "analysis_method":
            "PyVerilog AST",

        "modules":
            []
    }


    for node in walk(ast):

        if isinstance(
            node,
            ModuleDef
        ):

            knowledge[
                "modules"
            ].append(

                analyze_module(
                    node
                )

            )


    return knowledge


def main():

    if len(sys.argv) != 3:

        print(
            "Usage:"
        )

        print(
            "python parser/rtl_analyzer.py "
            "<rtl_file> <output_json>"
        )

        sys.exit(1)


    rtl_file = sys.argv[1]

    output_json = sys.argv[2]


    rtl_path = Path(
        rtl_file
    )


    if not rtl_path.exists():

        print(
            f"ERROR: RTL file not found: "
            f"{rtl_file}"
        )

        sys.exit(1)


    print(
        f"Analyzing RTL: "
        f"{rtl_file}"
    )


    ast, directives = parse(
        [rtl_file]
    )


    knowledge = analyze_rtl(
        ast
    )


    output_path = Path(
        output_json
    )


    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )


    output_path.write_text(

        json.dumps(
            knowledge,
            indent=4
        )

    )


    print()

    print(
        json.dumps(
            knowledge,
            indent=4
        )
    )


    print()

    print(
        f"Knowledge model saved to: "
        f"{output_json}"
    )


if __name__ == "__main__":

    main()
