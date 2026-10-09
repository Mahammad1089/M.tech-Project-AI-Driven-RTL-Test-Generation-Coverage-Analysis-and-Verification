#!/usr/bin/env python3
"""Day 29 Step 3: independent FSM constraint-sensitivity audit."""

import csv
import json
import math
import sys
from collections import Counter
from pathlib import Path

SOURCE = Path("extensions/results/day27/day27_efficiency_metrics.csv")
CONFIG = Path("extensions/results/day28/day28_architecture_selection.json")
SAVED = Path("extensions/results/day28/day28_constraint_sensitivity.csv")
OUT = Path("extensions/results/day29")

SCENARIOS = (
    "area_priority",
    "power_priority",
    "timing_priority",
    "balanced",
)

METRICS = {
    "area": "area_um2",
    "power": "total_power_uw",
    "arrival_time": "data_arrival_ns",
}

LIMITS = {
    "area": "area_limit_um2",
    "power": "power_limit_uw",
    "arrival_time": "arrival_limit_ns",
}

TOL = 1e-6


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError(f"Missing CSV header: {path}")
        return list(reader), set(reader.fieldnames)


def require_columns(actual, expected, label):
    missing = sorted(set(expected) - actual)
    if missing:
        raise ValueError(f"{label}: missing columns {missing}")


def number(value, label):
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{label}: non-finite value")
    return result


def optional_number(value, label):
    if value is None or str(value).strip() == "":
        return None
    return number(value, label)


def close(a, b):
    return math.isclose(a, b, rel_tol=0.0, abs_tol=TOL)


def normalized(value, low, high):
    if close(low, high):
        return 0.0
    return (value - low) / (high - low)


def audit():
    OUT.mkdir(parents=True, exist_ok=True)

    source_rows, source_columns = read_csv(SOURCE)
    saved_rows, saved_columns = read_csv(SAVED)

    require_columns(
        source_columns,
        ["configuration", *METRICS.values()],
        "Day 27 source",
    )

    require_columns(
        saved_columns,
        [
            "constraint_case",
            "scenario",
            "eligible_count",
            "excluded_count",
            *LIMITS.values(),
            "selection_status",
            "selected_configuration",
            "tied_winners",
            "weighted_score",
        ],
        "Day 28 sensitivity",
    )

    with CONFIG.open(encoding="utf-8") as handle:
        config = json.load(handle)

    if config.get("status") != "PASS":
        raise ValueError("Day 28 architecture-selection status is not PASS")

    weights = config["scenario_weights"]
    if set(weights) != set(SCENARIOS):
        raise ValueError("Unexpected scenario names in configuration")

    if len(source_rows) != 13:
        raise ValueError(
            f"Expected 13 source configurations; got {len(source_rows)}"
        )

    records = {}
    for row in source_rows:
        name = row["configuration"].strip()
        if not name or name in records:
            raise ValueError(f"Duplicate or empty configuration: {name!r}")

        records[name] = {
            metric: number(row[column], f"{name}.{column}")
            for metric, column in METRICS.items()
        }

    bounds = {}
    for metric in METRICS:
        values = [r[metric] for r in records.values()]
        bounds[metric] = (min(values), max(values))

    for scenario in SCENARIOS:
        w = weights[scenario]
        if any(number(w[m], f"{scenario}.{m}") < 0 for m in METRICS):
            raise ValueError(f"Negative weight: {scenario}")

        total = sum(number(w[m], f"{scenario}.{m}") for m in METRICS)
        if not close(total, 1.0):
            raise ValueError(f"Weights do not sum to 1: {scenario}")

    groups = {}
    for row in saved_rows:
        case = row["constraint_case"].strip()
        scenario = row["scenario"].strip()
        key = (case, scenario)

        if key in groups:
            raise ValueError(f"Duplicate decision: {key}")
        if scenario not in SCENARIOS:
            raise ValueError(f"Unknown scenario: {scenario}")

        groups[key] = row

    cases = sorted({case for case, _ in groups})

    if len(cases) != 8:
        raise ValueError(f"Expected 8 constraint cases; got {len(cases)}")

    if len(groups) != 32:
        raise ValueError(f"Expected 32 decisions; got {len(groups)}")

    for case in cases:
        for scenario in SCENARIOS:
            if (case, scenario) not in groups:
                raise ValueError(f"Missing decision: {case}/{scenario}")

    findings = []
    passed = 0
    failed = 0

    def check(case, scenario, field, expected, observed, valid):
        nonlocal passed, failed

        status = "PASS" if valid else "FAIL"
        if valid:
            passed += 1
        else:
            failed += 1

        findings.append({
            "constraint_case": case,
            "scenario": scenario,
            "field": field,
            "expected": str(expected),
            "observed": str(observed),
            "status": status,
        })

    for case in cases:
        limits_by_scenario = []

        for scenario in SCENARIOS:
            row = groups[(case, scenario)]

            limits = {
                metric: optional_number(
                    row[column],
                    f"{case}.{scenario}.{column}",
                )
                for metric, column in LIMITS.items()
            }

            limits_by_scenario.append(limits)

            eligible = []
            for name, metrics in records.items():
                if all(
                    limits[m] is None
                    or metrics[m] <= limits[m] + TOL
                    for m in METRICS
                ):
                    eligible.append(name)

            check(
                case, scenario, "eligible_count",
                len(eligible), row["eligible_count"],
                len(eligible) == int(row["eligible_count"]),
            )

            excluded = len(records) - len(eligible)
            check(
                case, scenario, "excluded_count",
                excluded, row["excluded_count"],
                excluded == int(row["excluded_count"]),
            )

            if not eligible:
                check(
                    case, scenario, "selection_status",
                    "NO_ELIGIBLE", row["selection_status"],
                    row["selection_status"] in (
                        "NO_ELIGIBLE",
                        "NO_ELIGIBLE_CONFIGURATIONS",
                    ),
                )
                continue

            scores = {}
            for name in eligible:
                scores[name] = sum(
                    float(weights[scenario][metric])
                    * normalized(
                        records[name][metric],
                        *bounds[metric],
                    )
                    for metric in METRICS
                )

            best_score = min(scores.values())
            winners = sorted(
                name for name, score in scores.items()
                if close(score, best_score)
            )

            selected = row["selected_configuration"].strip()
            saved_ties = {
                item.strip()
                for item in row["tied_winners"].split(",")
                if item.strip()
            }

            check(
                case, scenario, "selection_status",
                "SELECTED", row["selection_status"],
                row["selection_status"] == "SELECTED",
            )

            check(
                case, scenario, "selected_configuration",
                winners, selected,
                selected in winners,
            )

            check(
                case, scenario, "tied_winners",
                winners, sorted(saved_ties),
                set(winners) == saved_ties,
            )

            saved_score = number(
                row["weighted_score"],
                f"{case}.{scenario}.weighted_score",
            )

            check(
                case, scenario, "weighted_score",
                f"{best_score:.12f}",
                f"{saved_score:.12f}",
                close(best_score, saved_score),
            )

        # Constraint limits must be identical for all four scenarios
        # within the same constraint case.
        first_limits = limits_by_scenario[0]
        for index, other in enumerate(limits_by_scenario[1:], start=1):
            check(
                case,
                SCENARIOS[index],
                "constraint_limits_consistent",
                first_limits,
                other,
                first_limits == other,
            )

    status = "PASS" if failed == 0 else "FAIL"

    csv_path = OUT / "day29_independent_sensitivity_audit.csv"
    json_path = OUT / "day29_independent_sensitivity_audit.json"
    txt_path = OUT / "day29_independent_sensitivity_audit.txt"

    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "constraint_case",
                "scenario",
                "field",
                "expected",
                "observed",
                "status",
            ],
        )
        writer.writeheader()
        writer.writerows(findings)

    summary = {
        "day": 29,
        "step": 3,
        "status": status,
        "source_metrics": str(SOURCE),
        "source_constraints": str(SAVED),
        "source_scenarios": str(CONFIG),
        "configuration_count": len(records),
        "constraint_case_count": len(cases),
        "scenario_count": len(SCENARIOS),
        "decision_count": len(groups),
        "passed_checks": passed,
        "failed_checks": failed,
        "failed_findings": [
            finding for finding in findings
            if finding["status"] == "FAIL"
        ],
        "methodology": {
            "normalization": "min-max over all 13 source configurations",
            "objective": "minimize weighted normalized metrics",
            "normalization_recomputed": True,
            "rtl_modified": False,
            "synthesis_rerun": False,
            "simulation_rerun": False,
        },
    }

    json_path.write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )

    lines = [
        "=" * 70,
        "DAY 29 STEP 3 - INDEPENDENT CONSTRAINT-SENSITIVITY AUDIT",
        "=" * 70,
        f"Configurations: {len(records)}",
        f"Constraint cases: {len(cases)}",
        f"Scenarios: {len(SCENARIOS)}",
        f"Decisions: {len(groups)}",
        f"Passed checks: {passed}",
        f"Failed checks: {failed}",
        f"FINAL RESULT: {status}",
        "",
        "FAILED FINDINGS",
        "-" * 70,
    ]

    failures = summary["failed_findings"]
    if failures:
        for item in failures:
            lines.append(
                f"{item['constraint_case']} / {item['scenario']} / "
                f"{item['field']}: expected={item['expected']}, "
                f"observed={item['observed']}"
            )
    else:
        lines.append("None")

    lines += [
        "",
        "LIMITATIONS",
        "-" * 70,
        "Uses existing Day 27 and Day 28 evidence.",
        "No RTL, synthesis, STA or simulation rerun.",
        "Power is estimated using assumed switching activity.",
        "Arrival time is not post-layout signoff timing.",
        "Numerical ranking does not establish functional equivalence.",
        "",
        f"DAY 29 STEP 3: {status}",
    ]

    txt_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("\n".join(lines))
    print("\nGENERATED REPORTS:")
    print(csv_path)
    print(json_path)
    print(txt_path)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    try:
        sys.exit(audit())
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"DAY 29 STEP 3: FAIL - {exc}", file=sys.stderr)
        sys.exit(1)
