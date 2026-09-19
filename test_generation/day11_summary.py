#!/usr/bin/env python3

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


# ============================================================
# PROJECT PATHS
# ============================================================

VALIDATED_TESTS_FILE = Path(
    "results/alu/day10/validated_tests.json"
)

SIMULATION_REPORT_FILE = Path(
    "results/alu/day11/generated_simulation_report.json"
)

GENERATED_TESTBENCH_FILE = Path(
    "testbench/generated/tb_alu_hermes_generated.v"
)

VCD_FILE = Path(
    "results/alu/day11/alu_hermes_generated.vcd"
)

OUTPUT_SUMMARY_FILE = Path(
    "results/alu/day11/day11_summary.json"
)


# ============================================================
# JSON UTILITIES
# ============================================================

def load_json(path: Path) -> Dict[str, Any]:
    """
    Load a JSON file.

    Returns an empty dictionary if the file does not exist
    or cannot be parsed.
    """

    if not path.exists():
        return {}

    try:
        with path.open(
            "r",
            encoding="utf-8",
        ) as f:
            data = json.load(f)

        if isinstance(data, dict):
            return data

        return {
            "_root": data
        }

    except (
        json.JSONDecodeError,
        OSError,
    ):
        return {}


# ============================================================
# VALIDATED TEST EXTRACTION
# ============================================================

def get_validated_tests(
    data: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Extract validated scenarios from supported Day-10
    JSON structures.

    Supported keys:
        validated_tests
        scenarios
        validated_scenarios
        tests
        test_cases
    """

    if not isinstance(data, dict):
        return []

    root = data.get("_root")

    if isinstance(root, list):
        return [
            item
            for item in root
            if isinstance(item, dict)
        ]

    for key in (
        "validated_tests",
        "scenarios",
        "validated_scenarios",
        "tests",
        "test_cases",
    ):

        value = data.get(key)

        if isinstance(value, list):
            return [
                item
                for item in value
                if isinstance(item, dict)
            ]

    return []


# ============================================================
# NUMBER EXTRACTION
# ============================================================

def get_integer(
    data: Dict[str, Any],
    keys,
) -> Optional[int]:
    """
    Return the first valid integer found for any key.
    """

    if not isinstance(data, dict):
        return None

    for key in keys:

        value = data.get(key)

        if value is None:
            continue

        try:
            return int(value)

        except (
            TypeError,
            ValueError,
        ):
            continue

    return None


# ============================================================
# TESTBENCH TEST COUNT
# ============================================================

def count_generated_tests(
    testbench_path: Path,
) -> int:
    """
    Count generated run_test(...) calls in the Verilog
    testbench.

    The task declaration itself is excluded.
    """

    if not testbench_path.exists():
        return 0

    try:
        text = testbench_path.read_text(
            encoding="utf-8",
            errors="replace",
        )

    except OSError:
        return 0

    count = 0

    for line in text.splitlines():

        stripped = line.strip()

        if stripped.startswith("run_test("):
            count += 1

    return count


# ============================================================
# OPTIONAL DUT DETECTION
# ============================================================

def detect_dut(
    validated_data: Dict[str, Any],
) -> str:
    """
    Determine DUT name where possible.
    """

    for key in (
        "dut",
        "module",
        "module_name",
        "design",
    ):

        value = validated_data.get(key)

        if value:
            return str(value)

    # This Day-11 flow is for the ALU project.
    return "alu"


# ============================================================
# MAIN SUMMARY GENERATION
# ============================================================

def main() -> int:

    validated_data = load_json(
        VALIDATED_TESTS_FILE
    )

    simulation_data = load_json(
        SIMULATION_REPORT_FILE
    )

    validated_tests = get_validated_tests(
        validated_data
    )

    validated_scenarios = len(
        validated_tests
    )

    # --------------------------------------------------------
    # Generated-test count
    # --------------------------------------------------------

    generated_tests_from_tb = (
        count_generated_tests(
            GENERATED_TESTBENCH_FILE
        )
    )

    simulated_tests = get_integer(
        simulation_data,
        (
            "total_tests",
            "simulated_tests",
            "total",
            "test_count",
        ),
    )

    passed_tests = get_integer(
        simulation_data,
        (
            "passed_tests",
            "pass_count",
            "passed",
            "passes",
        ),
    )

    failed_tests = get_integer(
        simulation_data,
        (
            "failed_tests",
            "fail_count",
            "failed",
            "fails",
        ),
    )

    # If simulation report contains total tests,
    # use that as generated-test count.
    # Otherwise use run_test count from the testbench.

    if simulated_tests is not None:
        generated_tests = simulated_tests
    else:
        generated_tests = (
            generated_tests_from_tb
        )

    if passed_tests is None:
        passed_tests = 0

    if failed_tests is None:
        failed_tests = 0

    # --------------------------------------------------------
    # Artifact checks
    # --------------------------------------------------------

    generated_testbench_exists = (
        GENERATED_TESTBENCH_FILE.exists()
        and GENERATED_TESTBENCH_FILE.stat().st_size > 0
    )

    vcd_exists = (
        VCD_FILE.exists()
        and VCD_FILE.stat().st_size > 0
    )

    # --------------------------------------------------------
    # Consistency checks
    # --------------------------------------------------------

    scenario_count_matches = (
        validated_scenarios
        == generated_tests
    )

    generated_count_matches_tb = (
        generated_tests_from_tb
        == generated_tests
    )

    pass_fail_count_valid = (
        passed_tests
        + failed_tests
        == generated_tests
    )

    all_tests_passed = (
        generated_tests > 0
        and failed_tests == 0
        and passed_tests == generated_tests
    )

    # --------------------------------------------------------
    # Project methodology flags
    # --------------------------------------------------------

    # Hermes generated/selected the verification scenarios,
    # while deterministic Python logic produced expected
    # outputs and generated the executable Verilog testbench.

    hermes_directly_generated_verilog = False

    hermes_scenarios_executed = (
        validated_scenarios > 0
        and scenario_count_matches
    )

    deterministic_validation_used = True

    # Functional coverage belongs to Day 12.
    functional_coverage_measured = False

    # --------------------------------------------------------
    # DAY 11 STATUS
    # --------------------------------------------------------

    day11_pass = all(
        [
            validated_scenarios > 0,
            generated_tests > 0,
            scenario_count_matches,
            generated_count_matches_tb,
            pass_fail_count_valid,
            all_tests_passed,
            generated_testbench_exists,
            vcd_exists,
            hermes_scenarios_executed,
        ]
    )

    status = (
        "PASS"
        if day11_pass
        else "FAIL"
    )

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    summary = {
        "day": 11,

        "dut": detect_dut(
            validated_data
        ),

        "stage": (
            "Automatic Verilog testbench generation "
            "and Hermes-to-simulation integration"
        ),

        "validated_scenarios":
            validated_scenarios,

        "generated_tests":
            generated_tests,

        "generated_tests_in_testbench":
            generated_tests_from_tb,

        "passed_tests":
            passed_tests,

        "failed_tests":
            failed_tests,

        "scenario_count_matches_simulation":
            scenario_count_matches,

        "testbench_count_matches_simulation":
            generated_count_matches_tb,

        "pass_fail_count_valid":
            pass_fail_count_valid,

        "generated_testbench":
            str(
                GENERATED_TESTBENCH_FILE
            ),

        "generated_testbench_exists":
            generated_testbench_exists,

        "vcd_file":
            str(
                VCD_FILE
            ),

        "vcd_exists":
            vcd_exists,

        "expected_output_source":
            "deterministic_python_oracle",

        "hermes_directly_generated_verilog":
            hermes_directly_generated_verilog,

        "hermes_scenarios_executed":
            hermes_scenarios_executed,

        "deterministic_validation_used":
            deterministic_validation_used,

        "functional_coverage_measured":
            functional_coverage_measured,

        "next_stage":
            "DAY_12_FUNCTIONAL_COVERAGE_ANALYSIS",

        "status":
            status,
    }

    # --------------------------------------------------------
    # SAVE SUMMARY
    # --------------------------------------------------------

    OUTPUT_SUMMARY_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_SUMMARY_FILE.write_text(
        json.dumps(
            summary,
            indent=2,
        ),
        encoding="utf-8",
    )

    # Also show it in terminal.
    print(
        json.dumps(
            summary,
            indent=2,
        )
    )

    return (
        0
        if status == "PASS"
        else 1
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    raise SystemExit(
        main()
    )
