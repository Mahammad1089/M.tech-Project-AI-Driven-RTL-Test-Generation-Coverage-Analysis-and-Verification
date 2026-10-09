#!/usr/bin/env python3
"""
Day 29 Step 2 - Independent FSM Architecture Ranking Audit

Recomputes four scenario rankings from Day 27 source PPA
metrics and compares them with Day 28 saved rankings.

No RTL modification, simulation, synthesis or STA rerun.
"""

import csv
import json
import math
import sys
from pathlib import Path

ROOT = Path("extensions/results")
SOURCE = ROOT / "day27/day27_efficiency_metrics.csv"
RANKINGS = ROOT / "day28/day28_architecture_rankings.csv"
SELECTION = ROOT / "day28/day28_architecture_selection.json"
BASELINE = ROOT / "day29/day29_baseline_validation.json"
OUT = ROOT / "day29"

OUT_CSV = OUT / "day29_independent_ranking_audit.csv"
OUT_JSON = OUT / "day29_independent_ranking_audit.json"
OUT_TXT = OUT / "day29_independent_ranking_audit.txt"

METRICS = {
    "area": "area_um2",
    "power": "total_power_uw",
    "arrival_time": "data_arrival_ns",
}

SCENARIOS = (
    "area_priority",
    "power_priority",
    "timing_priority",
    "balanced",
)

TOLERANCE = 1e-9
EXPECTED_CONFIGURATIONS = 13

checks = []
errors = []


def check(condition, description):
    condition = bool(condition)
    checks.append({
        "description": description,
        "status": "PASS" if condition else "FAIL",
    })
    print(
        f"[{'PASS' if condition else 'FAIL'}] {description}"
    )
    if not condition:
        errors.append(description)
    return condition


def load_json(path):
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_csv(path):
    with path.open(
        "r", encoding="utf-8", newline=""
    ) as file:
        reader = csv.DictReader(file)
        if not reader.fieldnames:
            raise ValueError(f"No CSV header: {path}")
        return list(reader), reader.fieldnames


def finite_number(value, description):
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"Nonfinite {description}: {value}")
    return number


def normalize(value, minimum, maximum):
    span = maximum - minimum
    if abs(span) <= 1e-15:
        return 0.0
    return (value - minimum) / span


def close(a, b, tolerance=TOLERANCE):
    return math.isclose(
        float(a), float(b),
        rel_tol=tolerance,
        abs_tol=tolerance,
    )


def write_reports(rows, details):
    OUT.mkdir(parents=True, exist_ok=True)

    fields = [
        "scenario",
        "rank",
        "configuration",
        "independent_score",
        "saved_score",
        "score_difference",
        "independent_normalized_area",
        "independent_normalized_power",
        "independent_normalized_arrival_time",
        "score_match",
        "rank_match",
    ]

    with OUT_CSV.open(
        "w", newline="", encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    with OUT_JSON.open("w", encoding="utf-8") as file:
        json.dump(details, file, indent=2)
        file.write("\n")

    lines = [
        "DAY 29 - STEP 2",
        "INDEPENDENT FSM ARCHITECTURE RANKING AUDIT",
        "=" * 66,
        f"Status: {details['status']}",
        f"Passed checks: {details['passed_checks']}",
        f"Failed checks: {details['failed_checks']}",
        f"Configurations: {details.get('configuration_count', 0)}",
        f"Ranking records: {details.get('ranking_count', 0)}",
        "",
        "GLOBAL SCENARIO WINNERS",
    ]

    for scenario, item in details.get(
        "scenario_results", {}
    ).items():
        lines.extend([
            f"{scenario}:",
            f"  Independently calculated: {item['independent_winner']}",
            f"  Saved Day 28 winner:     {item['saved_winner']}",
            f"  Match: {item['winner_match']}",
        ])

    lines.extend(["", "CHECKS"])

    for item in checks:
        lines.append(
            f"[{item['status']}] {item['description']}"
        )

    lines.extend([
        "",
        "METHODOLOGY",
        "Recalculated from Day 27 efficiency CSV.",
        "Min-max normalization across all 13 configurations.",
        "Weighted sum with Day 28 saved scenario weights.",
        "Full ranking compared against Day 28 ranking CSV.",
        "No RTL or EDA reruns performed.",
        "Power is estimated using assumed activity.",
        "Timing is reported arrival time, not signoff delay.",
        "Functional equivalence is not established.",
        "",
        f"DAY 29 STEP 2: {details['status']}",
    ])

    OUT_TXT.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def main():
    print("=" * 72)
    print("DAY 29 - STEP 2")
    print("INDEPENDENT FSM ARCHITECTURE RANKING AUDIT")
    print("=" * 72)

    for path in (SOURCE, RANKINGS, SELECTION, BASELINE):
        check(path.is_file(), f"Source exists: {path.name}")

    if errors:
        raise ValueError("Required source files are missing")

    baseline = load_json(BASELINE)
    selection = load_json(SELECTION)
    source_rows, source_fields = load_csv(SOURCE)
    saved_rows, saved_fields = load_csv(RANKINGS)

    check(
        baseline.get("status") == "PASS",
        "Day 29 Step 1 baseline status PASS",
    )
    check(
        selection.get("status") == "PASS",
        "Day 28 selection status PASS",
    )

    check(
        len(source_rows) == EXPECTED_CONFIGURATIONS,
        "Exactly 13 source configurations",
    )
    check(
        len(saved_rows) ==
        EXPECTED_CONFIGURATIONS * len(SCENARIOS),
        "Exactly 52 saved ranking records",
    )

    required_source = ["configuration", *METRICS.values()]
    required_ranking = [
        "scenario", "rank", "configuration",
        "weighted_score",
        "normalized_area", "normalized_power",
        "normalized_arrival_time",
    ]

    check(
        all(name in source_fields for name in required_source),
        "Required Day 27 source columns present",
    )
    check(
        all(name in saved_fields for name in required_ranking),
        "Required Day 28 ranking columns present",
    )

    methodology = selection.get("methodology", {})
    check(
        methodology.get("score_method") ==
        "min_max_normalized_weighted_sum",
        "Expected scoring method",
    )
    check(
        methodology.get("normalization_population") ==
        "all_13_source_records",
        "Expected normalization population",
    )

    hard = selection.get("hard_constraints", {})
    check(
        all(
            hard.get(key) is None
            for key in (
                "maximum_area_um2",
                "maximum_power_uw",
                "maximum_arrival_time_ns",
            )
        ),
        "No hard constraints in baseline selection",
    )

    if errors:
        raise ValueError(
            "Source structure or methodology mismatch"
        )

    source = {}
    for row in source_rows:
        name = row["configuration"].strip()
        if not name or name in source:
            raise ValueError(
                f"Duplicate/empty configuration: {name}"
            )
        source[name] = {
            metric: finite_number(
                row[column], f"{name}.{column}"
            )
            for metric, column in METRICS.items()
        }

    minima = {
        metric: min(
            row[metric] for row in source.values()
        )
        for metric in METRICS
    }
    maxima = {
        metric: max(
            row[metric] for row in source.values()
        )
        for metric in METRICS
    }

    normalized = {
        name: {
            metric: normalize(
                values[metric],
                minima[metric],
                maxima[metric],
            )
            for metric in METRICS
        }
        for name, values in source.items()
    }

    saved_by_scenario = {name: [] for name in SCENARIOS}

    for row in saved_rows:
        scenario = row["scenario"].strip()
        if scenario not in saved_by_scenario:
            raise ValueError(
                f"Unknown scenario: {scenario}"
            )
        saved_by_scenario[scenario].append(row)

    weights = selection["scenario_weights"]
    global_winners = selection["global_winners"]
    tolerance = finite_number(
        methodology.get("tie_tolerance", 1e-12),
        "tie_tolerance",
    )

    output_rows = []
    scenario_results = {}

    for scenario in SCENARIOS:
        if scenario not in weights:
            raise ValueError(
                f"Missing weights: {scenario}"
            )

        w = weights[scenario]
        check(
            all(
                metric in w and
                math.isfinite(float(w[metric])) and
                float(w[metric]) >= 0
                for metric in METRICS
            ),
            f"Valid weights: {scenario}",
        )
        check(
            close(
                sum(float(w[m]) for m in METRICS),
                1.0,
            ),
            f"Weights sum to one: {scenario}",
        )

        scores = {}
        for name, values in normalized.items():
            scores[name] = sum(
                float(w[metric]) * values[metric]
                for metric in METRICS
            )

        # Sort by score and then by configuration name
        # for deterministic display order.
        independent_order = sorted(
            scores,
            key=lambda name: (scores[name], name),
        )

        saved = saved_by_scenario[scenario]
        saved_map = {
            row["configuration"].strip(): row
            for row in saved
        }

        check(
            len(saved) == EXPECTED_CONFIGURATIONS
            and len(saved_map) == EXPECTED_CONFIGURATIONS
            and set(saved_map) == set(source),
            f"Complete unique ranking set: {scenario}",
        )

        if set(saved_map) != set(source):
            raise ValueError(
                f"Ranking configuration mismatch: {scenario}"
            )

        score_matches = True
        normalization_matches = True
        rank_matches = True

        # Rank ties are audited by score ordering rather
        # than requiring a particular alphabetical tie order.
        saved_order = sorted(
            saved,
            key=lambda row: int(row["rank"]),
        )

        saved_ranks = [
            int(row["rank"])
            for row in saved_order
        ]

        check(
            saved_ranks ==
            list(range(1, EXPECTED_CONFIGURATIONS + 1)),
            f"Consecutive saved ranks: {scenario}",
        )

        for index, name in enumerate(independent_order, 1):
            saved_row = saved_map[name]
            saved_score = finite_number(
                saved_row["weighted_score"],
                f"{scenario}.{name}.weighted_score",
            )

            score_ok = close(scores[name], saved_score)
            score_matches &= score_ok

            normalization_ok = all(
                close(
                    normalized[name][metric],
                    saved_row[f"normalized_{metric}"],
                )
                for metric in METRICS
            )
            normalization_matches &= normalization_ok

            # A saved ranking is valid when its scores are
            # nondecreasing and its reported values agree.
            # Equal-score configurations may appear in
            # either order.
            saved_rank = int(saved_row["rank"])

            output_rows.append({
                "scenario": scenario,
                "rank": index,
                "configuration": name,
                "independent_score": f"{scores[name]:.15g}",
                "saved_score": f"{saved_score:.15g}",
                "score_difference": (
                    f"{abs(scores[name]-saved_score):.15g}"
                ),
                "independent_normalized_area": (
                    f"{normalized[name]['area']:.15g}"
                ),
                "independent_normalized_power": (
                    f"{normalized[name]['power']:.15g}"
                ),
                "independent_normalized_arrival_time": (
                    f"{normalized[name]['arrival_time']:.15g}"
                ),
                "score_match": score_ok,
                "rank_match": (
                    saved_rank == index
                    or any(
                        other != name
                        and abs(
                            scores[other] - scores[name]
                        ) <= tolerance
                        for other in independent_order
                    )
                ),
            })

        for left, right in zip(
            saved_order, saved_order[1:]
        ):
            left_name = left["configuration"].strip()
            right_name = right["configuration"].strip()

            if (
                scores[left_name] >
                scores[right_name] + tolerance
            ):
                rank_matches = False

        check(
            score_matches,
            f"All weighted scores match: {scenario}",
        )
        check(
            normalization_matches,
            f"All normalized metrics match: {scenario}",
        )
        check(
            rank_matches,
            f"Saved ranking order valid: {scenario}",
        )

        minimum_score = min(scores.values())
        independent_ties = sorted(
            name for name, score in scores.items()
            if abs(score - minimum_score) <= tolerance
        )

        recorded = global_winners[scenario]
        saved_winner = recorded["winner"]
        saved_ties = sorted(
            recorded.get("tied_winners", [])
        )

        winner_match = (
            saved_winner in independent_ties
            and saved_ties == independent_ties
            and close(
                recorded["best_score"],
                minimum_score,
            )
        )

        check(
            winner_match,
            f"Global winner and ties match: {scenario}",
        )

        scenario_results[scenario] = {
            "independent_winner": independent_ties[0],
            "independent_tied_winners": independent_ties,
            "saved_winner": saved_winner,
            "saved_tied_winners": saved_ties,
            "minimum_score": minimum_score,
            "winner_match": winner_match,
        }

        print(
            f"\n{scenario}: "
            f"independent={independent_ties[0]}, "
            f"saved={saved_winner}"
        )

    passed = sum(
        item["status"] == "PASS" for item in checks
    )
    failed = len(checks) - passed
    status = "PASS" if failed == 0 else "FAIL"

    details = {
        "day": 29,
        "step": 2,
        "status": status,
        "passed_checks": passed,
        "failed_checks": failed,
        "configuration_count": len(source),
        "ranking_count": len(saved_rows),
        "scenarios": list(SCENARIOS),
        "metric_minima": minima,
        "metric_maxima": maxima,
        "scenario_results": scenario_results,
        "checks": checks,
        "methodology": {
            "source": str(SOURCE),
            "reference_rankings": str(RANKINGS),
            "normalization": "min_max_all_13",
            "scoring": "weighted_sum",
            "tie_tolerance": tolerance,
            "rtl_modified": False,
            "eda_rerun": False,
            "functional_equivalence_proven": False,
        },
    }

    write_reports(output_rows, details)

    print("\n" + "=" * 72)
    print("DAY 29 STEP 2 SUMMARY")
    print("=" * 72)
    print(f"PASSED CHECKS: {passed}")
    print(f"FAILED CHECKS: {failed}")
    print(f"FINAL RESULT: {status}")
    print(f"CSV REPORT: {OUT_CSV}")
    print(f"JSON REPORT: {OUT_JSON}")
    print(f"TEXT REPORT: {OUT_TXT}")

    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"\nDAY 29 STEP 2: FAIL - {exc}")
        sys.exit(1)
