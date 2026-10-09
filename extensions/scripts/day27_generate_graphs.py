#!/usr/bin/env python3

"""
DAY 27 - STEP 5
FSM architecture comparison and visualization.

Reads existing Day 27 measurement and Pareto reports.
Does not rerun synthesis, simulation, STA or power analysis.
"""

import csv
import json
import math
import sys
from pathlib import Path

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ImportError:
    print(
        "ERROR: matplotlib is not installed.\n"
        "Run: python3 -m pip install matplotlib",
        file=sys.stderr
    )
    sys.exit(1)


ROOT = Path.home() / "Mtech_project" / "AI_RTL_Verification"

RESULT_DIR = ROOT / "extensions/results/day27"
GRAPH_DIR = RESULT_DIR / "graphs"

METRICS_CSV = RESULT_DIR / "day27_efficiency_metrics.csv"
PARETO_JSON = RESULT_DIR / "day27_pareto_analysis.json"

SUMMARY_JSON = RESULT_DIR / "day27_graph_summary.json"
SUMMARY_TXT = RESULT_DIR / "day27_graph_summary.txt"

GRAPH_FILES = {
    "area": "01_fsm_area_comparison.png",
    "power": "02_fsm_power_comparison.png",
    "timing": "03_fsm_arrival_time_comparison.png",
    "adp": "04_fsm_area_delay_product.png",
    "pdp": "05_fsm_power_delay_product.png",
    "pareto": "06_fsm_pareto_tradeoff.png",
}

REQUIRED_FIELDS = [
    "configuration",
    "area_um2",
    "total_power_uw",
    "data_arrival_ns",
    "setup_slack_ns",
]


def load_metrics():
    if not METRICS_CSV.is_file():
        raise FileNotFoundError(
            f"Missing input file: {METRICS_CSV}"
        )

    with METRICS_CSV.open(
        newline="",
        encoding="utf-8"
    ) as handle:
        reader = csv.DictReader(handle)

        missing = [
            field for field in REQUIRED_FIELDS
            if field not in (reader.fieldnames or [])
        ]

        if missing:
            raise ValueError(
                f"Missing CSV columns: {missing}"
            )

        records = list(reader)

    if len(records) != 13:
        raise ValueError(
            f"Expected 13 configurations, found {len(records)}"
        )

    parsed = []

    for record in records:
        name = record["configuration"].strip()

        entry = {"configuration": name}

        for field in REQUIRED_FIELDS[1:]:
            value = float(record[field])

            if not math.isfinite(value):
                raise ValueError(
                    f"Nonfinite {field} in {name}"
                )

            entry[field] = value

        for field in (
            "area_um2",
            "total_power_uw",
            "data_arrival_ns",
        ):
            if entry[field] <= 0:
                raise ValueError(
                    f"{name}: {field} must be positive"
                )

        entry["adp_um2_ns"] = (
            entry["area_um2"]
            * entry["data_arrival_ns"]
        )

        entry["pdp_fj"] = (
            entry["total_power_uw"]
            * entry["data_arrival_ns"]
            / 1000.0
        )

        parsed.append(entry)

    names = [r["configuration"] for r in parsed]

    if len(set(names)) != 13:
        raise ValueError("Duplicate configuration names")

    return sorted(
        parsed,
        key=lambda r: r["configuration"]
    )


def load_pareto():
    if not PARETO_JSON.is_file():
        raise FileNotFoundError(
            f"Missing Pareto JSON: {PARETO_JSON}"
        )

    document = json.loads(
        PARETO_JSON.read_text(encoding="utf-8")
    )

    if document.get("configuration_count") != 13:
        raise ValueError(
            "Pareto JSON configuration count mismatch"
        )

    if document.get("status") != "PASS":
        raise ValueError(
            "Pareto JSON status is not PASS"
        )

    return document


def style_for(name):
    if name.startswith("mealy_"):
        return "#3274A1"

    if name.startswith("moore_"):
        return "#E1812C"

    return "#648C5A"


def make_bar_chart(
    records,
    field,
    title,
    ylabel,
    filename
):
    ordered = sorted(
        records,
        key=lambda item: item[field]
    )

    names = [
        item["configuration"]
        for item in ordered
    ]

    values = [
        item[field]
        for item in ordered
    ]

    colors = [
        style_for(name)
        for name in names
    ]

    fig, ax = plt.subplots(figsize=(12, 8))

    positions = list(range(len(names)))

    ax.barh(
        positions,
        values,
        color=colors
    )

    ax.set_yticks(positions)
    ax.set_yticklabels(names, fontsize=9)

    ax.set_xlabel(ylabel)
    ax.set_title(title, fontsize=14)

    ax.grid(
        axis="x",
        linestyle="--",
        alpha=0.35
    )

    ax.set_axisbelow(True)

    maximum = max(values)

    ax.set_xlim(
        0,
        maximum * 1.20
    )

    for position, value in zip(positions, values):
        ax.text(
            value + maximum * 0.01,
            position,
            f"{value:.4f}",
            va="center",
            fontsize=8
        )

    fig.tight_layout()

    output = GRAPH_DIR / filename

    fig.savefig(
        output,
        dpi=200,
        bbox_inches="tight"
    )

    plt.close(fig)

    return output


def make_pareto_chart(records, pareto):
    front = set(
        pareto["global_pareto_front"]
    )

    record_names = {
        record["configuration"]
        for record in records
    }

    if not front:
        raise ValueError("Global Pareto front is empty")

    if not front.issubset(record_names):
        raise ValueError(
            "Pareto JSON references unknown configurations"
        )

    fig, ax = plt.subplots(figsize=(12, 8))

    for record in records:
        name = record["configuration"]

        is_pareto = name in front

        ax.scatter(
            record["area_um2"],
            record["total_power_uw"],
            s=170 if is_pareto else 65,
            marker="*" if is_pareto else "o",
            color=style_for(name),
            edgecolor="black" if is_pareto else "none",
            linewidth=0.8,
            alpha=0.95
        )

        ax.annotate(
            name,
            (
                record["area_um2"],
                record["total_power_uw"]
            ),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=7
        )

    ax.set_xlabel("Mapped area (um²)")
    ax.set_ylabel("Estimated total power (uW)")

    ax.set_title(
        "FSM area-power trade-off\n"
        "Stars = globally Pareto-optimal across "
        "area, power and arrival time"
    )

    ax.grid(
        linestyle="--",
        alpha=0.35
    )

    fig.tight_layout()

    output = (
        GRAPH_DIR
        / GRAPH_FILES["pareto"]
    )

    fig.savefig(
        output,
        dpi=200,
        bbox_inches="tight"
    )

    plt.close(fig)

    return output


def validate_graphs(paths):
    if len(paths) != 6:
        raise ValueError(
            f"Expected 6 graphs, found {len(paths)}"
        )

    for path in paths:
        if not path.is_file():
            raise FileNotFoundError(
                f"Missing graph: {path}"
            )

        if path.stat().st_size < 1000:
            raise ValueError(
                f"Graph appears empty: {path}"
            )

        with path.open("rb") as handle:
            signature = handle.read(8)

        if signature != b"\x89PNG\r\n\x1a\n":
            raise ValueError(
                f"Invalid PNG signature: {path}"
            )


def save_summary(records, pareto, paths):
    best_area = min(
        records,
        key=lambda r: r["area_um2"]
    )

    best_power = min(
        records,
        key=lambda r: r["total_power_uw"]
    )

    best_arrival = min(
        records,
        key=lambda r: r["data_arrival_ns"]
    )

    best_adp = min(
        records,
        key=lambda r: r["adp_um2_ns"]
    )

    best_pdp = min(
        records,
        key=lambda r: r["pdp_fj"]
    )

    summary = {
        "day": 27,
        "step": 5,
        "status": "PASS",
        "configurations_analyzed": len(records),
        "graphs_generated": len(paths),
        "global_pareto_front": (
            pareto["global_pareto_front"]
        ),
        "best_area": {
            "configuration": best_area["configuration"],
            "value_um2": best_area["area_um2"],
        },
        "best_power": {
            "configuration": best_power["configuration"],
            "value_uw": best_power["total_power_uw"],
        },
        "best_arrival": {
            "configuration": best_arrival["configuration"],
            "value_ns": best_arrival["data_arrival_ns"],
        },
        "best_adp": {
            "configuration": best_adp["configuration"],
            "value_um2_ns": best_adp["adp_um2_ns"],
        },
        "best_pdp": {
            "configuration": best_pdp["configuration"],
            "value_fj": best_pdp["pdp_fj"],
        },
        "graphs": [
            str(path.relative_to(ROOT))
            for path in paths
        ],
        "limitations": [
            "Pre-layout mapped area only",
            "Power based on assumed switching activity",
            "Timing uses reported data arrival time",
            "Global Pareto comparison mixes FSM semantics",
            "No physical layout or post-route analysis",
        ],
    }

    SUMMARY_JSON.write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8"
    )

    lines = [
        "=" * 70,
        "DAY 27 - STEP 5 - FSM GRAPHICAL ANALYSIS",
        "=" * 70,
        "",
        f"Configurations: {len(records)}",
        f"Graphs generated: {len(paths)}",
        "",
        "BEST METRICS",
        "-" * 70,
        (
            f"Minimum area: "
            f"{best_area['configuration']} "
            f"({best_area['area_um2']:.3f} um2)"
        ),
        (
            f"Minimum estimated power: "
            f"{best_power['configuration']} "
            f"({best_power['total_power_uw']:.3f} uW)"
        ),
        (
            f"Minimum arrival time: "
            f"{best_arrival['configuration']} "
            f"({best_arrival['data_arrival_ns']:.3f} ns)"
        ),
        (
            f"Minimum ADP: "
            f"{best_adp['configuration']} "
            f"({best_adp['adp_um2_ns']:.4f} um2*ns)"
        ),
        (
            f"Minimum PDP: "
            f"{best_pdp['configuration']} "
            f"({best_pdp['pdp_fj']:.6f} fJ)"
        ),
        "",
        "GLOBAL PARETO FRONT",
        "-" * 70,
    ]

    lines.extend(
        pareto["global_pareto_front"]
    )

    lines.extend([
        "",
        "GENERATED GRAPHS",
        "-" * 70,
    ])

    lines.extend(
        str(path.relative_to(ROOT))
        for path in paths
    )

    lines.extend([
        "",
        "LIMITATIONS",
        "-" * 70,
        "Results are pre-layout estimates.",
        "Power uses assumed switching activity.",
        "Arrival time is a timing proxy.",
        "Global Pareto rankings mix FSM behaviors.",
        "",
        "DAY 27 STEP 5: PASS",
        "",
    ])

    SUMMARY_TXT.write_text(
        "\n".join(lines),
        encoding="utf-8"
    )


def main():
    print("=" * 70)
    print("DAY 27 - STEP 5")
    print("FSM GRAPHICAL COMPARISON")
    print("=" * 70)

    GRAPH_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    records = load_metrics()
    pareto = load_pareto()

    paths = []

    specifications = [
        (
            "area_um2",
            "FSM Standard-Cell Area Comparison",
            "Area (um²)",
            GRAPH_FILES["area"],
        ),
        (
            "total_power_uw",
            "FSM Estimated Total Power Comparison",
            "Power (uW)",
            GRAPH_FILES["power"],
        ),
        (
            "data_arrival_ns",
            "FSM Data Arrival Time Comparison",
            "Arrival time (ns)",
            GRAPH_FILES["timing"],
        ),
        (
            "adp_um2_ns",
            "FSM Area-Delay Product Comparison",
            "ADP (um² × ns)",
            GRAPH_FILES["adp"],
        ),
        (
            "pdp_fj",
            "FSM Power-Delay Product Comparison",
            "PDP (fJ)",
            GRAPH_FILES["pdp"],
        ),
    ]

    for field, title, ylabel, filename in specifications:
        path = make_bar_chart(
            records,
            field,
            title,
            ylabel,
            filename
        )

        paths.append(path)
        print("[PASS]", path.name)

    pareto_path = make_pareto_chart(
        records,
        pareto
    )

    paths.append(pareto_path)
    print("[PASS]", pareto_path.name)

    validate_graphs(paths)
    save_summary(records, pareto, paths)

    # Validate both generated summary files.
    saved = json.loads(
        SUMMARY_JSON.read_text(encoding="utf-8")
    )

    if (
        saved["status"] != "PASS"
        or saved["graphs_generated"] != 6
        or saved["configurations_analyzed"] != 13
    ):
        raise ValueError(
            "Summary JSON validation failed"
        )

    if (
        "DAY 27 STEP 5: PASS"
        not in SUMMARY_TXT.read_text(encoding="utf-8")
    ):
        raise ValueError(
            "Summary TXT validation failed"
        )

    print()
    print("========== FINAL VERIFICATION ==========")
    print("CONFIGURATIONS ANALYZED: 13")
    print("GRAPHS GENERATED: 6")
    print("PNG VALIDATION: PASS")
    print("JSON VALIDATION: PASS")
    print("TEXT REPORT VALIDATION: PASS")
    print("DAY 27 STEP 5: PASS")

    print()
    print("Generated reports:")
    print(SUMMARY_JSON.relative_to(ROOT))
    print(SUMMARY_TXT.relative_to(ROOT))


if __name__ == "__main__":
    try:
        main()
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
    ) as exc:
        print(
            "DAY 27 STEP 5: FAIL -",
            exc,
            file=sys.stderr
        )
        sys.exit(1)
