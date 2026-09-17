import sys

from pathlib import Path

from core.simulator import (
    VerilogSimulator
)

from core.result_parser import (
    VerificationResultParser
)

from core.report_generator import (
    ReportGenerator
)


RTL_FILE = (
    "rtl/alu.v"
)

TB_FILE = (
    "testbench/automated/"
    "tb_alu_selfcheck.v"
)

OUTPUT_FILE = (
    "results/alu/day4/"
    "alu_day4.out"
)

REPORT_FILE = (
    "results/alu/day4/"
    "alu_day4_report.json"
)


def main():

    print(
        "========================================"
    )

    print(
        "DAY 4 - AUTOMATED VERIFICATION ENGINE"
    )

    print(
        "========================================"
    )


    simulator = (
        VerilogSimulator()
    )

    parser = (
        VerificationResultParser()
    )

    reporter = (
        ReportGenerator()
    )


    simulation_result = (
        simulator.run(
            RTL_FILE,
            TB_FILE,
            OUTPUT_FILE
        )
    )


    if (
        simulation_result[
            "overall_status"
        ]
        != "PASS"
    ):

        print(
            "Simulation engine failed."
        )

        print(
            "Stage:",
            simulation_result[
                "stage"
            ]
        )

        sys.exit(1)


    simulation_output = (
        simulation_result[
            "simulation"
        ][
            "stdout"
        ]
    )



    Path(
          "results/alu/day4/"
          "simulation_output.log"
        ).write_text(
         simulation_output
      )



    parsed = parser.parse(
        simulation_output
    )


    final_result = {

        "day":
            4,

        "dut":
            "alu",

        "rtl_file":
            RTL_FILE,

        "testbench_file":
            TB_FILE,

        "compile_status":
            "PASS",

        "simulation_status":
            "PASS",

        **parsed

    }


    reporter.save_json(

        final_result,

        REPORT_FILE

    )


    print(
        "RTL                 :",
        RTL_FILE
    )

    print(
        "Testbench           :",
        TB_FILE
    )

    print(
        "Compilation         : PASS"
    )

    print(
        "Simulation          : PASS"
    )

    print(
        "Total tests         :",
        parsed[
            "total_tests"
        ]
    )

    print(
        "Passed tests        :",
        parsed[
            "passed_tests"
        ]
    )

    print(
        "Failed tests        :",
        parsed[
            "failed_tests"
        ]
    )

    print(
        "Verification status :",
        parsed[
            "verification_status"
        ]
    )

    print(
        "Report              :",
        REPORT_FILE
    )


    if (
        parsed[
            "verification_status"
        ]
        == "PASS"
    ):

        print()

        print(
            "DAY 4 VERIFICATION: PASS"
        )

        sys.exit(0)


    else:

        print()

        print(
            "DAY 4 VERIFICATION: FAIL"
        )

        sys.exit(1)


if __name__ == "__main__":

    main()

