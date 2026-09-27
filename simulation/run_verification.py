#!/usr/bin/env python3

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path


# =============================================================
# Utility functions
# =============================================================

def run_command(command):
    """
    Execute a command and return:
        return_code
        stdout
        stderr
    """

    result = subprocess.run(
        command,
        text=True,
        capture_output=True
    )

    return (
        result.returncode,
        result.stdout,
        result.stderr
    )


def extract_integer(text, labels):
    """
    Search simulation output for an integer field.

    Supports formats such as:

        TOTAL TESTS: 15
        TOTAL_TESTS=15
        TOTAL CHECKS : 15
        Passed tests : 15

    labels is a list of possible names.
    """

    for label in labels:

        pattern = (
            re.escape(label)
            + r"\s*[:=]\s*(\d+)"
        )

        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE
        )

        if match:
            return int(match.group(1))

    return None


def extract_explicit_status(text):
    """
    Extract explicit verification status if printed
    by the Verilog testbench.
    """

    patterns = [
        r"VERIFICATION\s+STATUS\s*[:=]\s*(PASS|FAIL)",
        r"DAY\s+16\s+FSM\s+VERIFICATION\s+(PASS|FAIL)",
        r"FSM\s+VERIFICATION\s+(PASS|FAIL)",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE
        )

        if match:
            return match.group(1).upper()

    return None


# =============================================================
# Simulation-result parser
# =============================================================

def parse_simulation_output(sim_output):
    """
    Extract test counters from simulator output.

    Both TESTS and CHECKS formats are supported.
    """

    total_tests = extract_integer(
        sim_output,
        [
            "TOTAL TESTS",
            "TOTAL_TESTS",
            "TOTAL CHECKS",
            "TOTAL_CHECKS",
        ]
    )

    passed_tests = extract_integer(
        sim_output,
        [
            "PASSED TESTS",
            "PASSED_TESTS",
            "PASSED CHECKS",
            "PASSED_CHECKS",
        ]
    )

    failed_tests = extract_integer(
        sim_output,
        [
            "FAILED TESTS",
            "FAILED_TESTS",
            "FAILED CHECKS",
            "FAILED_CHECKS",
        ]
    )

    explicit_status = extract_explicit_status(sim_output)

    # ---------------------------------------------------------
    # Determine final verification status.
    # ---------------------------------------------------------

    if (
        total_tests is not None
        and passed_tests is not None
        and failed_tests is not None
    ):

        if (
            total_tests > 0
            and passed_tests == total_tests
            and failed_tests == 0
        ):
            calculated_status = "PASS"

        else:
            calculated_status = "FAIL"

    else:
        calculated_status = "UNKNOWN"


    # Explicit FAIL always has priority.
    if explicit_status == "FAIL":
        verification_status = "FAIL"

    elif (
        explicit_status == "PASS"
        and calculated_status == "PASS"
    ):
        verification_status = "PASS"

    elif calculated_status != "UNKNOWN":
        verification_status = calculated_status

    else:
        verification_status = "UNKNOWN"


    return {
        "total_tests": total_tests,
        "passed_tests": passed_tests,
        "failed_tests": failed_tests,
        "verification_status": verification_status,
    }


# =============================================================
# Main verification function
# =============================================================

def main():

    parser = argparse.ArgumentParser(
        description="Generic RTL compile and simulation verification runner"
    )

    parser.add_argument(
        "--rtl",
        required=True,
        help="RTL Verilog file"
    )

    parser.add_argument(
        "--tb",
        required=True,
        help="Verilog/SystemVerilog testbench"
    )

    parser.add_argument(
        "--dut",
        required=True,
        help="DUT/module name used for reporting"
    )

    parser.add_argument(
        "--output",
        required=True,
        help="Compiled Icarus simulation output"
    )

    parser.add_argument(
        "--report",
        required=True,
        help="JSON report output path"
    )

    args = parser.parse_args()


    # ---------------------------------------------------------
    # Resolve paths
    # ---------------------------------------------------------

    rtl_path = Path(args.rtl)
    tb_path = Path(args.tb)
    output_path = Path(args.output)
    report_path = Path(args.report)


    # ---------------------------------------------------------
    # Validate input files
    # ---------------------------------------------------------

    if not rtl_path.exists():

        print(
            f"ERROR: RTL file does not exist: "
            f"{rtl_path}"
        )

        sys.exit(1)


    if not tb_path.exists():

        print(
            f"ERROR: Testbench file does not exist: "
            f"{tb_path}"
        )

        sys.exit(1)


    # ---------------------------------------------------------
    # Create result directories
    # ---------------------------------------------------------

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    report_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )


    # =========================================================
    # STEP 1
    # Compile RTL + testbench
    # =========================================================

    compile_command = [
        "iverilog",
        "-g2012",
        "-Wall",
        "-o",
        str(output_path),
        str(rtl_path),
        str(tb_path),
    ]


    print("")
    print("==============================================")
    print("RTL VERIFICATION")
    print("==============================================")

    print("DUT :", args.dut)

    print("")
    print("Compiling RTL and testbench...")

    compile_rc, compile_stdout, compile_stderr = run_command(
        compile_command
    )


    if compile_rc == 0:

        compile_status = "PASS"

        print("Compilation : PASS")

    else:

        compile_status = "FAIL"

        print("Compilation : FAIL")

        if compile_stdout.strip():
            print("")
            print("Compiler stdout:")
            print(compile_stdout)

        if compile_stderr.strip():
            print("")
            print("Compiler stderr:")
            print(compile_stderr)


        report = {

            "generated_at":
                datetime.now().isoformat(),

            "dut":
                args.dut,

            "rtl_file":
                str(rtl_path),

            "testbench_file":
                str(tb_path),

            "compile_status":
                "FAIL",

            "simulation_status":
                "NOT_RUN",

            "total_tests":
                None,

            "passed_tests":
                None,

            "failed_tests":
                None,

            "verification_status":
                "FAIL",

            "compile_stdout":
                compile_stdout,

            "compile_stderr":
                compile_stderr,
        }


        with report_path.open(
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                report,
                file,
                indent=4
            )


        print("")
        print(
            f"Report written to: "
            f"{report_path}"
        )

        sys.exit(1)


    # =========================================================
    # STEP 2
    # Run simulation
    # =========================================================

    print("")
    print("Running simulation...")


    simulation_command = [
        "vvp",
        str(output_path)
    ]


    sim_rc, sim_stdout, sim_stderr = run_command(
        simulation_command
    )


    if sim_rc == 0:

        simulation_status = "PASS"

        print("Simulation  : PASS")

    else:

        simulation_status = "FAIL"

        print("Simulation  : FAIL")


    # ---------------------------------------------------------
    # Display Verilog output
    # ---------------------------------------------------------

    if sim_stdout.strip():

        print("")
        print("--------------- SIMULATION OUTPUT ------------")
        print(sim_stdout.rstrip())
        print("----------------------------------------------")


    if sim_stderr.strip():

        print("")
        print("Simulation stderr:")
        print(sim_stderr)


    # =========================================================
    # STEP 3
    # Parse self-checking results
    # =========================================================

    parsed = parse_simulation_output(
        sim_stdout
    )


    total_tests = parsed["total_tests"]
    passed_tests = parsed["passed_tests"]
    failed_tests = parsed["failed_tests"]
    verification_status = parsed[
        "verification_status"
    ]


    # A simulator execution failure must never be PASS.
    if simulation_status != "PASS":
        verification_status = "FAIL"


    # =========================================================
    # STEP 4
    # Build JSON report
    # =========================================================

    report = {

        "generated_at":
            datetime.now().isoformat(),

        "dut":
            args.dut,

        "rtl_file":
            str(rtl_path),

        "testbench_file":
            str(tb_path),

        "compile_status":
            compile_status,

        "simulation_status":
            simulation_status,

        "total_tests":
            total_tests,

        "passed_tests":
            passed_tests,

        "failed_tests":
            failed_tests,

        "verification_status":
            verification_status,
    }


    # ---------------------------------------------------------
    # Save JSON report
    # ---------------------------------------------------------

    with report_path.open(
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            report,
            file,
            indent=4
        )


    # =========================================================
    # STEP 5
    # Final terminal summary
    # =========================================================

    print("")
    print("==============================================")
    print("PYTHON VERIFICATION SUMMARY")
    print("==============================================")

    print(
        f"DUT                 : "
        f"{args.dut}"
    )

    print(
        f"Compile status      : "
        f"{compile_status}"
    )

    print(
        f"Simulation status   : "
        f"{simulation_status}"
    )

    print(
        f"Total tests         : "
        f"{total_tests}"
    )

    print(
        f"Passed tests        : "
        f"{passed_tests}"
    )

    print(
        f"Failed tests        : "
        f"{failed_tests}"
    )

    print(
        f"Verification status : "
        f"{verification_status}"
    )

    print(
        f"JSON report         : "
        f"{report_path}"
    )

    print("==============================================")


    # ---------------------------------------------------------
    # Exit code
    # ---------------------------------------------------------

    if verification_status == "PASS":
        sys.exit(0)

    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
