#!/usr/bin/env python3

"""
DAY 28 - STEP 3
Constraint-Aware FSM Architecture Selection

Inputs:
    extensions/config/day28_selection_constraints.json
    extensions/results/day27/day27_efficiency_metrics.csv
    extensions/results/day28/day28_step2_validation.json

Outputs:
    extensions/results/day28/day28_architecture_rankings.csv
    extensions/results/day28/day28_architecture_selection.json
    extensions/results/day28/day28_architecture_selection.txt

This script:
    - Does not modify RTL.
    - Does not run synthesis.
    - Does not run simulation.
    - Does not claim Mealy/Moore functional equivalence.
"""

import csv
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

CONFIG_PATH = (
    ROOT / "extensions/config/day28_selection_constraints.json"
)

STEP2_PATH = (
    ROOT / "extensions/results/day28/day28_step2_validation.json"
)

OUTPUT_DIR = ROOT / "extensions/results/day28"

CSV_OUTPUT = OUTPUT_DIR / "day28_architecture_rankings.csv"
JSON_OUTPUT = OUTPUT_DIR / "day28_architecture_selection.json"
TEXT_OUTPUT = OUTPUT_DIR / "day28_architecture_selection.txt"

METRIC_COLUMNS = {
    "area": "area_um2",
    "power": "total_power_uw",
    "arrival_time": "data_arrival_ns",
}

METRIC_LABELS = {
    "area": "Area (um2)",
    "power": "Estimated power (uW)",
    "arrival_time": "Reported data arrival time (ns)",
}

TOLERANCE = 1e-12


def load_json(path):
    if not path.is_file():
        raise FileNotFoundError(f"Required file not found: {path}")

    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_csv(path):
    if not path.is_file():
        raise FileNotFoundError(f"Source CSV not found: {path}")

    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)

        required = {"configuration", *METRIC_COLUMNS.values()}
        missing = required - set(reader.fieldnames or [])

        if missing:
            raise ValueError(
                "Missing required CSV columns: "
                + ", ".join(sorted(missing))
            )

        records = []

        for line_number, row in enumerate(reader, start=2):
            name = (row.get("configuration") or "").strip()

            if not name:
                raise ValueError(
                    f"Empty configuration name at CSV line {line_number}"
                )

            record = {"configuration": name}

            for metric, column in METRIC_COLUMNS.items():
                raw = row.get(column)

                try:
                    value = float(raw)
                except (TypeError, ValueError) as exc:
                    raise ValueError(
                        f"Invalid {column} for {name}: {raw}"
                    ) from exc

                if not math.isfinite(value) or value < 0:
                    raise ValueError(
                        f"Non-finite or negative {column} for {name}"
                    )

                record[metric] = value

            records.append(record)

    names = [record["configuration"] for record in records]

    if len(names) != len(set(names)):
        raise ValueError("Duplicate configuration names in source CSV")

    return records


def identify_architecture(name):
    if name == "fsm_original_1011":
        return {
            "architecture": "original",
            "pattern": "1011",
            "overlap": None,
            "comparison_group": None,
        }

    match = re.fullmatch(
        r"(mealy|moore)_([01]+)_overlap_([01])",
        name,
    )

    if not match:
        raise ValueError(
            f"Unrecognized FSM configuration name: {name}"
        )

    architecture, pattern, overlap = match.groups()

    return {
        "architecture": architecture,
        "pattern": pattern,
        "overlap": int(overlap),
        "comparison_group": f"pattern_{pattern}_overlap_{overlap}",
    }


def satisfies_constraints(record, constraints):
    limits = {
        "area": constraints.get("maximum_area_um2"),
        "power": constraints.get("maximum_power_uw"),
        "arrival_time": constraints.get(
            "maximum_arrival_time_ns"
        ),
    }

    for metric, limit in limits.items():
        if limit is None:
            continue

        if (
            not isinstance(limit, (int, float))
            or isinstance(limit, bool)
            or not math.isfinite(limit)
            or limit < 0
        ):
            raise ValueError(
                f"Invalid hard constraint for {metric}: {limit}"
            )

        if record[metric] > limit + TOLERANCE:
            return False

    return True


def normalize_records(records):
    """
    Min-max normalization for minimization objectives.

    Normalization is calculated across all source records,
    preserving a common reference scale across scenarios.
    """

    bounds = {}

    for metric in METRIC_COLUMNS:
        values = [record[metric] for record in records]

        bounds[metric] = {
            "minimum": min(values),
            "maximum": max(values),
        }

    normalized = {}

    for record in records:
        name = record["configuration"]
        normalized[name] = {}

        for metric in METRIC_COLUMNS:
            minimum = bounds[metric]["minimum"]
            maximum = bounds[metric]["maximum"]

            if math.isclose(
                minimum,
                maximum,
                rel_tol=0.0,
                abs_tol=TOLERANCE,
            ):
                value = 0.0
            else:
                value = (
                    (record[metric] - minimum)
                    / (maximum - minimum)
                )

            normalized[name][metric] = value

    return normalized, bounds


def validate_scenarios(scenarios):
    if not scenarios:
        raise ValueError("No selection scenarios configured")

    for name, weights in scenarios.items():
        if set(weights) != set(METRIC_COLUMNS):
            raise ValueError(
                f"Invalid metric weights for scenario {name}"
            )

        values = list(weights.values())

        if any(
            not isinstance(value, (int, float))
            or isinstance(value, bool)
            or not math.isfinite(value)
            or value < 0
            for value in values
        ):
            raise ValueError(
                f"Invalid numerical weights for scenario {name}"
            )

        if not math.isclose(
            sum(values),
            1.0,
            rel_tol=0.0,
            abs_tol=1e-9,
        ):
            raise ValueError(
                f"Scenario weights do not sum to 1: {name}"
            )


def calculate_score(normalized_metrics, weights):
    return sum(
        normalized_metrics[metric] * weights[metric]
        for metric in METRIC_COLUMNS
    )


def rank_scenario(records, normalized, weights):
    ranked = []

    for record in records:
        if not record["eligible"]:
            continue

        name = record["configuration"]

        ranked.append({
            **record,
            "score": calculate_score(
                normalized[name],
                weights,
            ),
            "normalized": normalized[name],
        })

    ranked.sort(
        key=lambda item: (
            item["score"],
            item["area"],
            item["power"],
            item["arrival_time"],
            item["configuration"],
        )
    )

    for index, item in enumerate(ranked, start=1):
        item["rank"] = index

    return ranked


def find_controlled_comparisons(records, normalized, scenarios):
    groups = {}

    for record in records:
        group = record["comparison_group"]

        if group is None:
            continue

        groups.setdefault(group, []).append(record)

    comparisons = {}

    for group_name, members in sorted(groups.items()):
        architectures = {
            member["architecture"] for member in members
        }

        if architectures != {"mealy", "moore"} or len(members) != 2:
            raise ValueError(
                f"Incomplete controlled comparison: {group_name}"
            )

        comparisons[group_name] = {
            "configurations": [
                member["configuration"] for member in members
            ],
            "scenarios": {},
        }

        for scenario_name, weights in scenarios.items():
            eligible_members = [
                member for member in members if member["eligible"]
            ]

            if not eligible_members:
                comparisons[group_name]["scenarios"][
                    scenario_name
                ] = {
                    "status": "NO_ELIGIBLE_CONFIGURATION",
                    "winner": None,
                    "tied_winners": [],
                }
                continue

            scored = [
                {
                    "configuration": member["configuration"],
                    "score": calculate_score(
                        normalized[member["configuration"]],
                        weights,
                    ),
                }
                for member in eligible_members
            ]

            best_score = min(
                item["score"] for item in scored
            )

            winners = sorted(
                item["configuration"]
                for item in scored
                if math.isclose(
                    item["score"],
                    best_score,
                    rel_tol=0.0,
                    abs_tol=TOLERANCE,
                )
            )

            comparisons[group_name]["scenarios"][
                scenario_name
            ] = {
                "status": (
                    "TIE" if len(winners) > 1 else "SELECTED"
                ),
                "winner": (
                    winners[0] if len(winners) == 1 else None
                ),
                "tied_winners": winners,
                "best_score": best_score,
                "eligible_count": len(eligible_members),
            }

    return comparisons


def write_rankings_csv(scenario_rankings):
    fieldnames = [
        "scenario",
        "rank",
        "configuration",
        "architecture",
        "pattern",
        "overlap",
        "area_um2",
        "total_power_uw",
        "data_arrival_ns",
        "normalized_area",
        "normalized_power",
        "normalized_arrival_time",
        "weighted_score",
    ]

    with CSV_OUTPUT.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        for scenario, ranked in scenario_rankings.items():
            for item in ranked:
                writer.writerow({
                    "scenario": scenario,
                    "rank": item["rank"],
                    "configuration": item["configuration"],
                    "architecture": item["architecture"],
                    "pattern": item["pattern"],
                    "overlap": (
                        ""
                        if item["overlap"] is None
                        else item["overlap"]
                    ),
                    "area_um2": f"{item['area']:.6f}",
                    "total_power_uw": f"{item['power']:.6f}",
                    "data_arrival_ns": (
                        f"{item['arrival_time']:.6f}"
                    ),
                    "normalized_area": (
                        f"{item['normalized']['area']:.9f}"
                    ),
                    "normalized_power": (
                        f"{item['normalized']['power']:.9f}"
                    ),
                    "normalized_arrival_time": (
                        f"{item['normalized']['arrival_time']:.9f}"
                    ),
                    "weighted_score": f"{item['score']:.9f}",
                })


def write_text_report(
    records,
    scenarios,
    scenario_rankings,
    comparisons,
    bounds,
):
    lines = [
        "=" * 76,
        "DAY 28 - STEP 3",
        "CONSTRAINT-AWARE FSM ARCHITECTURE SELECTION",
        "=" * 76,
        "",
        f"Total configurations: {len(records)}",
        f"Eligible configurations: "
        f"{sum(item['eligible'] for item in records)}",
        f"Selection scenarios: {len(scenarios)}",
        "",
        "METRIC NORMALIZATION BOUNDS",
        "-" * 76,
    ]

    for metric, values in bounds.items():
        lines.append(
            f"{METRIC_LABELS[metric]}: "
            f"min={values['minimum']:.6f}, "
            f"max={values['maximum']:.6f}"
        )

    lines.extend([
        "",
        "GLOBAL SCENARIO RANKINGS",
        "-" * 76,
    ])

    for scenario, ranked in scenario_rankings.items():
        lines.extend([
            "",
            f"SCENARIO: {scenario}",
        ])

        if not ranked:
            lines.append("No eligible configurations")
            continue

        best_score = ranked[0]["score"]

        tied_best = [
            item["configuration"]
            for item in ranked
            if math.isclose(
                item["score"],
                best_score,
                rel_tol=0.0,
                abs_tol=TOLERANCE,
            )
        ]

        if len(tied_best) == 1:
            lines.append(
                f"BEST CONFIGURATION: {tied_best[0]}"
            )
        else:
            lines.append(
                "TIED BEST CONFIGURATIONS: "
                + ", ".join(tied_best)
            )

        for item in ranked:
            lines.append(
                f"  {item['rank']:2d}. "
                f"{item['configuration']:<28} "
                f"score={item['score']:.9f} "
                f"area={item['area']:.3f} "
                f"power={item['power']:.3f} "
                f"arrival={item['arrival_time']:.3f}"
            )

    lines.extend([
        "",
        "CONTROLLED MEALY VS MOORE COMPARISONS",
        "-" * 76,
    ])

    for group, details in comparisons.items():
        lines.append("")
        lines.append(f"GROUP: {group}")

        for scenario, result in details["scenarios"].items():
            if result["status"] == "SELECTED":
                decision = result["winner"]
            elif result["status"] == "TIE":
                decision = (
                    "TIE: " + ", ".join(result["tied_winners"])
                )
            else:
                decision = "NO ELIGIBLE CONFIGURATION"

            lines.append(
                f"  {scenario:<18}: {decision}"
            )

    lines.extend([
        "",
        "METHODOLOGY AND LIMITATIONS",
        "-" * 76,
        "1. Lower area, estimated power and arrival time are preferred.",
        "2. Scores use min-max normalization across all 13 source records.",
        "3. Hard constraints exclude ineligible configurations.",
        "4. Global rankings are numerical comparisons only.",
        "5. Controlled comparisons match sequence pattern and overlap.",
        "6. Mealy and Moore outputs may have different cycle semantics.",
        "7. Cross-architecture functional equivalence is not established.",
        "8. Power is based on assumed switching activity.",
        "9. Timing uses reported data arrival time, not full signoff.",
        "10. Results are pre-layout technology-mapped estimates.",
        "11. No new RTL, synthesis or simulation is performed.",
        "",
        "DAY 28 STEP 3: PASS",
        "",
    ])

    TEXT_OUTPUT.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


def main():
    print("=" * 72)
    print("DAY 28 - STEP 3")
    print("CONSTRAINT-AWARE FSM ARCHITECTURE SELECTION")
    print("=" * 72)

    config = load_json(CONFIG_PATH)
    step2 = load_json(STEP2_PATH)

    if step2.get("status") != "PASS":
        raise ValueError(
            "Day 28 Step 2 validation must be PASS"
        )

    if config.get("execution_day") != 28:
        raise ValueError("Incorrect execution day")

    source_path = ROOT / config["source_csv"]

    records = read_csv(source_path)

    expected_count = config.get(
        "expected_configurations",
        13,
    )

    if len(records) != expected_count:
        raise ValueError(
            f"Expected {expected_count} configurations, "
            f"found {len(records)}"
        )

    for record in records:
        record.update(
            identify_architecture(record["configuration"])
        )

        record["eligible"] = satisfies_constraints(
            record,
            config["hard_constraints"],
        )

    scenarios = config["selection_scenarios"]
    validate_scenarios(scenarios)

    normalized, bounds = normalize_records(records)

    scenario_rankings = {}

    for scenario_name, weights in scenarios.items():
        scenario_rankings[scenario_name] = rank_scenario(
            records,
            normalized,
            weights,
        )

    comparisons = find_controlled_comparisons(
        records,
        normalized,
        scenarios,
    )

    if len(comparisons) != 6:
        raise ValueError(
            f"Expected 6 controlled groups, "
            f"found {len(comparisons)}"
        )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    write_rankings_csv(scenario_rankings)

    global_winners = {}

    for scenario, ranked in scenario_rankings.items():
        if not ranked:
            global_winners[scenario] = {
                "status": "NO_ELIGIBLE_CONFIGURATION",
                "winner": None,
                "tied_winners": [],
            }
            continue

        best_score = ranked[0]["score"]

        winners = sorted(
            item["configuration"]
            for item in ranked
            if math.isclose(
                item["score"],
                best_score,
                rel_tol=0.0,
                abs_tol=TOLERANCE,
            )
        )

        global_winners[scenario] = {
            "status": (
                "TIE" if len(winners) > 1 else "SELECTED"
            ),
            "winner": (
                winners[0] if len(winners) == 1 else None
            ),
            "tied_winners": winners,
            "best_score": best_score,
        }

    report = {
        "day": 28,
        "step": 3,
        "status": "PASS",
        "source_csv": config["source_csv"],
        "configuration_count": len(records),
        "eligible_count": sum(
            record["eligible"] for record in records
        ),
        "scenario_count": len(scenarios),
        "controlled_group_count": len(comparisons),
        "metric_bounds": bounds,
        "hard_constraints": config["hard_constraints"],
        "scenario_weights": scenarios,
        "global_winners": global_winners,
        "controlled_comparisons": comparisons,
        "configuration_records": records,
        "methodology": {
            "score_method": "min_max_normalized_weighted_sum",
            "normalization_population": "all_13_source_records",
            "tie_tolerance": TOLERANCE,
            "functional_equivalence_established": False,
            "rtl_modified": False,
            "synthesis_rerun": False,
            "simulation_rerun": False,
        },
        "limitations": [
            "Pre-layout technology-mapped estimates",
            "Assumed switching activity for power",
            "Reported data arrival time is a timing proxy",
            "Different FSM variants may have different cycle semantics",
        ],
    }

    JSON_OUTPUT.write_text(
        json.dumps(
            report,
            indent=2,
            allow_nan=False,
        ) + "\n",
        encoding="utf-8",
    )

    write_text_report(
        records,
        scenarios,
        scenario_rankings,
        comparisons,
        bounds,
    )

    print()
    print("========== GLOBAL SCENARIO RESULTS ==========")

    for scenario, result in global_winners.items():
        if result["status"] == "SELECTED":
            display = result["winner"]
        elif result["status"] == "TIE":
            display = ", ".join(result["tied_winners"])
        else:
            display = "NONE"

        print(f"{scenario}: {display}")

    print()
    print("========== GENERATED REPORTS ==========")
    print(CSV_OUTPUT.relative_to(ROOT))
    print(JSON_OUTPUT.relative_to(ROOT))
    print(TEXT_OUTPUT.relative_to(ROOT))

    print()
    print("CONFIGURATIONS ANALYZED:", len(records))
    print("CONTROLLED COMPARISON GROUPS:", len(comparisons))
    print("SELECTION SCENARIOS:", len(scenarios))
    print("DAY 28 STEP 3: PASS")


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
        print()
        print(f"DAY 28 STEP 3: FAIL - {exc}")
        sys.exit(1)
