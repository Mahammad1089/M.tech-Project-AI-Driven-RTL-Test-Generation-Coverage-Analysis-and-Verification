from alu_oracle import alu_expected


TESTS = [

    (
        "ADD",
        5,
        3,
        8
    ),

    (
        "ADD",
        15,
        1,
        0
    ),

    (
        "SUB",
        5,
        3,
        2
    ),

    (
        "SUB",
        0,
        1,
        15
    ),

    (
        "AND",
        5,
        3,
        1
    ),

    (
        "OR",
        5,
        3,
        7
    ),

    (
        "XOR",
        5,
        3,
        6
    ),

    (
        "NOT",
        5,
        0,
        10
    ),

    (
        "SHIFT_LEFT",
        5,
        0,
        10
    ),

    (
        "SHIFT_LEFT",
        9,
        0,
        2
    ),

    (
        "SHIFT_RIGHT",
        5,
        0,
        2
    ),

    (
        "SHIFT_RIGHT",
        9,
        0,
        4
    )
]


def main():

    passed = 0

    failed = 0

    for (
        operation,
        a,
        b,
        expected
    ) in TESTS:

        actual = alu_expected(
            operation,
            a,
            b
        )

        if actual == expected:

            print(
                "PASS:",
                operation,
                a,
                b,
                "->",
                actual
            )

            passed += 1

        else:

            print(
                "FAIL:",
                operation,
                a,
                b,
                "expected",
                expected,
                "received",
                actual
            )

            failed += 1

    print()

    print(
        "ORACLE TESTS =",
        len(
            TESTS
        )
    )

    print(
        "PASSED       =",
        passed
    )

    print(
        "FAILED       =",
        failed
    )

    if failed != 0:

        raise SystemExit(1)

    print()

    print(
        "ALU ORACLE VALIDATION: PASS"
    )


if __name__ == "__main__":
    main()
