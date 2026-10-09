#!/usr/bin/env python3
"""Day 30 Step 8C-1: final reconciliation of the *18 original* master requirements.

Uses the previously validated Step 8A-4 PASS results for 15 requirements, then
independently checks the three newly extended Day 30 FSM comparison datasets.
Does not overwrite the original audit, Day 26/27/30 PPA inputs, or the v2 audit.
Run from anywhere after installing at extensions/scripts/ in the repository.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "extensions/results/day30"
OUT = BASE / "master_audit_reconciled_v3"
V2_CSV = BASE / "master_audit_reconciled_v2/day30_master_requirements_reconciled_v2.csv"
V2_JSON = BASE / "master_audit_reconciled_v2/day30_master_requirements_reconciled_v2.json"
OLD_CSV = BASE / "master_audit/master_requirements_audit.csv"
COMPARISON = BASE / "fsm_comparison_extended"
PPA = BASE / "fsm_ppa_extension/day30_fsm_20_ppa_summary.csv"
DAY26 = ROOT / "extensions/results/day26/day26_fsm_ppa_summary.csv"
EFF = COMPARISON / "day30_fsm_20_efficiency_metrics.csv"
PAIR = COMPARISON / "day30_fsm_10_mealy_moore_comparison.csv"
PARETO = COMPARISON / "day30_fsm_20_pareto_analysis.csv"
SUMMARY = COMPARISON / "day30_fsm_20_comparison_summary.json"
REPORT = COMPARISON / "day30_fsm_20_comparison_report.md"
GRAPH_NAMES = (
    "01_fsm_area_comparison.png",
    "02_fsm_power_comparison.png",
    "03_fsm_arrival_time_comparison.png",
    "04_fsm_arrival_based_adp.png",
    "05_fsm_arrival_based_pdp.png",
    "06_fsm_pareto_tradeoff.png",
)
PATTERNS = ("1011", "1101", "1001", "10101", "1110")
ARCHS = ("mealy", "moore")
MODES = (0, 1)
EXPECTED = {
    f"{a}_{p}_overlap_{o}"
    for p in PATTERNS for a in ARCHS for o in MODES
}
MEASUREMENTS = (
    "area_um2", "setup_slack_ns", "data_arrival_ns",
    "internal_power_uw", "switching_power_uw",
    "leakage_power_uw", "total_power_uw",
)
HISTORICAL_IDS = {"PPA-02", "PPA-03", "PPA-04"}


def require(condition, description):
    if not condition:
        raise ValueError(description)


def nonempty(path):
    require(path.is_file() and path.stat().st_size > 0, f"Missing/empty file: {path}")
    return path


def load_csv(path, columns=()):
    nonempty(path)
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        require(reader.fieldnames is not None, f"CSV has no header: {path}")
        require(set(columns) <= set(reader.fieldnames),
                f"Missing columns {sorted(set(columns)-set(reader.fieldnames))}: {path}")
        rows = list(reader)
    return rows


def load_json(path):
    return json.loads(nonempty(path).read_text(encoding="utf-8"))


def num(value, label, positive=False):
    try:
        n = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label}: invalid numeric value {value!r}") from exc
    require(math.isfinite(n), f"{label}: nonfinite value")
    if positive:
        require(n > 0, f"{label}: expected a positive value")
    return n


def equal_number(observed, expected, label, absolute=1e-5):
    a = num(observed, label)
    b = num(expected, label)
    require(math.isclose(a, b, rel_tol=1e-7, abs_tol=absolute),
            f"{label}: got {a}, expected {b}")


def unique(rows, key, expected, description):
    names = [str(r.get(key, "")).strip() for r in rows]
    require(len(names) == len(expected), f"{description}: expected {len(expected)} rows, got {len(names)}")
    require(len(set(names)) == len(names), f"{description}: duplicate {key} entries")
    require(set(names) == set(expected),
            f"{description}: missing={sorted(set(expected)-set(names))}; unexpected={sorted(set(names)-set(expected))}")
    return {str(row[key]).strip(): row for row in rows}


def dominates(a, b):
    keys = ("area_um2", "total_power_uw", "data_arrival_ns")
    return (all(a[k] <= b[k] + 1e-10 for k in keys)
            and any(a[k] < b[k] - 1e-10 for k in keys))


def match_label(mealy, moore, field, lower_better=True):
    x = mealy[field]
    y = moore[field]
    if math.isclose(x, y, abs_tol=1e-10, rel_tol=1e-10):
        return "Tie"
    if lower_better:
        return "Mealy" if x < y else "Moore"
    return "Mealy" if x > y else "Moore"


def validate_comparison():
    required_ppa_columns = (*MEASUREMENTS, "configuration", "timing_status")
    ppa_rows = load_csv(PPA, required_ppa_columns)
    ppa_by_name = unique(ppa_rows, "configuration", EXPECTED, "20-variant mapped PPA")
    designs = {}
    for name, row in ppa_by_name.items():
        require(row["timing_status"].strip().upper() == "MET", f"{name}: timing not MET")
        converted = {metric: num(row[metric], f"{name}.{metric}", positive=metric in
                                    ("area_um2", "total_power_uw", "data_arrival_ns"))
                     for metric in MEASUREMENTS}
        require(converted["setup_slack_ns"] >= 0, f"{name}: negative setup slack")
        designs[name] = converted

    summary = load_json(SUMMARY)
    require(isinstance(summary, dict) and summary.get("status") == "PASS", "Comparison summary status not PASS")
    for key, expected_count in (
        ("extended_configuration_count", 20),
        ("matched_pair_count", 10),
        ("pareto_record_count", 20),
        ("exploratory_global_pareto_count", 2),
        ("controlled_pareto_count", 14),
    ):
        require(int(summary.get(key, -1)) == expected_count, f"Summary {key} is inconsistent")

    # Validate the efficiency formulas against the original mapped PPA numbers.
    efficiency = load_csv(EFF, ("configuration", "area_um2", "total_power_uw", "data_arrival_ns",
                                 "arrival_based_adp_um2_ns", "arrival_based_pdp_fj",
                                 "area_power_product_um2_uw", "setup_timing_met"))
    e_by_name = unique(efficiency, "configuration", EXPECTED, "Efficiency metrics")
    for name, row in e_by_name.items():
        d = designs[name]
        for metric in ("area_um2", "total_power_uw", "data_arrival_ns", "setup_slack_ns"):
            equal_number(row[metric], d[metric], f"Efficiency {name}.{metric}")
        for metric, expected_value in (
            ("arrival_based_adp_um2_ns", d["area_um2"] * d["data_arrival_ns"]),
            ("arrival_based_pdp_fj", d["total_power_uw"] * d["data_arrival_ns"]),
            ("area_power_product_um2_uw", d["area_um2"] * d["total_power_uw"]),
        ):
            equal_number(row[metric], expected_value, f"Efficiency {name}.{metric}")
        require(str(row["setup_timing_met"]).strip().lower() == "true",
                f"{name}: efficiency timing not MET")
    print("[PASS] PPA-02: 20 efficiency rows; ADP/PDP/area-power formulae rechecked")

    # Matched comparisons: full numeric reconciliation for every of the 10 pairs.
    pair_rows = load_csv(PAIR, ("pattern", "overlap", "mealy_configuration", "moore_configuration"))
    pair_names = [f"{p}_{o}" for p in PATTERNS for o in MODES]
    pair_by_name = unique([dict(r, _key=f"{r['pattern']}_{r['overlap']}")
                           for r in pair_rows], "_key", pair_names, "Mealy/Moore comparisons")
    for pat in PATTERNS:
        for overlap in MODES:
            row = pair_by_name[f"{pat}_{overlap}"]
            mn = f"mealy_{pat}_overlap_{overlap}"
            rn = f"moore_{pat}_overlap_{overlap}"
            require(row["mealy_configuration"] == mn and row["moore_configuration"] == rn,
                    f"Matched pair wrong design names: {pat}/{overlap}")
            mealy, moore = designs[mn], designs[rn]
            for metric in MEASUREMENTS:
                a, b = mealy[metric], moore[metric]
                equal_number(row[f"mealy_{metric}"], a, f"{mn}.{metric}")
                equal_number(row[f"moore_{metric}"], b, f"{rn}.{metric}")
                equal_number(row[f"{metric}_difference"], round(b-a, 6),
                             f"{pat}/{overlap}.{metric}.difference")
                if a:
                    equal_number(row[f"{metric}_change_pct"], round(100*(b-a)/a, 4),
                                 f"{pat}/{overlap}.{metric}.percent", absolute=0.0002)
                else:
                    require(row[f"{metric}_change_pct"] in ("", None),
                            f"{pat}/{overlap}.{metric}: zero baseline expected empty change")
            for label, metric, low in (
                ("lower_area", "area_um2", True),
                ("lower_power", "total_power_uw", True),
                ("higher_setup_slack", "setup_slack_ns", False),
            ):
                require(row[label] == match_label(mealy, moore, metric, lower_better=low),
                        f"{pat}/{overlap}: inconsistent {label}")
    print("[PASS] PPA-03: 10 matched pairs; numeric differences and percentages rechecked")

    # Pareto records: reconstruct global and matched-pair domination from the source PPA.
    pareto_rows = load_csv(PARETO, ("configuration", "global_pareto_status", "global_dominated_by",
                                        "controlled_pareto_status", "controlled_dominated_by"))
    pareto_by_name = unique(pareto_rows, "configuration", EXPECTED, "Pareto analysis")
    globals_found, controlled_found = [], []
    for name, row in pareto_by_name.items():
        parts = name.split("_")
        arch, pat, overlap = parts[0], parts[1], parts[-1]
        d = designs[name]
        for metric in ("area_um2", "total_power_uw", "data_arrival_ns", "setup_slack_ns"):
            equal_number(row[metric], d[metric], f"Pareto {name}.{metric}")
        require(row.get("architecture") == arch and row.get("pattern") == pat
                and row.get("overlap") == overlap, f"Pareto {name}: mislabeled variant")
        all_dominators = sorted(other for other in designs if other != name and dominates(designs[other], d))
        opponents = [f"{a}_{pat}_overlap_{overlap}" for a in ARCHS if a != arch]
        matched_dominators = sorted(other for other in opponents if dominates(designs[other], d))
        for prefix, dominators in (("global", all_dominators), ("controlled", matched_dominators)):
            expected_status = "DOMINATED" if dominators else "PARETO"
            require(row[f"{prefix}_pareto_status"] == expected_status,
                    f"Pareto {name}: wrong {prefix} status")
            observed = sorted(x for x in row[f"{prefix}_dominated_by"].split(";") if x)
            require(observed == dominators, f"Pareto {name}: wrong {prefix} dominators")
        if not all_dominators:
            globals_found.append(name)
        if not matched_dominators:
            controlled_found.append(name)

    require(len(globals_found) == 2 and len(controlled_found) == 14,
            f"Unexpected Pareto counts global={len(globals_found)} matched={len(controlled_found)}")
    require(sorted(summary.get("exploratory_global_pareto_variants", [])) == sorted(globals_found),
            "Summary global Pareto members do not agree")
    require(sorted(summary.get("controlled_pareto_variants", [])) == sorted(controlled_found),
            "Summary controlled Pareto members do not agree")
    print("[PASS] PPA-04: 20 Pareto rows; global=2, controlled=14; dominators recomputed")

    nonempty(REPORT)
    for filename in GRAPH_NAMES:
        nonempty(COMPARISON / "graphs" / filename)
    print("[PASS] Six nonempty FSM comparison graphs and Markdown report")

    # Verify that the Day 27 reference pair report still agrees with the 6 old pairs.
    old_pairs = load_csv(ROOT / "extensions/results/day27/day27_mealy_moore_comparison.csv",
                         ("pattern", "overlap", "mealy_area_um2", "moore_area_um2"))
    require(len(old_pairs) == 6, "Original Day 27 matched pair count is not six")
    for old in old_pairs:
        key = f"{old['pattern']}_{old['overlap']}"
        require(key in pair_by_name, f"Historical Day 27 pair missing: {key}")
        latest = pair_by_name[key]
        for metric in ("mealy_area_um2", "moore_area_um2", "mealy_total_power_uw",
                       "moore_total_power_uw"):
            equal_number(latest[metric], old[metric], f"Historical consistency {key}.{metric}")

    # Verify original data files have retained their stored hashes when available.
    hashes = summary.get("historic_sources_sha256", {})
    if isinstance(hashes, dict):
        for file_string, expected_hash in hashes.items():
            path = Path(file_string)
            if not path.is_absolute():
                path = ROOT / path
            require(hashlib.sha256(nonempty(path).read_bytes()).hexdigest() == expected_hash,
                    f"Historical evidence modified: {path}")

    original = load_csv(DAY26, ("configuration",))
    require(len(original) == 13, "Day 26 must remain 13 records")
    require("fsm_original_1011" in {r["configuration"] for r in original},
            "Day 26 original reference missing")
    return {
        "efficiency_rows": len(efficiency),
        "matched_pair_rows": len(pair_rows),
        "pareto_rows": len(pareto_rows),
        "global_pareto_count": len(globals_found),
        "controlled_pareto_count": len(controlled_found),
        "graph_count": len(GRAPH_NAMES),
        "original_reference": "fsm_original_1011",
    }


def main():
    print("=" * 76)
    print("DAY 30 STEP 8C-1 — FINAL 18-REQUIREMENT MASTER RECONCILIATION")
    print("=" * 76)

    old_rows = load_csv(OLD_CSV, ("id", "module", "requirement", "status"))
    require(len(old_rows) == 18, "Original master audit does not have 18 requirements")
    original_ids = [r["id"] for r in old_rows]
    require(len(set(original_ids)) == 18, "Duplicate original requirement IDs")

    v2rows = load_csv(V2_CSV, ("id", "module", "requirement", "old_status", "reconciled_status", "evidence", "notes"))
    require(len(v2rows) == 18, "Corrected v2 audit does not have 18 rows")
    v2_by_id = unique(v2rows, "id", original_ids, "Corrected v2 audit")
    v2j = load_json(V2_JSON)
    require(v2j.get("overall_status") == "PASS_WITH_HISTORICAL_SCOPE", "Step 8A-4 audit did not pass")
    counts = Counter(r["reconciled_status"] for r in v2rows)
    require(counts == {"PASS": 15, "HISTORICAL_SCOPE": 3},
            f"Expected 15 passing and three historical v2 rows; got {dict(counts)}")
    require({r["id"] for r in v2rows if r["reconciled_status"] == "HISTORICAL_SCOPE"} == HISTORICAL_IDS,
            "Unexpected historical IDs in v2")
    print("[PASS] Step 8A-4 validated the other 15 master requirements")

    figures = validate_comparison()
    new_evidence = {
        "PPA-02": EFF,
        "PPA-03": PAIR,
        "PPA-04": PARETO,
    }
    next_rows = []
    for source in old_rows:
        rid = source["id"]
        old = v2_by_id[rid]
        row = dict(old)
        row["reconciled_status"] = "PASS"
        if rid in HISTORICAL_IDS:
            row["evidence"] = str(new_evidence[rid].relative_to(ROOT)) + "; " + str(SUMMARY.relative_to(ROOT))
            row["notes"] = {
                "PPA-02": "Day 30: 20/20 efficiency metrics, formulae independently verified. Day 27 retained as history.",
                "PPA-03": "Day 30: 10/10 matched Mealy/Moore pairs; change percentages verified.",
                "PPA-04": "Day 30: 20/20 Pareto records, global and controlled dominance verified; global comparisons exploratory.",
            }[rid]
        else:
            row["notes"] = "Inherited from Step 8A-4 validated evidence. " + row["notes"]
        next_rows.append(row)

    require(len(next_rows) == 18 and all(row["reconciled_status"] == "PASS" for row in next_rows),
            "Final requirement reconciliation incomplete")
    OUT.mkdir(parents=True, exist_ok=True)
    csv_path = OUT / "day30_master_requirements_reconciled_v3.csv"
    json_path = OUT / "day30_master_requirements_reconciled_v3.json"
    md_path = OUT / "day30_master_requirements_reconciled_v3.md"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(next_rows[0]))
        writer.writeheader()
        writer.writerows(next_rows)

    summary = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "18 original master requirements; v2 evidence inherited for 15; extended PPA comparisons recomputed for three",
        "status": "PASS",
        "overall_status": "PASS_18_OF_18_REQUIREMENTS",
        "status_counts": {"PASS": 18},
        "source_master": str(OLD_CSV.relative_to(ROOT)),
        "source_v2": str(V2_JSON.relative_to(ROOT)),
        "comparison_validation": figures,
        "requirements": next_rows,
        "limitations": [
            "No new RTL simulations, synthesis or STA performed during this reconciliation.",
            "The first 15 results inherit verified Step 8A-4 evidence; this is not a clean-room reproduction.",
            "Power and area are technology-mapped pre-layout estimates, not routed silicon results.",
            "Reported arrival time is not an intrinsic combinational delay measurement.",
            "Mealy and Moore detection cycle timing may differ.",
            "Global Pareto comparison across patterns is exploratory, not a functional replacement recommendation.",
            "The 18-requirement master list does not cover thesis writing, repository archival, or final submission readiness.",
            "All original Day 26, Day 27 and v2 audit files were read-only inputs.",
        ],
    }
    json_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    md = [
        "# Day 30 — Final reconciled master requirements (v3)", "",
        "## Results", "",
        "**18/18 original requirements PASS.** The existing Day 27 reports remain historical; updated Day 30 reports cover their extended scope.", "",
        "| ID | Requirement | Result | Evidence |",
        "|---|---|---|---|",
    ]
    for r in next_rows:
        md.append(f"| {r['id']} | {r['requirement']} | PASS | {r['evidence']} |")
    md.extend(["", "## FSM comparison", ""])
    for k, v in figures.items():
        md.append(f"- {k}: {v}")
    md.extend(["", "## Limitations", ""])
    md.extend(f"- {x}" for x in summary["limitations"])
    md_path.write_text("\n".join(md) + "\n", encoding="utf-8")

    print("\n========== FINAL MASTER REQUIREMENTS SUMMARY ==========")
    for row in next_rows:
        print(f"{row['id']:<9} PASS  {row['requirement']}")
    print("STATUS COUNTS: {'PASS': 18}")
    print("OVERALL: PASS_18_OF_18_REQUIREMENTS")
    print("HISTORICAL DAY 27 REPORTS: PRESERVED")
    print("THESIS SUBMISSION READINESS: NOT ASSESSED")
    print("CSV:", csv_path.relative_to(ROOT))
    print("JSON:", json_path.relative_to(ROOT))
    print("MARKDOWN:", md_path.relative_to(ROOT))
    print("DAY 30 FINAL MASTER AUDIT: PASS")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError, AssertionError, IndexError) as exc:
        print(f"DAY 30 FINAL MASTER AUDIT: FAIL — {exc}", file=sys.stderr)
        sys.exit(1)
