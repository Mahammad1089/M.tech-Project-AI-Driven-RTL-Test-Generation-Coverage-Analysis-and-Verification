#!/usr/bin/env python3

import csv
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path.home() / "Mtech_project" / "AI_RTL_Verification"
OUT = ROOT / "extensions/results/day30/uart/ppa"
LIB = ROOT / "extensions/technology/nangate45/NangateOpenCellLibrary_typical.lib"

DESIGNS = [
    ("baseline_tx", "uart_tx", "extensions/rtl/uart/uart_tx.v"),
    ("optimized_tx", "uart_tx_opt", "extensions/rtl/uart/optimized/uart_tx_opt.v"),
    ("baseline_rx", "uart_rx", "extensions/rtl/uart/uart_rx.v"),
    ("optimized_rx", "uart_rx_opt", "extensions/rtl/uart/optimized/uart_rx_opt.v"),
]

def main():
    OUT.mkdir(parents=True, exist_ok=True)

    if not LIB.is_file():
        print(f"[FAIL] Missing Liberty library: {LIB}")
        return 1

    rows = []
    failed = False

    for name, top, relative_path in DESIGNS:
        rtl = ROOT / relative_path
        netlist = OUT / f"{name}_mapped.v"
        log = OUT / f"{name}_synthesis.log"
        json_path = OUT / f"{name}_mapped.json"

        print(f"\n========== {name.upper()} ==========", flush=True)

        if not rtl.is_file():
            print(f"[FAIL] Missing RTL: {rtl}")
            failed = True
            continue

        script = f"""
read_verilog {rtl}
hierarchy -check -top {top}
synth -top {top}
dfflibmap -liberty {LIB}
abc -liberty {LIB}
clean
tee -o {OUT / (name + "_stat.txt")} stat -liberty {LIB}
write_verilog -noattr -noexpr {netlist}
write_json {json_path}
"""

        script_file = OUT / f"{name}_yosys.ys"
        script_file.write_text(script, encoding="utf-8")

        with log.open("w", encoding="utf-8") as handle:
            result = subprocess.run(
                ["yosys", "-s", str(script_file)],
                cwd=ROOT,
                stdout=handle,
                stderr=subprocess.STDOUT,
            )

        if result.returncode != 0:
            print(f"[FAIL] Yosys synthesis; inspect {log}")
            failed = True
            continue

        if not netlist.is_file() or not json_path.is_file():
            print("[FAIL] Expected synthesis artifacts missing")
            failed = True
            continue

        data = json.loads(json_path.read_text(encoding="utf-8"))
        module = data.get("modules", {}).get(top)

        if module is None:
            print(f"[FAIL] Top module {top} missing from mapped JSON")
            failed = True
            continue

        cells = module.get("cells", {})
        counts = {}

        for cell in cells.values():
            cell_type = cell["type"]
            counts[cell_type] = counts.get(cell_type, 0) + 1

        stat_text = (OUT / f"{name}_stat.txt").read_text(
            encoding="utf-8", errors="replace"
        )

        # Match the area reported by Yosys, rather than treating
        # generic cell counts as physical area.
        matches = re.findall(
            r"Chip area for module\s+['\\]?[^\s:]+['\\]?\s*:\s*"
            r"([0-9]+(?:\.[0-9]+)?)",
            stat_text,
            flags=re.IGNORECASE,
        )

        if not matches:
            print("[FAIL] Technology-mapped chip area not found")
            print("Inspect:", OUT / f"{name}_stat.txt")
            failed = True
            continue

        area = float(matches[-1])

        if area <= 0:
            print("[FAIL] Nonpositive mapped area")
            failed = True
            continue

        row = {
            "design": name,
            "top_module": top,
            "clks_per_bit": 16,
            "technology": "Nangate45 typical",
            "mapped_cells": len(cells),
            "cell_area_um2": area,
            "mapped_netlist": str(netlist.relative_to(ROOT)),
            "synthesis_log": str(log.relative_to(ROOT)),
        }

        rows.append(row)

        print("[PASS] Technology mapping completed")
        print("Mapped cells:", len(cells))
        print(f"Cell area: {area:.6f} um^2")
        print("Netlist:", netlist)

        print("Cell distribution:")
        for cell_type, count in sorted(counts.items()):
            print(f"  {cell_type}: {count}")

    if len(rows) != len(DESIGNS) or failed:
        print("\n[FAIL] One or more UART synthesis runs failed")
        return 1

    csv_path = OUT / "day30_uart_area_comparison.csv"
    json_report = OUT / "day30_uart_area_comparison.json"

    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    by_name = {row["design"]: row for row in rows}

    comparisons = []

    for block in ("tx", "rx"):
        baseline = by_name[f"baseline_{block}"]["cell_area_um2"]
        optimized = by_name[f"optimized_{block}"]["cell_area_um2"]

        reduction = (baseline - optimized) / baseline * 100

        comparisons.append({
            "block": block.upper(),
            "baseline_area_um2": baseline,
            "optimized_area_um2": optimized,
            "area_reduction_percent": reduction,
            "optimized_area_is_smaller": optimized < baseline,
        })

    report = {
        "status": "PASS",
        "scope": "Technology-mapped synthesis area only",
        "technology": "Nangate45 typical",
        "clks_per_bit": 16,
        "limitations": [
            "Pre-layout standard-cell area, not routed area",
            "No timing analysis performed in this step",
            "No dynamic or leakage power analysis performed in this step",
            "Functional equivalence supported by earlier simulation tests",
        ],
        "designs": rows,
        "comparisons": comparisons,
    }

    json_report.write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
    )

    print("\n========== UART AREA COMPARISON ==========")

    for item in comparisons:
        print(
            f"{item['block']}: "
            f"baseline={item['baseline_area_um2']:.6f} um^2, "
            f"optimized={item['optimized_area_um2']:.6f} um^2, "
            f"reduction={item['area_reduction_percent']:.2f}%"
        )

        if not item["optimized_area_is_smaller"]:
            print(
                f"[NOTE] {item['block']} optimization did not "
                "reduce mapped cell area"
            )

    print("\nCSV:", csv_path)
    print("JSON:", json_report)
    print("DAY 30 UART TECHNOLOGY-MAPPED AREA: PASS")

    return 0

if __name__ == "__main__":
    sys.exit(main())
