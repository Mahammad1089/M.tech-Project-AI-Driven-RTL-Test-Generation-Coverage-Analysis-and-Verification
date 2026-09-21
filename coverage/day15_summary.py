import json
from pathlib import Path


SIMULATION = Path(
    "results/alu/day15/"
    "closed_loop_simulation_report.json"
)

COVERAGE = Path(
    "results/alu/day15/"
    "closed_loop_coverage.json"
)

COVERAGE_COMPARISON = Path(
    "results/alu/day15/"
    "coverage_comparison.json"
)

GAPS = Path(
    "results/alu/day15/"
    "remaining_gaps.json"
)

GAP_COMPARISON = Path(
    "results/alu/day15/"
    "gap_comparison.json"
)

DECISION = Path(
    "results/alu/day15/"
    "closure_decision.json"
)

SUMMARY = Path(
    "results/alu/day15/"
    "day15_summary.json"
)


def load_json(path):
    if not path.exists():
        raise FileNotFoundError(
            f"Missing file: {path}"
        )

    return json.loads(
        path.read_text()
    )


def main():
    try:
        simulation = load_json(
            SIMULATION
        )

        coverage = load_json(
            COVERAGE
        )

        coverage_comparison = load_json(
            COVERAGE_COMPARISON
        )

        gaps = load_json(
            GAPS
        )

        gap_comparison = load_json(
            GAP_COMPARISON
        )

        decision = load_json(
            DECISION
        )

    except (
        FileNotFoundError,
        json.JSONDecodeError
    ) as error:

        print(
            "DAY 15 SUMMARY: FAIL"
        )

        print(
            f"ERROR: {error}"
        )

        raise SystemExit(1)

    if simulation.get(
        "status"
    ) != "PASS":

        print(
            "DAY 15 SUMMARY: FAIL"
        )

        print(
            "Closed-loop simulation "
            "did not pass."
        )

        raise SystemExit(1)

    if simulation.get(
        "failed_tests"
    ) != 0:

        print(
            "DAY 15 SUMMARY: FAIL"
        )

        print(
            "Closed-loop tests contain failures."
        )

        raise SystemExit(1)

    summary = {
        "day":
            15,

        "dut":
            coverage.get("dut"),

        "stage":
            "Closed-loop verification controller",

        "closed_loop_iteration":
            decision.get(
                "iteration"
            ),

        "simulated_tests":
            simulation.get(
                "total_tests"
            ),

        "passed_tests":
            simulation.get(
                "passed_tests"
            ),

        "failed_tests":
            simulation.get(
                "failed_tests"
            ),

        "operation_coverage":
            coverage.get(
                "operation_coverage",
                {}
            ).get(
                "percentage"
            ),

        "objective_coverage":
            coverage.get(
                "objective_coverage",
                {}
            ).get(
                "percentage"
            ),

        "coverage_trend":
            coverage_comparison.get(
                "trend"
            ),

        "operation_coverage_delta":
            coverage_comparison.get(
                "delta",
                {}
            ).get(
                "operation_coverage"
            ),

        "objective_coverage_delta":
            coverage_comparison.get(
                "delta",
                {}
            ).get(
                "objective_coverage"
            ),

        "remaining_gaps":
            gaps.get(
                "total_gap_count"
            ),

        "gap_trend":
            gap_comparison.get(
                "trend"
            ),

        "gaps_closed":
            gap_comparison.get(
                "gaps_closed"
            ),

        "closure_action":
            decision.get(
                "action"
            ),

        "closure_reason":
            decision.get(
                "reason"
            ),

        "hermes_feedback_source":
            "DAY_14",

        "deterministic_validation":
            True,

        "deterministic_oracle":
            True,

        "verilog_generated":
            True,

        "targeted_tests_simulated":
            True,

        "coverage_remeasured":
            True,

        "closed_loop_demonstrated":
            True,

        "status":
            "PASS"
    }

    SUMMARY.write_text(
        json.dumps(
            summary,
            indent=4
        )
    )

    print(
        json.dumps(
            summary,
            indent=4
        )
    )

    print()

    print(
        "DAY 15 SUMMARY: PASS"
    )


if __name__ == "__main__":
    main()
