import sys
from pathlib import Path

from pyverilog.vparser.parser import parse


def walk(node, depth=0):

    indent = "  " * depth

    print(
        f"{indent}{node.__class__.__name__}"
    )


    for child in node.children():

        walk(
            child,
            depth + 1
        )


def main():

    if len(sys.argv) != 2:

        print(
            "Usage: python parser/ast_inspector.py "
            "<verilog_file>"
        )

        sys.exit(1)


    rtl_file = sys.argv[1]


    if not Path(rtl_file).exists():

        print(
            f"ERROR: File not found: {rtl_file}"
        )

        sys.exit(1)


    ast, directives = parse(
        [rtl_file]
    )


    print(
        "AST NODE TYPES"
    )

    print(
        "=============="
    )


    walk(ast)


if __name__ == "__main__":

    main()
