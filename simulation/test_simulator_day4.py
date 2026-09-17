from core.simulator import (
    VerilogSimulator
)

from core.result_parser import (
    VerificationResultParser
)


def main():

    simulator = (
        VerilogSimulator()
    )

    parser = (
        VerificationResultParser()
    )


    result = simulator.run(

        rtl_file=
        "rtl/alu.v",

        testbench_file=
        "testbench/automated/"
        "tb_alu_selfcheck.v",

        output_file=
        "results/alu/day4/"
        "alu_day4.out"

    )


    print(
        "================================"
    )

    print(
        "DAY 4 AUTOMATED SIMULATION"
    )

    print(
        "================================"
    )


    if (
        result[
            "overall_status"
        ]
        != "PASS"
    ):

        print(
            "SIMULATION ENGINE: FAIL"
        )

        print(
            "Failure stage:",
            result["stage"]
        )

        return


    output = result[
        "simulation"
    ][
        "stdout"
    ]


    parsed = parser.parse(
        output
    )


    print(
        "Compilation       : PASS"
    )

    print(
        "Simulation        : PASS"
    )

    print(
        "Total tests       :",
        parsed["total_tests"]
    )

    print(
        "Passed tests      :",
        parsed["passed_tests"]
    )

    print(
        "Failed tests      :",
        parsed["failed_tests"]
    )

    print(
        "Verification      :",
        parsed[
            "verification_status"
        ]
    )


if __name__ == "__main__":

    main()
