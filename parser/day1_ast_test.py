from pyverilog.vparser.parser import parse


def main():

    files = [
        "rtl/day1_test.v"
    ]

    ast, directives = parse(
        files
    )

    print(
        "\n=============================="
    )

    print(
        "PYVERILOG AST"
    )

    print(
        "==============================\n"
    )

    ast.show()

    print(
        "\n=============================="
    )

    print(
        "AST TEST PASS"
    )

    print(
        "=============================="
    )


if __name__ == "__main__":
    main()
