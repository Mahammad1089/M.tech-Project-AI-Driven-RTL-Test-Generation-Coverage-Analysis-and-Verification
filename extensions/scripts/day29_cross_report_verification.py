#!/usr/bin/env python3
"""Day 29 Step 4: cross-report evidence consistency verification."""

import csv
import json
import sys
from pathlib import Path

BASE = Path("extensions/results")
DAY27 = BASE / "day27"
DAY28 = BASE / "day28"
DAY29 = BASE / "day29"

SCENARIOS = {
    "area_priority",
    "power_priority",
    "timing_priority",
    "balanced",
}

REQUIRED_FILES = {
    "day27_efficiency": DAY27 / "day27_efficiency_metrics.csv",
    "day28_selection": DAY28 / "day28_architecture_selection.json",
    "day28_rankings": DAY28 / "day28_architecture_rankings.csv",
    "day28_sensitivity": DAY28 / "day28_constraint_sensitivity.json",
    "day28_sensitivity_csv": DAY28 / "day28_constraint_sensitivity.csv",
    "day28_robustness": DAY28 / "day28_architecture_robustness.json",
    "day29_baseline": DAY29 / "day29_baseline_validation.json",
    "day29_ranking": DAY29 / "day29_independent_ranking_audit.json",
    "day29_ranking_csv": DAY29 / "day29_independent_ranking_audit.csv",
    "day29_sensitivity": DAY29 / "day29_independent_sensitivity_audit.json",
    "day29_sensitivity_csv": DAY29 / "day29_independent_sensitivity_audit.csv",
}

checks = []


def check(description, condition):
    status = "PASS" if condition else "FAIL"
    checks.append({
        "description": description,
        "status": status,
    })
    print(f"[{status}] {description}")


def read_json(path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def get_winner(value):
    """Extract winner from a saved or independently audited record."""
    if isinstance(value, str):
        return value

    if isinstance(value, dict):
        for key in ("winner", "selected_configuration", "independent_winner", "saved_winner"):
            candidate = value.get(key)
            if isinstance(candidate, str):
                return candidate

    return None


def verify():
    DAY29.mkdir(parents=True, exist_ok=True)

    print("=" * 72)
    print("DAY 29 STEP 4")
    print("CROSS-REPORT CONSISTENCY VERIFICATION")
    checks.clear()
    print("=" * 72)

    for label, path in REQUIRED_FILES.items():
        check(
            f"Required evidence available: {label}",
            path.is_file() and path.stat().st_size > 0,
        )

    if any(item["status"] == "FAIL" for item in checks):
        return finalize()

    reports = {
        "day28_selection": read_json(REQUIRED_FILES["day28_selection"]),
        "day28_sensitivity": read_json(REQUIRED_FILES["day28_sensitivity"]),
        "day28_robustness": read_json(REQUIRED_FILES["day28_robustness"]),
        "day29_baseline": read_json(REQUIRED_FILES["day29_baseline"]),
        "day29_ranking": read_json(REQUIRED_FILES["day29_ranking"]),
        "day29_sensitivity": read_json(REQUIRED_FILES["day29_sensitivity"]),
    }

    for name, data in reports.items():
        check(
            f"{name} reports PASS",
            isinstance(data, dict) and data.get("status") == "PASS",
        )

    source = read_csv(REQUIRED_FILES["day27_efficiency"])
    rankings = read_csv(REQUIRED_FILES["day28_rankings"])
    sensitivity = read_csv(REQUIRED_FILES["day28_sensitivity_csv"])
    ranking_audit = read_csv(REQUIRED_FILES["day29_ranking_csv"])
    sensitivity_audit = read_csv(REQUIRED_FILES["day29_sensitivity_csv"])

    source_names = [r.get("configuration") for r in source]

    check("Day 27 contains 13 configurations", len(source) == 13)
    check(
        "Day 27 configuration names are unique",
        len(set(source_names)) == 13 and all(source_names),
    )

    check("Day 28 contains 52 ranking records", len(rankings) == 52)
    check("Day 28 contains 32 sensitivity records", len(sensitivity) == 32)

    check(
        "Day 28 rankings contain four scenarios",
        {r.get("scenario") for r in rankings} == SCENARIOS,
    )

    for scenario in sorted(SCENARIOS):
        subset = [r for r in rankings if r.get("scenario") == scenario]
        check(
            f"Day 28 {scenario}: 13 ranking records",
            len(subset) == 13,
        )
        check(
            f"Day 28 {scenario}: unique configurations",
            {r.get("configuration") for r in subset} == set(source_names),
        )

        try:
            ranks = sorted(int(r["rank"]) for r in subset)
            rank_valid = ranks == list(range(1, 14))
        except (KeyError, TypeError, ValueError):
            rank_valid = False

        check(
            f"Day 28 {scenario}: consecutive ranks",
            rank_valid,
        )

    sensitivity_pairs = [
        (r.get("constraint_case"), r.get("scenario"))
        for r in sensitivity
    ]

    constraint_cases = {
        r.get("constraint_case") for r in sensitivity
    }

    check(
        "Day 28 contains eight constraint cases",
        len(constraint_cases) == 8 and None not in constraint_cases,
    )
    check(
        "Day 28 sensitivity decisions are unique",
        len(set(sensitivity_pairs)) == 32,
    )

    for case in sorted(x for x in constraint_cases if x is not None):
        actual = {
            r.get("scenario")
            for r in sensitivity
            if r.get("constraint_case") == case
        }
        check(
            f"{case}: four selection scenarios",
            actual == SCENARIOS,
        )

    baseline = reports["day29_baseline"]
    ranking = reports["day29_ranking"]
    audit = reports["day29_sensitivity"]

    check(
        "Step 1: 27 passed checks, zero failures",
        baseline.get("passed_checks") == 27
        and baseline.get("failed_checks") == 0,
    )

    check(
        "Step 2: 45 passed checks, zero failures",
        ranking.get("passed_checks") == 45
        and ranking.get("failed_checks") == 0,
    )

    check(
        "Step 3: 216 passed checks, zero failures",
        audit.get("passed_checks") == 216
        and audit.get("failed_checks") == 0,
    )

    check(
        "Step 2: 13 configurations",
        ranking.get("configuration_count") == 13,
    )

    check(
        "Step 2: 52 ranking records",
        ranking.get("ranking_count") == 52,
    )

    check(
        "Step 3: 13 configurations",
        audit.get("configuration_count") == 13,
    )

    check(
        "Step 3: eight constraint cases",
        audit.get("constraint_case_count") == 8,
    )

    check(
        "Step 3: four scenarios",
        audit.get("scenario_count") == 4,
    )

    check(
        "Step 3: 32 audited decisions",
        audit.get("decision_count") == 32,
    )

    check(
        "Step 3: no failed findings",
        audit.get("failed_findings") == [],
    )

    # Step 2 CSV stores boolean comparison fields rather than a PASS status.
    # Every row must have both independent score and rank agreement.
    def is_true(value):
        return value is True or str(value).strip().lower() in ("true", "1", "pass")

    check(
        "Step 2 audit CSV has no failed records",
        len(ranking_audit) == 52
        and all(
            is_true(r.get("score_match")) and is_true(r.get("rank_match"))
            for r in ranking_audit
        ),
    )

    # 216 is the number of Step 3 checks, not necessarily CSV rows.
    # Verify that its CSV is populated and has no explicit failed findings,
    # and that the independently produced Step 3 JSON confirms 216/0.
    def row_has_no_failure(row):
        if "status" in row:
            return str(row["status"]).strip().upper() == "PASS"
        if "result" in row and str(row["result"]).strip().upper() in ("PASS", "FAIL"):
            return str(row["result"]).strip().upper() == "PASS"
        for key, value in row.items():
            if key.endswith("_match") or key in ("passed", "match"):
                if not is_true(value):
                    return False
        return all(v is not None for v in row.values())

    check(
        "Step 3 audit CSV consistent with 216 passed checks",
        bool(sensitivity_audit)
        and all(row_has_no_failure(r) for r in sensitivity_audit)
        and audit.get("passed_checks") == 216
        and audit.get("failed_checks") == 0
        and audit.get("failed_findings") == [],
    )

    day28_winners = reports["day28_selection"].get(
        "global_winners", {}
    )

    independent_winners = ranking.get("scenario_results", {})

    for scenario in sorted(SCENARIOS):
        saved = get_winner(day28_winners.get(scenario))
        independent = get_winner(independent_winners.get(scenario))

        # The independent audit's scenario_results may have a
        # different nested schema. Only compare values when both
        # are extractable; otherwise report a failed comparison.
        check(
            f"Global winner agreement: {scenario}",
            saved is not None
            and independent is not None
            and saved == independent,
        )

    check(
        "No RTL modifications recorded in Step 3",
        audit.get("methodology", {}).get("rtl_modified") is False,
    )

    check(
        "No synthesis rerun recorded in Step 3",
        audit.get("methodology", {}).get("synthesis_rerun") is False,
    )

    check(
        "No simulation rerun recorded in Step 3",
        audit.get("methodology", {}).get("simulation_rerun") is False,
    )

    return finalize()


def finalize():
    passed = sum(x["status"] == "PASS" for x in checks)
    failed = sum(x["status"] == "FAIL" for x in checks)
    status = "PASS" if failed == 0 else "FAIL"

    summary = {
        "day": 29,
        "step": 4,
        "status": status,
        "passed_checks": passed,
        "failed_checks": failed,
        "checks": checks,
        "limitations": [
            "Existing evidence is reused without RTL or EDA reruns.",
            "Numerical consistency does not prove functional equivalence.",
            "Power values are based on assumed switching activity.",
            "Timing values are not post-layout signoff results.",
        ],
    }

    json_path = DAY29 / "day29_cross_report_verification.json"
    txt_path = DAY29 / "day29_cross_report_verification.txt"

    json_path.write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )

    lines = [
        "=" * 72,
        "DAY 29 STEP 4 - CROSS-REPORT VERIFICATION",
        "=" * 72,
        f"PASSED CHECKS: {passed}",
        f"FAILED CHECKS: {failed}",
        f"FINAL RESULT: {status}",
        "",
        "CHECK DETAILS",
        "-" * 72,
    ]

    lines.extend(
        f"[{item['status']}] {item['description']}"
        for item in checks
    )

    lines.extend([
        "",
        "LIMITATIONS",
        "-" * 72,
        *summary["limitations"],
        "",
        f"DAY 29 STEP 4: {status}",
    ])

    txt_path.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )

    print("\n" + "=" * 72)
    print("DAY 29 STEP 4 SUMMARY")
    print("=" * 72)
    print(f"PASSED CHECKS: {passed}")
    print(f"FAILED CHECKS: {failed}")
    print(f"FINAL RESULT: {status}")
    print(f"JSON REPORT: {json_path}")
    print(f"TEXT REPORT: {txt_path}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    try:
        sys.exit(verify())
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"[FAIL] Unexpected verification error: {exc}")
        sys.exit(1)
