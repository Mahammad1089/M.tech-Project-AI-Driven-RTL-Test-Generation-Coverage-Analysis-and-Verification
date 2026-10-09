#!/usr/bin/env python3

"""
DAY 28 - STEP 4
FSM Constraint Sensitivity and Architecture Trade-off Analysis

Uses existing Day 28 Step 3 evidence.
Does not modify RTL, rerun simulation, or rerun synthesis.

Outputs:
    day28_constraint_sensitivity.csv
    day28_constraint_sensitivity.json
    day28_constraint_sensitivity.txt
"""

import csv
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "extensions/results/day28"

STEP3 = OUT / "day28_architecture_selection.json"

CSV_OUT = OUT / "day28_constraint_sensitivity.csv"
JSON_OUT = OUT / "day28_constraint_sensitivity.json"
TXT_OUT = OUT / "day28_constraint_sensitivity.txt"

METRICS = ("area", "power", "arrival_time")
TOL = 1e-12


def load_step3():
    if not STEP3.is_file():
        raise FileNotFoundError(f"Missing Step 3 report: {STEP3}")

    with STEP3.open(encoding="utf-8") as handle:
        data = json.load(handle)

    if data.get("status") != "PASS":
        raise ValueError("Day 28 Step 3 is not PASS")

    records = data.get("configuration_records", [])
    weights = data.get("scenario_weights", {})
    bounds = data.get("metric_bounds", {})

    if len(records) != 13:
        raise ValueError("Expected 13 configuration records")

    if len(weights) != 4:
        raise ValueError("Expected four optimization scenarios")

    if set(bounds) != set(METRICS):
        raise ValueError("Metric bounds are incomplete")

    names = set()

    for record in records:
        name = record.get("configuration")

        if not name or name in names:
            raise ValueError("Missing or duplicate configuration")

        names.add(name)

        for metric in METRICS:
            value = record.get(metric)

            if (
                not isinstance(value, (int, float))
                or isinstance(value, bool)
                or not math.isfinite(value)
                or value < 0
            ):
                raise ValueError(
                    f"Invalid {metric} for {name}"
                )

    return data, records, weights, bounds


def normalized_value(value, minimum, maximum):
    if math.isclose(
        minimum, maximum,
        rel_tol=0,
        abs_tol=TOL
    ):
        return 0.0

    return (value - minimum) / (maximum - minimum)


def score(record, weights, bounds):
    total = 0.0

    for metric in METRICS:
        value = normalized_value(
            record[metric],
            bounds[metric]["minimum"],
            bounds[metric]["maximum"],
        )

        total += value * weights[metric]

    return total


def eligible(record, limits):
    for metric in METRICS:
        limit = limits.get(metric)

        if limit is not None and record[metric] > limit + TOL:
            return False

    return True


def build_cases(records, original_limits):
    maxima = {
        metric: max(record[metric] for record in records)
        for metric in METRICS
    }

    # Original limits are taken from Step 3.
    cases = [
        {
            "case": "original_constraints",
            "description": "Original Day 28 configuration",
            "limits": dict(original_limits),
        }
    ]

    definitions = [
        ("area_95pct", "area", 0.95),
        ("area_85pct", "area", 0.85),
        ("power_95pct", "power", 0.95),
        ("power_85pct", "power", 0.85),
        ("arrival_95pct", "arrival_time", 0.95),
        ("arrival_85pct", "arrival_time", 0.85),
    ]

    for name, metric, factor in definitions:
        cases.append({
            "case": name,
            "description": (
                f"{metric} <= {factor:.0%} of observed maximum"
            ),
            "limits": {
                "area": None,
                "power": None,
                "arrival_time": None,
                metric: maxima[metric] * factor,
            },
        })

    cases.append({
        "case": "combined_90pct",
        "description": (
            "All three metrics <= 90% of observed maxima"
        ),
        "limits": {
            metric: maxima[metric] * 0.90
            for metric in METRICS
        },
    })

    return cases


def evaluate_case(case, records, scenarios, bounds):
    candidates = [
        record
        for record in records
        if eligible(record, case["limits"])
    ]

    selections = {}

    for scenario_name, weights in scenarios.items():
        scored = sorted(
            (
                {
                    "configuration": record["configuration"],
                    "architecture": record["architecture"],
                    "score": score(record, weights, bounds),
                }
                for record in candidates
            ),
            key=lambda item: (
                item["score"],
                item["configuration"],
            ),
        )

        if not scored:
            selections[scenario_name] = {
                "status": "NO_ELIGIBLE_CONFIGURATION",
                "winner": None,
                "tied_winners": [],
                "score": None,
            }
            continue

        best = scored[0]["score"]

        tied = sorted(
            item["configuration"]
            for item in scored
            if math.isclose(
                item["score"],
                best,
                rel_tol=0,
                abs_tol=TOL,
            )
        )

        selections[scenario_name] = {
            "status": (
                "TIE" if len(tied) > 1 else "SELECTED"
            ),
            "winner": tied[0] if len(tied) == 1 else None,
            "tied_winners": tied,
            "score": best,
        }

    return {
        "case": case["case"],
        "description": case["description"],
        "limits": case["limits"],
        "eligible_count": len(candidates),
        "excluded_count": len(records) - len(candidates),
        "eligible_configurations": sorted(
            record["configuration"] for record in candidates
        ),
        "selections": selections,
    }


def write_csv(results, scenario_names):
    fields = [
        "constraint_case",
        "scenario",
        "eligible_count",
        "excluded_count",
        "area_limit_um2",
        "power_limit_uw",
        "arrival_limit_ns",
        "selection_status",
        "selected_configuration",
        "tied_winners",
        "weighted_score",
    ]

    with CSV_OUT.open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(
            handle, fieldnames=fields
        )

        writer.writeheader()

        for result in results:
            for scenario in scenario_names:
                decision = result["selections"][scenario]

                writer.writerow({
                    "constraint_case": result["case"],
                    "scenario": scenario,
                    "eligible_count": result["eligible_count"],
                    "excluded_count": result["excluded_count"],
                    "area_limit_um2": (
                        result["limits"]["area"]
                    ),
                    "power_limit_uw": (
                        result["limits"]["power"]
                    ),
                    "arrival_limit_ns": (
                        result["limits"]["arrival_time"]
                    ),
                    "selection_status": decision["status"],
                    "selected_configuration": (
                        decision["winner"] or ""
                    ),
                    "tied_winners": ";".join(
                        decision["tied_winners"]
                    ),
                    "weighted_score": (
                        ""
                        if decision["score"] is None
                        else f"{decision['score']:.9f}"
                    ),
                })


def write_text(results, scenario_names):
    lines = [
        "=" * 74,
        "DAY 28 - STEP 4",
        "CONSTRAINT SENSITIVITY AND FSM TRADE-OFF ANALYSIS",
        "=" * 74,
        "",
        f"Constraint cases: {len(results)}",
        f"Optimization scenarios: {len(scenario_names)}",
        "",
    ]

    for result in results:
        lines.extend([
            "-" * 74,
            f"CASE: {result['case']}",
            f"DESCRIPTION: {result['description']}",
            f"ELIGIBLE: {result['eligible_count']}",
            f"EXCLUDED: {result['excluded_count']}",
        ])

        for metric in METRICS:
            limit = result["limits"].get(metric)

            lines.append(
                f"{metric} limit: "
                + (
                    "UNRESTRICTED"
                    if limit is None
                    else f"{limit:.6f}"
                )
            )

        for scenario in scenario_names:
            decision = result["selections"][scenario]

            if decision["status"] == "SELECTED":
                display = decision["winner"]
            elif decision["status"] == "TIE":
                display = (
                    "TIE: "
                    + ", ".join(decision["tied_winners"])
                )
            else:
                display = "NO ELIGIBLE CONFIGURATION"

            lines.append(f"{scenario}: {display}")

        lines.append("")

    lines.extend([
        "METHODOLOGY AND LIMITATIONS",
        "-" * 74,
        "1. Uses the existing 13 Day 27 FSM PPA records.",
        "2. Uses the same min-max bounds as Day 28 Step 3.",
        "3. Lower weighted score is preferred.",
        "4. Hard constraints filter candidates before ranking.",
        "5. Percentage limits are fractions of observed maxima.",
        "6. These limits are experimental, not signoff targets.",
        "7. Global comparisons may mix different FSM behaviors.",
        "8. Cross-architecture functional equivalence is not proven.",
        "9. Power is estimated using assumed switching activity.",
        "10. Timing is reported data arrival time.",
        "11. No RTL changes or EDA reruns are performed.",
        "",
        "DAY 28 STEP 4: PASS",
        "",
    ])

    TXT_OUT.write_text(
        "\n".join(lines), encoding="utf-8"
    )


def main():
    print("=" * 70)
    print("DAY 28 - STEP 4")
    print("FSM CONSTRAINT SENSITIVITY ANALYSIS")
    print("=" * 70)

    data, records, scenarios, bounds = load_step3()

    configured = data.get("hard_constraints", {})

    original_limits = {
        "area": configured.get("maximum_area_um2"),
        "power": configured.get("maximum_power_uw"),
        "arrival_time": configured.get(
            "maximum_arrival_time_ns"
        ),
    }

    cases = build_cases(records, original_limits)

    results = [
        evaluate_case(case, records, scenarios, bounds)
        for case in cases
    ]

    if len(results) != 8:
        raise ValueError("Expected eight constraint cases")

    OUT.mkdir(parents=True, exist_ok=True)

    write_csv(results, list(scenarios))
    write_text(results, list(scenarios))

    report = {
        "day": 28,
        "step": 4,
        "status": "PASS",
        "source": str(STEP3.relative_to(ROOT)),
        "configuration_count": len(records),
        "constraint_case_count": len(results),
        "scenario_count": len(scenarios),
        "results": results,
        "methodology": {
            "normalization": "Day 28 Step 3 fixed bounds",
            "constraint_reference": "observed metric maxima",
            "rtl_modified": False,
            "synthesis_rerun": False,
            "simulation_rerun": False,
            "functional_equivalence_proven": False,
        },
    }

    JSON_OUT.write_text(
        json.dumps(
            report, indent=2, allow_nan=False
        ) + "\n",
        encoding="utf-8",
    )

    print()
    print("========== SENSITIVITY SUMMARY ==========")

    for result in results:
        print(
            f"{result['case']:<23} "
            f"eligible={result['eligible_count']:2d} "
            f"excluded={result['excluded_count']:2d}"
        )

    print()
    print("========== GENERATED REPORTS ==========")

    for path in (CSV_OUT, JSON_OUT, TXT_OUT):
        print(path.relative_to(ROOT))

    print()
    print("CONFIGURATIONS ANALYZED:", len(records))
    print("CONSTRAINT CASES:", len(results))
    print("SELECTION SCENARIOS:", len(scenarios))
    print("DAY 28 STEP 4: PASS")


if __name__ == "__main__":
    try:
        main()
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        json.JSONDecodeError,
    ) as exc:
        print(f"DAY 28 STEP 4: FAIL - {exc}")
        sys.exit(1)
