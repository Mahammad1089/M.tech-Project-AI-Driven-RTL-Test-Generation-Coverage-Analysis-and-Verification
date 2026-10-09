#!/usr/bin/env python3

import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path.cwd()
UART = ROOT / "extensions/results/day30/uart"
PPA = UART / "ppa"
OUT = UART / "final_report"

CPBS = (8, 16, 32, 64)

TESTS = {
    "tx_equivalence": {
        "folder": "tx_equivalence",
        "prefix": "tx",
        "marker": "DAY 30 UART TX EQUIVALENCE: PASS",
        "expected": {
            "FAILED CHECKS": 0,
            "COMPLETE FRAMES": 273,
        },
    },
    "rx_equivalence": {
        "folder": "rx_equivalence",
        "prefix": "rx",
        "marker": "DAY 30 UART RX EQUIVALENCE: PASS",
        "expected": {
            "FAILED CHECKS": 0,
            "FRAMES DRIVEN": 260,
            "VALID FRAMES": 257,
            "FRAMING ERRORS": 3,
        },
    },
    "hybrid_loopback": {
        "folder": "hybrid_loopback",
        "prefix": "hybrid",
        "marker": "DAY 30 UART HYBRID LOOPBACK: PASS",
        "expected": {
            "TOTAL CHECKS": 194,
            "PASSED CHECKS": 194,
            "FAILED CHECKS": 0,
            "TX FRAMES": 38,
            "RX VALID FRAMES": 38,
            "RX FRAMING ERRORS": 1,
        },
    },
}


def fail(message):
    raise ValueError(message)


def read_csv(path):
    if not path.is_file():
        fail(f"Missing CSV: {path}")

    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    if not rows:
        fail(f"Empty CSV: {path}")

    result = {}

    for row in rows:
        name = row.get("design")

        if not name or name in result:
            fail(f"Invalid or duplicate design in {path}")

        result[name] = row

    required = {
        "baseline_tx",
        "optimized_tx",
        "baseline_rx",
        "optimized_rx",
    }

    if set(result) != required:
        fail(
            f"Unexpected designs in {path}: "
            f"{sorted(result)}"
        )

    return result


def get_number(row, key):
    if key not in row:
        fail(f"Missing CSV column: {key}")

    try:
        return float(row[key])
    except (ValueError, TypeError):
        fail(f"Invalid numeric value for {key}: {row[key]}")


def verify_logs():
    print("========== UART FUNCTIONAL LOG AUDIT ==========")

    evidence = {}
    total_checks = 0

    for test_name, config in TESTS.items():
        evidence[test_name] = []

        for cpb in CPBS:
            log = (
                UART
                / config["folder"]
                / f"{config['prefix']}_{cpb}.log"
            )

            if not log.is_file():
                fail(f"Missing log: {log}")

            content = log.read_text(
                encoding="utf-8",
                errors="replace",
            )

            if config["marker"] not in content:
                fail(f"PASS marker missing in {log}")

            if re.search(r"(?m)^\s*\[FAIL\]", content):
                fail(f"Failure message found in {log}")

            values = {}

            labels = set(config["expected"]) | {
                "TOTAL CHECKS",
                "PASSED CHECKS",
                "FAILED CHECKS",
            }

            for label in labels:
                match = re.search(
                    rf"(?m)^\s*{re.escape(label)}:\s*(\d+)\s*$",
                    content,
                )

                if not match:
                    fail(f"Missing {label} in {log}")

                values[label] = int(match.group(1))

            for label, expected in config["expected"].items():
                if values[label] != expected:
                    fail(
                        f"{log}: {label} = {values[label]}, "
                        f"expected {expected}"
                    )

            if (
                values["TOTAL CHECKS"]
                != values["PASSED CHECKS"]
                + values["FAILED CHECKS"]
            ):
                fail(f"Check-count inconsistency in {log}")

            if values["TOTAL CHECKS"] <= 0:
                fail(f"No checks reported in {log}")

            total_checks += values["PASSED CHECKS"]

            evidence[test_name].append({
                "cpb": cpb,
                "status": "PASS",
                "values": values,
                "log": str(log.relative_to(ROOT)),
            })

            print(
                f"[PASS] {test_name}, CPB={cpb}, "
                f"checks={values['PASSED CHECKS']}"
            )

    print(f"TOTAL VERIFIED PASSING CHECKS: {total_checks}")
    return evidence, total_checks


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    evidence, total_checks = verify_logs()

    area_csv = PPA / "day30_uart_area_comparison.csv"
    timing_csv = PPA / "day30_uart_timing_comparison.csv"
    power_csv = PPA / "day30_uart_power_comparison.csv"

    areas = read_csv(area_csv)
    timings = read_csv(timing_csv)
    powers = read_csv(power_csv)

    designs = {}

    print("\n========== UART PPA DATA AUDIT ==========")

    for name in areas:
        area = get_number(areas[name], "cell_area_um2")
        slack = get_number(
            timings[name], "worst_setup_slack_ns"
        )
        power = get_number(
            powers[name], "total_power_uw"
        )

        if min(area, power) <= 0:
            fail(f"Nonpositive area/power for {name}")

        if timings[name].get("setup_status") != "MET":
            fail(f"Setup timing not met for {name}")

        for dataset, rows in (
            ("area", areas),
            ("timing", timings),
            ("power", powers),
        ):
            if int(rows[name].get("clks_per_bit", -1)) != 16:
                fail(f"Unexpected CPB for {name} in {dataset}")

        designs[name] = {
            "area_um2": area,
            "setup_slack_ns": slack,
            "estimated_power_uw": power,
        }

        print(
            f"[PASS] {name}: area={area:.3f} um^2, "
            f"slack={slack:.3f} ns, "
            f"power={power:.3f} uW"
        )

    configurations = {
        "baseline": ("baseline_tx", "baseline_rx"),
        "fully_optimized": ("optimized_tx", "optimized_rx"),
        "hybrid": ("baseline_tx", "optimized_rx"),
    }

    summary = {}

    for config_name, (tx, rx) in configurations.items():
        summary[config_name] = {
            "tx": tx,
            "rx": rx,
            "combined_area_um2": (
                designs[tx]["area_um2"]
                + designs[rx]["area_um2"]
            ),
            "combined_estimated_power_uw": (
                designs[tx]["estimated_power_uw"]
                + designs[rx]["estimated_power_uw"]
            ),
            "minimum_individual_setup_slack_ns": min(
                designs[tx]["setup_slack_ns"],
                designs[rx]["setup_slack_ns"],
            ),
        }

    baseline = summary["baseline"]
    hybrid = summary["hybrid"]

    area_reduction = (
        (
            baseline["combined_area_um2"]
            - hybrid["combined_area_um2"]
        )
        / baseline["combined_area_um2"]
        * 100
    )

    power_reduction = (
        (
            baseline["combined_estimated_power_uw"]
            - hybrid["combined_estimated_power_uw"]
        )
        / baseline["combined_estimated_power_uw"]
        * 100
    )

    report = {
        "status": "PASS",
        "report": "Day 30 UART functional and PPA evidence",
        "functional_evidence": evidence,
        "total_verified_checks": total_checks,
        "technology": "Nangate45 typical",
        "ppa_clks_per_bit": 16,
        "clock_period_ns": 10.0,
        "designs": designs,
        "configurations": summary,
        "hybrid_vs_baseline": {
            "area_reduction_percent": area_reduction,
            "estimated_power_reduction_percent": power_reduction,
        },
        "preferred_configuration": {
            "tx": "baseline_tx",
            "rx": "optimized_rx",
            "reason": (
                "Lowest combined mapped area and assumed-activity "
                "power among the three evaluated configurations"
            ),
        },
        "limitations": [
            "Simulation-based functional verification, not formal proof",
            "Area is technology-mapped, pre-layout area",
            "Power uses assumed switching activity, not VCD/SAIF",
            "Combined PPA is the sum of separately analyzed modules",
            "Integrated hybrid STA is not performed",
            "Timing numbers are from independently analyzed modules",
            "Post-layout timing, power and area are not available",
            "FIFO and FSM extension requirements are outside this report",
        ],
        "source_files": [
            str(area_csv.relative_to(ROOT)),
            str(timing_csv.relative_to(ROOT)),
            str(power_csv.relative_to(ROOT)),
        ],
    }

    json_path = OUT / "day30_uart_final_report.json"
    csv_path = OUT / "day30_uart_architecture_comparison.csv"
    md_path = OUT / "day30_uart_final_report.md"

    with csv_path.open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.writer(handle)
        writer.writerow([
            "configuration",
            "tx_design",
            "rx_design",
            "combined_area_um2",
            "combined_estimated_power_uw",
            "minimum_individual_setup_slack_ns",
        ])

        for name, row in summary.items():
            writer.writerow([
                name,
                row["tx"],
                row["rx"],
                f"{row['combined_area_um2']:.6f}",
                f"{row['combined_estimated_power_uw']:.6f}",
                f"{row['minimum_individual_setup_slack_ns']:.6f}",
            ])

    json_path.write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
    )

    markdown = [
        "# Day 30 UART Verification and PPA Report",
        "",
        "## Functional verification",
        "",
        "All audited UART TX equivalence, RX equivalence, "
        "and hybrid loopback logs passed.",
        "",
        f"Total checked assertions/comparisons: **{total_checks:,}**",
        "",
        "The hybrid loopback passed at CPB = 8, 16, 32 and 64.",
        "",
        "## Technology-mapped PPA",
        "",
        "| Architecture | Area (um²) | Estimated power (uW) |",
        "|---|---:|---:|",
    ]

    for name, row in summary.items():
        markdown.append(
            f"| {name} | "
            f"{row['combined_area_um2']:.3f} | "
            f"{row['combined_estimated_power_uw']:.3f} |"
        )

    markdown += [
        "",
        "## Hybrid versus baseline",
        "",
        f"- Mapped area reduction: **{area_reduction:.2f}%**",
        f"- Estimated power reduction: **{power_reduction:.2f}%**",
        "- Individually analyzed TX and RX blocks met setup timing.",
        "",
        "## Selected architecture",
        "",
        "**Baseline UART TX + optimized UART RX** is the "
        "provisional area/power-preferred architecture.",
        "",
        "## Limitations",
        "",
        "- Power assumes input switching activity and is not "
        "waveform-derived.",
        "- Combined PPA is calculated from separately analyzed blocks.",
        "- Integrated STA and post-layout analysis are not performed.",
        "- Functional tests do not constitute formal equivalence proof.",
        "",
        "## Project status",
        "",
        "UART functional and pre-layout PPA comparison: completed.",
        "",
        "Optimized FIFO, full FSM configuration evidence, "
        "and the integrated project audit: pending.",
        "",
    ]

    md_path.write_text(
        "\n".join(markdown),
        encoding="utf-8",
    )

    print("\n========== UART FINAL REPORT ==========")
    print(f"Functional checks verified: {total_checks:,}")
    print(f"Hybrid area reduction: {area_reduction:.2f}%")
    print(f"Hybrid power reduction: {power_reduction:.2f}%")
    print("Markdown:", md_path)
    print("CSV:", csv_path)
    print("JSON:", json_path)
    print("DAY 30 UART FINAL EVIDENCE REPORT: PASS")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, OSError) as exc:
        print("[FAIL]", exc)
        sys.exit(1)
