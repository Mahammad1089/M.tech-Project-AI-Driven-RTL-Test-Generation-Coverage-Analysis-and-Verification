import sys
from pathlib import Path

from pyverilog.vparser.parser import parse
from pyverilog.vparser.ast import CaseStatement


def walk(node):

    yield node

    for child in node.children():

        yield from walk(child)


def main():

    if len(sys.argv) != 2:

        print(
            "Usage: python parser/inspect_cases.py "
            "<verilog_file>"
        )

        sys.exit(1)


    rtl_file = sys.argv[1]


    if not Path(rtl_file).exists():

        print(
            "ERROR: RTL file not found."
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
                f"CASE STATEMENT #{count}"
            )

            print(
                "Case expression:"
            )

            node.comp.show()

            print(
                "Number of case items:",
                len(node.caselist)
            )

            print()


    print(
        "Total case statements:",
        count
    )


if __name__ == "__main__":

    main()
