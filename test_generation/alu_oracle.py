import sys


MASK_4BIT = 0xF


def validate_input(value, name):

    if not isinstance(value, int):
        raise TypeError(
            f"{name} must be an integer."
        )

    if not 0 <= value <= 15:
        raise ValueError(
            f"{name} must be in range 0..15."
        )


def alu_expected(operation, a, b):

    validate_input(a, "a")
    validate_input(b, "b")

    if operation == "ADD":

        result = a + b

    elif operation == "SUB":

        result = a - b

    elif operation == "AND":

        result = a & b

    elif operation == "OR":

        result = a | b

    elif operation == "XOR":

        result = a ^ b

    elif operation == "NOT":

        result = ~a

    elif operation == "SHIFT_LEFT":

        result = a << 1

    elif operation == "SHIFT_RIGHT":

        result = a >> 1

    else:

        raise ValueError(
            f"Unsupported ALU operation: "
            f"{operation}"
        )

    return result & MASK_4BIT


def main():

    if len(sys.argv) != 4:

        print(
            "Usage: python "
            "test_generation/alu_oracle.py "
            "<operation> <a> <b>"
        )

        sys.exit(1)

    operation = sys.argv[1]

    try:

        a = int(
            sys.argv[2]
        )

        b = int(
            sys.argv[3]
        )

        result = alu_expected(
            operation,
            a,
            b
        )

    except (
        ValueError,
        TypeError
    ) as error:

        print(
            f"ERROR: {error}"
        )

        sys.exit(1)

    print(
        "Operation :",
        operation
    )

    print(
        "a         :",
        a
    )

    print(
        "b         :",
        b
    )

    print(
        "expected  :",
        result
    )

    print(
        "binary    :",
        format(
            result,
            "04b"
        )
    )


if __name__ == "__main__":
    main()
