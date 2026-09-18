import sys
from pathlib import Path

from pyverilog.vparser.parser import parse
from pyverilog.vparser.ast import CaseStatement


def walk(node):

    yield node

    for child in node.children():

        yield from walk(child)


def describe_node(
    node,
    depth=0
):

    indent = "  " * depth

    print(
        f"{indent}"
        f"{node.__class__.__name__}"
    )


    for child in node.children():

        describe_node(
            child,
            depth + 1
        )


def main():

    if len(sys.argv) != 2:

        print(
            "Usage: python "
            "parser/inspect_case_details.py "
            "<verilog_file>"
        )

        sys.exit(1)


    rtl_file = sys.argv[1]


    if not Path(
        rtl_file
    ).exists():

        print(
            f"ERROR: RTL file not found: "
            f"{rtl_file}"
        )

        sys.exit(1)


    ast, directives = parse(
        [rtl_file]
    )


    count = 0


    for node in walk(ast):

        if isinstance(
            node,
            CaseStatement
        ):

            count += 1

            print(
                "================================"
            )

            print(
                f"CASE STATEMENT #{count}"
            )

            print(
                "================================"
            )


            print(
                "Selector node:"
            )

            node.comp.show()


            print()

            print(
                "Complete case subtree:"
            )

            describe_node(
                node
            )


            print()


    print(
        "Total case statements:",
        count
    )


if __name__ == "__main__":

    main()
