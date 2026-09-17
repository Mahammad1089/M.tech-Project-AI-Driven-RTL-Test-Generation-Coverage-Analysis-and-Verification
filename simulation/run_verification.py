import argparse
import sys

from core.simulator import (
    VerilogSimulator
)

from core.result_parser import (
    VerificationResultParser
)

from core.report_generator import (
    ReportGenerator
)


def main():

    parser_cli = argparse.ArgumentParser(

        description=(
            "Reusable Verilog "
            "verification runner"
        )

    )


    parser_cli.add_argument(
        "--rtl",
        required=True,
        help="RTL Verilog file"
    )


    parser_cli.add_argument(
        "--tb",
        required=True,
        help="Verilog testbench file"
    )


    parser_cli.add_argument(
        "--dut",
        required=True,
        help="DUT name"
    )


    parser_cli.add_argument(
        "--output",
        required=True,
        help="Compiled simulation output"
    )


    parser_cli.add_argument(
        "--report",
        required=True,
        help="JSON report path"
    )


    args = parser_cli.parse_args()


    simulator = (
        VerilogSimulator()
    )

    result_parser = (
        VerificationResultParser()
    )

    reporter = (
        ReportGenerator()
    )


    result = simulator.run(

        args.rtl,
        args.tb,
        args.output

    )


    if (
        result["overall_status"]
        != "PASS"
    ):

        print(
            "Execution failed at:",
            result["stage"]
        )

        sys.exit(1)


    output = result[
        "simulation"
    ][
        "stdout"
    ]


    parsed = (
        result_parser.parse(
            output
        )
    )


    report = {

        "dut":
            args.dut,

        "rtl_file":
            args.rtl,

        "testbench_file":
            args.tb,

        "compile_status":
            "PASS",

        "simulation_status":
            "PASS",

        **parsed

    }


    reporter.save_json(

        report,

        args.report

    )


    print(
        "DUT                 :",
        args.dut
    )

    print(
        "Total tests         :",
        parsed["total_tests"]
    )

    print(
        "Passed tests        :",
        parsed["passed_tests"]
    )

    print(
        "Failed tests        :",
        parsed["failed_tests"]
    )

    print(
        "Verification status :",
        parsed[
            "verification_status"
        ]
    )


    if (
        parsed[
            "verification_status"
        ]
        == "PASS"
    ):

        sys.exit(0)

    else:

        sys.exit(1)


if __name__ == "__main__":

    main()
