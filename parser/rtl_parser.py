import sys
from pathlib import Path

from pyverilog.vparser.parser import parse


def parse_verilog(file_path):

    path = Path(file_path)

    if not path.exists():

        print(
            f"ERROR: RTL file not found: {file_path}"
        )

        return None


    print(
        f"Parsing RTL file: {file_path}"
    )


    ast, directives = parse(
        [str(path)]
    )


    return ast


def main():

    if len(sys.argv) != 2:

        print(
            "Usage: python parser/rtl_parser.py "
            "<verilog_file>"
        )

        sys.exit(1)


    rtl_file = sys.argv[1]


    ast = parse_verilog(
        rtl_file
    )


    if ast is None:

        print(
            "RTL PARSING: FAIL"
        )

        sys.exit(1)


    print()
    print(
        "RTL PARSING: PASS"
    )


    print()
    print(
        "========== AST =========="
    )


    ast.show()


if __name__ == "__main__":

    main()
