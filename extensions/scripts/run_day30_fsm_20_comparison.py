#!/usr/bin/env python3
"""Day 30 Step 8B-3: extend historical Day 27 FSM PPA comparisons.

Reads Day 26 and merged Day 30 inputs, makes fresh Day 30 artifacts only.
No RTL or existing Day 26/27/30 PPA evidence is modified.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / "extensions/results/day30/fsm_ppa_extension/day30_fsm_20_ppa_summary.csv"
HISTORICAL = ROOT / "extensions/results/day26/day26_fsm_ppa_summary.csv"
OUT = ROOT / "extensions/results/day30/fsm_comparison_extended"
GRAPHS = OUT / "graphs"
PATTERNS = ("1011", "1101", "1001", "10101", "1110")
MODES = (0, 1)
ARCHS = ("mealy", "moore")
METRICS = (
    "area_um2", "setup_slack_ns", "data_arrival_ns",
    "internal_power_uw", "switching_power_uw",
    "leakage_power_uw", "total_power_uw",
)
REQUIRED = {f"{arch}_{pattern}_overlap_{mode}"
            for pattern in PATTERNS for arch in ARCHS for mode in MODES}
NAME = re.compile(r"^(mealy|moore)_(1011|1101|1001|10101|1110)_overlap_([01])$")


def check(condition, message):
    if not condition:
        raise ValueError(message)


def read_csv(path):
    check(path.is_file() and path.stat().st_size > 0, f"Missing CSV: {path}")
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        check(reader.fieldnames is not None, f"Missing CSV header: {path}")
        rows = list(reader)
    return reader.fieldnames, rows


def load_inputs():
    fields, rows = read_csv(INPUT)
    needed = {"configuration", "timing_status", *METRICS}
    check(not (needed - set(fields)), f"Day 30 missing columns: {sorted(needed-set(fields))}")
    check(len(rows) == 20, f"Day 30 must have exactly 20 rows, found {len(rows)}")
    names = [r["configuration"].strip() for r in rows]
    count = Counter(names)
    check(set(names) == REQUIRED, f"Missing={sorted(REQUIRED-set(names))}, extra={sorted(set(names)-REQUIRED)}")
    check(all(n == 1 for n in count.values()), f"Duplicate configurations: {dict(count)}")
    records = {}
    for row in rows:
        name = row["configuration"].strip()
        check(NAME.fullmatch(name), f"Unexpected configuration: {name}")
        check(row["timing_status"].strip().upper() == "MET", f"Setup status not MET: {name}")
        clean = {"configuration": name}
        for metric in METRICS:
            try:
                value = float(row[metric])
            except (ValueError, TypeError) as exc:
                raise ValueError(f"Invalid {metric} in {name}: {row[metric]!r}") from exc
            check(math.isfinite(value), f"Nonfinite {metric} in {name}")
            check(value >= 0, f"Negative {metric} in {name}")
            clean[metric] = value
        for k in ("area_um2", "total_power_uw", "data_arrival_ns"):
            check(clean[k] > 0, f"Nonpositive {k} in {name}")
        check(abs(clean["total_power_uw"] - sum(clean[k] for k in
                  ("internal_power_uw", "switching_power_uw", "leakage_power_uw"))) <= 0.08,
              f"Power components inconsistent in {name}")
        clean["timing_status"] = "MET"
        records[name] = clean

    old_fields, old_rows = read_csv(HISTORICAL)
    check(len(old_rows) == 13, f"Expected 13 historical records, found {len(old_rows)}")
    check(set(METRICS) <= set(old_fields), "Historical PPA CSV missing numeric columns")
    old = {r["configuration"]: r for r in old_rows}
    check(len(old) == 13 and "fsm_original_1011" in old,
          "Day 26 baseline + 12 extended records not found")
    historical_names = set(old) - {"fsm_original_1011"}
    check(len(historical_names) == 12 and historical_names <= REQUIRED,
          "Unexpected Day 26 extended configuration set")
    for name in historical_names:
        for metric in METRICS:
            check(math.isclose(float(old[name][metric]), records[name][metric],
                               rel_tol=1e-8, abs_tol=1e-7),
                  f"Day 26/Day 30 data conflict: {name}, {metric}")
    return records, old


def pct_change(base, new):
    return round(100 * (new - base) / base, 4) if base != 0 else None


def create_efficiency(records):
    rows = []
    for name in sorted(records):
        r = records[name]
        area = r["area_um2"]
        arrival = r["data_arrival_ns"]
        power = r["total_power_uw"]
        rows.append({
            "configuration": name,
            "area_um2": area,
            "data_arrival_ns": arrival,
            "setup_slack_ns": r["setup_slack_ns"],
            "total_power_uw": power,
            "arrival_based_adp_um2_ns": round(area * arrival, 8),
            "arrival_based_pdp_fj": round(power * arrival, 8),
            "area_power_product_um2_uw": round(area * power, 8),
            "setup_timing_met": True,
        })
    return rows


def better_label(a, b, lower_is_better=True):
    if math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-12):
        return "Tie"
    if lower_is_better:
        return "Mealy" if a < b else "Moore"
    return "Mealy" if a > b else "Moore"


def create_pairs(records):
    rows = []
    for pattern in PATTERNS:
        for overlap in MODES:
            mn = f"mealy_{pattern}_overlap_{overlap}"
            rn = f"moore_{pattern}_overlap_{overlap}"
            m, r = records[mn], records[rn]
            item = {
                "pattern": pattern,
                "overlap": overlap,
                "mealy_configuration": mn,
                "moore_configuration": rn,
            }
            for k in METRICS:
                a, b = m[k], r[k]
                item["mealy_" + k] = round(a, 6)
                item["moore_" + k] = round(b, 6)
                item[k + "_difference"] = round(b - a, 6)
                item[k + "_change_pct"] = pct_change(a, b)
            item["lower_area"] = better_label(m["area_um2"], r["area_um2"])
            item["lower_power"] = better_label(m["total_power_uw"], r["total_power_uw"])
            item["higher_setup_slack"] = better_label(
                m["setup_slack_ns"], r["setup_slack_ns"], lower_is_better=False)
            rows.append(item)
    return rows


def dominates(a, b):
    # Reproduce historical Day 27 intent: minimize area, total power,
    # and reported data arrival. Arrival is NOT intrinsic gate delay.
    keys = ("area_um2", "total_power_uw", "data_arrival_ns")
    return all(a[k] <= b[k] + 1e-10 for k in keys) and any(
        a[k] < b[k] - 1e-10 for k in keys)


def create_pareto(records):
    rows = []
    for name in sorted(records):
        match = NAME.fullmatch(name)
        assert match
        arch, pattern, overlap = match.groups()
        r = records[name]
        group = f"pattern_{pattern}_overlap_{overlap}"
        competitors = [f"{a}_{pattern}_overlap_{overlap}" for a in ARCHS]
        global_dominators = sorted(other for other in records if other != name
                                   and dominates(records[other], r))
        controlled_dominators = sorted(other for other in competitors if other != name
                                       and dominates(records[other], r))
        rows.append({
            "configuration": name,
            "architecture": arch,
            "pattern": pattern,
            "overlap": overlap,
            "comparison_group": group,
            "area_um2": r["area_um2"],
            "total_power_uw": r["total_power_uw"],
            "data_arrival_ns": r["data_arrival_ns"],
            "setup_slack_ns": r["setup_slack_ns"],
            "global_pareto_status": "DOMINATED" if global_dominators else "PARETO",
            "global_dominated_by": ";".join(global_dominators),
            "controlled_pareto_status": "DOMINATED" if controlled_dominators else "PARETO",
            "controlled_dominated_by": ";".join(controlled_dominators),
        })
    return rows


def write_csv(name, rows):
    check(bool(rows), f"No rows for {name}")
    path = OUT / name
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return path


def write_json(name, data):
    path = OUT / name
    path.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return path


def plot_graphs(efficiency, pareto):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise RuntimeError("Matplotlib not installed. Install python3-matplotlib or 'python3 -m pip install matplotlib' into your project virtualenv.") from exc

    GRAPHS.mkdir(parents=True, exist_ok=True)
    cases = [r["configuration"].replace("_overlap_", "_o") for r in efficiency]
    def bar(filename, key, ylabel, title):
        fig, ax = plt.subplots(figsize=(17, 7))
        ax.bar(range(len(cases)), [r[key] for r in efficiency])
        ax.set_xticks(range(len(cases)))
        ax.set_xticklabels(cases, rotation=65, ha="right", fontsize=8)
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.grid(axis="y", alpha=0.25)
        fig.tight_layout()
        fig.savefig(GRAPHS / filename, dpi=180)
        plt.close(fig)

    bar("01_fsm_area_comparison.png", "area_um2", "Cell area (µm²)", "20 extended FSM variants: mapped area")
    bar("02_fsm_power_comparison.png", "total_power_uw", "Estimated power (µW)", "20 extended FSM variants: assumed-activity power")
    bar("03_fsm_arrival_time_comparison.png", "data_arrival_ns", "Reported arrival (ns)", "20 extended FSM variants: reported arrival (not intrinsic delay)")
    bar("04_fsm_arrival_based_adp.png", "arrival_based_adp_um2_ns", "Area × arrival (µm²·ns)", "20 FSM variants: arrival-based ADP")
    bar("05_fsm_arrival_based_pdp.png", "arrival_based_pdp_fj", "Power × arrival (fJ)", "20 FSM variants: arrival-based PDP")

    fig, ax = plt.subplots(figsize=(11, 7))
    for status, marker in (("PARETO", "o"), ("DOMINATED", "x")):
        subset = [r for r in pareto if r["global_pareto_status"] == status]
        ax.scatter([r["area_um2"] for r in subset], [r["total_power_uw"] for r in subset],
                   label=f"Exploratory global: {status}", marker=marker, s=68)
    for r in pareto:
        ax.annotate(r["configuration"].replace("_overlap_", "_o"),
                    (r["area_um2"], r["total_power_uw"]), xytext=(3, 4),
                    textcoords="offset points", fontsize=6)
    ax.set_xlabel("Cell area (µm²)")
    ax.set_ylabel("Estimated power (µW)")
    ax.set_title("FSM area vs power (global Pareto also minimizes reported arrival)")
    ax.grid(alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(GRAPHS / "06_fsm_pareto_tradeoff.png", dpi=180)
    plt.close(fig)
    return sorted(GRAPHS.glob("*.png"))


def main():
    print("=" * 75)
    print("DAY 30 STEP 8B-3 — 20-CONFIGURATION FSM COMPARISON EXTENSION")
    print("=" * 75)
    records, old = load_inputs()
    print("[PASS] Day 30 mapped PPA: 20 unique extended variants, all timing MET")
    print("[PASS] Historical Day 26: original reference + 12 matching extended variants")
    print("[PASS] Day 26 vs Day 30 numerical consistency for existing 12 variants")

    efficiency = create_efficiency(records)
    pairs = create_pairs(records)
    pareto = create_pareto(records)
    check(len(efficiency) == 20 and len(pairs) == 10 and len(pareto) == 20,
          "Incorrect generated comparison counts")
    for r in efficiency:
        check(math.isclose(r["arrival_based_adp_um2_ns"], r["area_um2"] * r["data_arrival_ns"], rel_tol=1e-8, abs_tol=1e-7), "ADP check failed")
        check(math.isclose(r["arrival_based_pdp_fj"], r["total_power_uw"] * r["data_arrival_ns"], rel_tol=1e-8, abs_tol=1e-7), "PDP check failed")

    # Compare every old Mealy/Moore matched pair against prior Day 27 metrics.
    _, historic_pairs = read_csv(ROOT / "extensions/results/day27/day27_mealy_moore_comparison.csv")
    check(len(historic_pairs) == 6, "Day 27 matched comparison should have 6 pairs")
    historic_by_key = {(r["pattern"], str(r["overlap"])): r for r in historic_pairs}
    for item in pairs:
        key = (item["pattern"], str(item["overlap"]))
        if key not in historic_by_key:
            continue
        old_pair = historic_by_key[key]
        for k in ("mealy_area_um2", "moore_area_um2", "area_um2_change_pct",
                  "mealy_total_power_uw", "moore_total_power_uw", "total_power_uw_change_pct",
                  "mealy_data_arrival_ns", "moore_data_arrival_ns", "higher_setup_slack"):
            if k == "higher_setup_slack":
                check(item[k] == old_pair[k], f"Historical pair mismatch {key} {k}")
            else:
                check(math.isclose(float(item[k]), float(old_pair[k]), abs_tol=1e-3),
                      f"Historical pair mismatch {key} {k}")
    print("[PASS] Day 27 matched comparison values reproduced for existing 6 pairs")

    source_hash = {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                   for p in (INPUT, HISTORICAL,
                             ROOT / "extensions/results/day27/day27_mealy_moore_comparison.csv")}
    OUT.mkdir(parents=True, exist_ok=True)
    files = [
        write_csv("day30_fsm_20_efficiency_metrics.csv", efficiency),
        write_csv("day30_fsm_10_mealy_moore_comparison.csv", pairs),
        write_csv("day30_fsm_20_pareto_analysis.csv", pareto),
    ]

    exploratory = [r["configuration"] for r in pareto if r["global_pareto_status"] == "PARETO"]
    controlled = [r["configuration"] for r in pareto if r["controlled_pareto_status"] == "PARETO"]
    baseline = old["fsm_original_1011"]
    doc = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS",
        "source": str(INPUT.relative_to(ROOT)),
        "historical_reference_source": str(HISTORICAL.relative_to(ROOT)),
        "technology": "Nangate45 typical",
        "analysis_scope": "20 extended variants; original FSM separately referenced",
        "extended_configuration_count": len(efficiency),
        "matched_pair_count": len(pairs),
        "pareto_record_count": len(pareto),
        "exploratory_global_pareto_count": len(exploratory),
        "controlled_pareto_count": len(controlled),
        "exploratory_global_pareto_variants": exploratory,
        "controlled_pareto_variants": controlled,
        "original_fsm_reference": {k: baseline[k] for k in ("configuration", *METRICS)},
        "formulae": {
            "arrival_based_adp_um2_ns": "area_um2 * data_arrival_ns",
            "arrival_based_pdp_fj": "total_power_uw * data_arrival_ns",
            "area_power_product_um2_uw": "area_um2 * total_power_uw",
            "moore_change_pct": "100 * (Moore - Mealy) / Mealy",
            "pareto": "minimize area_um2, total_power_uw, data_arrival_ns",
        },
        "constraints_and_limits": [
            "Technology-mapped pre-layout results, no parasitics or die area",
            "Power estimated from assumed switching activity (not waveform/silicon power)",
            "Reported data arrival is not necessarily intrinsic combinational delay",
            "Mealy and Moore output event timing can differ; PPA does not establish cycle equivalence",
            "Only same-pattern/same-overlap Mealy–Moore comparisons are controlled",
            "Global Pareto across different patterns and overlap settings is exploratory only",
            "Reported power/area/arrival optimization not equivalent to functional quality",
        ],
        "historic_sources_sha256": source_hash,
    }
    files.append(write_json("day30_fsm_20_comparison_summary.json", doc))

    report = [
        "# Day 30 — Complete FSM architecture and PPA comparison", "",
        "## Verification summary", "",
        "- Extended FSM implementations: **20/20**",
        "- Matched Mealy/Moore comparisons: **10/10**",
        "- Pareto comparison records: **20/20**",
        "- Original `fsm_original_1011`: preserved as separate historical reference", "",
        "## Matched Mealy/Moore pairs", "",
        "| Pattern | Overlap | Mealy area | Moore area | Moore area change | Mealy power | Moore power | Moore power change |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in pairs:
        report.append(f"| `{r['pattern']}` | {r['overlap']} | {r['mealy_area_um2']:.3f} | {r['moore_area_um2']:.3f} | {r['area_um2_change_pct']:+.2f}% | {r['mealy_total_power_uw']:.3f} | {r['moore_total_power_uw']:.3f} | {r['total_power_uw_change_pct']:+.2f}% |")
    report.extend([
        "", "Values: cell area in µm² and estimated power in µW.", "",
        "## Pareto analysis", "",
        "Criteria: lower mapped area, lower estimated total power, lower reported data arrival.",
        f"Exploratory global Pareto members: **{len(exploratory)}** / 20.",
        f"Controlled matched-pair Pareto members: **{len(controlled)}** / 20.",
        "The controlled comparisons (same pattern, same overlap) are the appropriate architecture comparison.",
        "Global Pareto mixes functionally different pattern/mode choices and must not be used to recommend a substitute detector.",
        "", "## Historical methodology", "",
        "- Arrival-based ADP = mapped area × reported arrival, µm²·ns.",
        "- Arrival-based PDP = estimated power × reported arrival, fJ.",
        "- Area-power product = mapped area × estimated power, µm²·µW.",
        "- Signed percentage change = 100 × (Moore − Mealy) / Mealy.",
        "", "## Limitations", "",
    ])
    for item in doc["constraints_and_limits"]:
        report.append("- " + item)
    report.extend(["", "**DAY 30 FSM 20-CONFIGURATION COMPARISON: PASS**", ""])
    md_path = OUT / "day30_fsm_20_comparison_report.md"
    md_path.write_text("\n".join(report), encoding="utf-8")
    files.append(md_path)

    images = plot_graphs(efficiency, pareto)
    check(len(images) == 6 and all(f.stat().st_size > 0 for f in images), "Expected 6 nonempty graphs")
    for p, digest in source_hash.items():
        check(hashlib.sha256(Path(p).read_bytes()).hexdigest() == digest,
              f"Source file unexpectedly modified: {p}")

    print("\n========== FINAL FSM COMPARISON SUMMARY ==========")
    print(f"EXTENDED CONFIGURATIONS: {len(efficiency)}/20")
    print(f"MATCHED MEALY/MOORE PAIRS: {len(pairs)}/10")
    print(f"PARETO RECORDS: {len(pareto)}/20")
    print(f"EXPLORATORY GLOBAL PARETO VARIANTS: {len(exploratory)}")
    print(f"CONTROLLED PARETO VARIANTS: {len(controlled)}")
    print(f"GRAPHS GENERATED: {len(images)}/6")
    print("DAY 26 AND DAY 27 INPUT FILES: UNCHANGED")
    for path in files:
        print("REPORT:", path.relative_to(ROOT))
    print("GRAPHS DIRECTORY:", GRAPHS.relative_to(ROOT))
    print("DAY 30 FSM 20-CONFIGURATION COMPARISON: PASS")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, AssertionError, RuntimeError, TypeError) as exc:
        print(f"DAY 30 FSM 20-CONFIGURATION COMPARISON: FAIL — {exc}", file=sys.stderr)
        sys.exit(1)
