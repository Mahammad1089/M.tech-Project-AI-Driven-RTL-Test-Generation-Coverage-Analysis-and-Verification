#!/usr/bin/env python3

import csv
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path.home() / "Mtech_project" / "AI_RTL_Verification"

OUT = ROOT / "extensions/results/day30/fifo_ppa"

LIB = (
    ROOT / "extensions/technology/nangate45"
    / "NangateOpenCellLibrary_typical.lib"
)

DESIGNS = [
    (
        "baseline",
        "fifo",
        ROOT / "rtl/fifo.v"
    ),
    (
        "optimized",
        "fifo_opt",
        ROOT / "extensions/rtl/optimized/fifo_opt.v"
    ),
]

CONFIGURATIONS = [
    ("w8_d4", 8, 4, 2),
    ("w8_d8", 8, 8, 3),
    ("w16_d4", 16, 4, 2),
    ("w8_d16", 8, 16, 4),
]

AREA_PATTERN = re.compile(
    r"Chip area for module[^\n:]*:\s*"
    r"([0-9]+(?:\.[0-9]+)?)",
    re.IGNORECASE
)


def run_synthesis(name, top, rtl, config):
    label, width, depth, addr_width = config

    design_id = f"{name}_{label}"

    netlist = OUT / f"{design_id}_mapped.v"
    json_file = OUT / f"{design_id}_mapped.json"
    stat_file = OUT / f"{design_id}_stat.txt"
    script_file = OUT / f"{design_id}_yosys.ys"
    log_file = OUT / f"{design_id}_synthesis.log"

    print(
        f"\n========== FIFO SYNTHESIS: "
        f"{design_id.upper()} ==========",
        flush=True
    )

    if not rtl.is_file():
        print("[FAIL] RTL not found:", rtl)
        return None

    script = f"""
read_verilog {rtl}
chparam -set DATA_WIDTH {width} -set DEPTH {depth} -set ADDR_WIDTH {addr_width} {top}
hierarchy -check -top {top}
synth -top {top}
dfflibmap -liberty {LIB}
abc -liberty {LIB}
clean
tee -o {stat_file} stat -liberty {LIB}
write_verilog -noattr -noexpr {netlist}
write_json {json_file}
"""

    script_file.write_text(
        script,
        encoding="utf-8"
    )

    try:
        with log_file.open("w", encoding="utf-8") as handle:
            process = subprocess.run(
                ["yosys", "-s", str(script_file)],
                cwd=ROOT,
                stdout=handle,
                stderr=subprocess.STDOUT,
                timeout=180,
            )
    except (OSError, subprocess.TimeoutExpired) as exc:
        print("[FAIL] Yosys execution:", exc)
        return None

    if process.returncode != 0:
        print("[FAIL] Yosys synthesis failed")
        print("Log:", log_file)
        return None

    required_files = [
        netlist,
        json_file,
        stat_file,
    ]

    for path in required_files:
        if not path.is_file() or path.stat().st_size == 0:
            print("[FAIL] Missing synthesis output:", path)
            return None

    stat_text = stat_file.read_text(
        encoding="utf-8",
        errors="replace"
    )

    areas = AREA_PATTERN.findall(stat_text)

    if len(areas) != 1:
        print("[FAIL] Could not extract unique mapped area")
        print("Statistics file:", stat_file)
        print(stat_text[-2000:])
        return None

    area = float(areas[0])

    if area <= 0:
        print("[FAIL] Invalid mapped area:", area)
        return None

    data = json.loads(
        json_file.read_text(encoding="utf-8")
    )

    modules = data.get("modules", {})

    if top not in modules:
        print("[FAIL] Expected top module not present:", top)
        return None

    cells = modules[top].get("cells", {})

    if not cells:
        print("[FAIL] No mapped cells found")
        return None

    cell_counts = {}

    for cell in cells.values():
        cell_type = cell["type"]

        # All synthesized cells should belong to the
        # technology library, not generic Yosys primitives.
        if cell_type.startswith("$"):
            print("[FAIL] Unmapped Yosys cell:", cell_type)
            return None

        cell_counts[cell_type] = (
            cell_counts.get(cell_type, 0) + 1
        )

    print("[PASS] Technology mapping completed")
    print("Configuration:", label)
    print("Data width:", width)
    print("Depth:", depth)
    print("Address width:", addr_width)
    print("Mapped cells:", len(cells))
    print(f"Cell area: {area:.6f} um^2")
    print("Netlist:", netlist)

    return {
        "design": name,
        "configuration": label,
        "data_width": width,
        "depth": depth,
        "addr_width": addr_width,
        "top_module": top,
        "technology": "Nangate45 typical",
        "mapped_cells": len(cells),
        "cell_area_um2": area,
        "cell_distribution": cell_counts,
        "netlist": str(netlist.relative_to(ROOT)),
        "synthesis_log": str(log_file.relative_to(ROOT)),
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    if not LIB.is_file():
        print("[FAIL] Nangate45 Liberty file missing")
        return 1

    print("=" * 70)
    print("DAY 30 STEP 5C - FIFO TECHNOLOGY-MAPPED AREA ANALYSIS")
    print("=" * 70)

    records = []
    failed = []

    for config in CONFIGURATIONS:
        for name, top, rtl in DESIGNS:
            record = run_synthesis(
                name,
                top,
                rtl,
                config,
            )

            if record is None:
                failed.append(
                    f"{name}_{config[0]}"
                )
            else:
                records.append(record)

    if failed or len(records) != 8:
        print("\n========== FINAL RESULT ==========")
        print("[FAIL] Incomplete FIFO synthesis analysis")
        print("Failed designs:", ", ".join(failed))
        return 1

    by_key = {
        (
            record["design"],
            record["configuration"],
        ): record
        for record in records
    }

    comparison = []

    print("\n========== FIFO AREA COMPARISON ==========")

    for label, width, depth, addr_width in CONFIGURATIONS:
        baseline = by_key[("baseline", label)]
        optimized = by_key[("optimized", label)]

        baseline_area = baseline["cell_area_um2"]
        optimized_area = optimized["cell_area_um2"]

        reduction = (
            (baseline_area - optimized_area)
            / baseline_area * 100.0
        )

        row = {
            "configuration": label,
            "data_width": width,
            "depth": depth,
            "addr_width": addr_width,
            "baseline_area_um2": baseline_area,
            "optimized_area_um2": optimized_area,
            "area_reduction_percent": reduction,
            "baseline_mapped_cells": baseline["mapped_cells"],
            "optimized_mapped_cells": optimized["mapped_cells"],
        }

        comparison.append(row)

        print(f"\nConfiguration: {label}")
        print(f"Baseline area:  {baseline_area:.6f} um^2")
        print(f"Optimized area: {optimized_area:.6f} um^2")
        print(f"Area reduction: {reduction:+.2f}%")

        if reduction > 0:
            print("[RESULT] Optimized FIFO uses less cell area")
        elif reduction < 0:
            print("[RESULT] Optimized FIFO uses more cell area")
        else:
            print("[RESULT] Both have equal mapped cell area")

    csv_file = OUT / "day30_fifo_area_comparison.csv"
    json_file = OUT / "day30_fifo_area_comparison.json"

    with csv_file.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(comparison[0].keys())
        )

        writer.writeheader()
        writer.writerows(comparison)

    report = {
        "status": "SYNTHESIS_COMPLETED",
        "technology": "Nangate45 typical",
        "scope": "Pre-layout standard-cell area",
        "configurations": len(CONFIGURATIONS),
        "mapped_implementations": len(records),
        "results": records,
        "comparison": comparison,
        "limitations": [
            "No placement and routing",
            "No routed parasitics",
            "Timing analysis not included",
            "Power analysis not included",
            "Functional equivalence supported by "
            "separate simulation tests",
        ],
    }

    json_file.write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8"
    )

    print("\n========== FINAL VALIDATION ==========")
    print("[PASS] All eight FIFO implementations mapped")
    print("CSV:", csv_file)
    print("JSON:", json_file)
    print("DAY 30 FIFO AREA ANALYSIS: PASS")

    return 0


if __name__ == "__main__":
    sys.exit(main())
