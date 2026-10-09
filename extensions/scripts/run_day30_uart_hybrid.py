#!/usr/bin/env python3

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path.home() / "Mtech_project" / "AI_RTL_Verification"

SOURCE_TB = ROOT / (
    "extensions/testbench/"
    "tb_day30_uart_optimized_loopback.v"
)

HYBRID_TB = ROOT / (
    "extensions/testbench/"
    "tb_day30_uart_hybrid_loopback.v"
)

BASELINE_TX = ROOT / (
    "extensions/rtl/uart/uart_tx.v"
)

OPTIMIZED_RX = ROOT / (
    "extensions/rtl/uart/optimized/uart_rx_opt.v"
)

OUT = ROOT / (
    "extensions/results/day30/uart/hybrid_loopback"
)

TOP = "tb_day30_uart_hybrid_loopback"

EXPECTED = {
    "TOTAL CHECKS": 194,
    "PASSED CHECKS": 194,
    "FAILED CHECKS": 0,
    "TX FRAMES": 38,
    "RX VALID FRAMES": 38,
    "RX FRAMING ERRORS": 1,
}

def main():
    OUT.mkdir(parents=True, exist_ok=True)

    print("=" * 65)
    print("DAY 30 STEP 4E-6 - HYBRID UART VERIFICATION")
    print("=" * 65)

    for path in (SOURCE_TB, BASELINE_TX, OPTIMIZED_RX):
        if not path.is_file():
            print("[FAIL] Required file missing:", path)
            return 1

    code = SOURCE_TB.read_text(encoding="utf-8")

    replacements = [
        (
            r"\bmodule\s+tb_day30_uart_optimized_loopback\b",
            "module tb_day30_uart_hybrid_loopback",
        ),
        (
            r"\buart_tx_opt\s*#\s*\(",
            "uart_tx #(",
        ),
        (
            re.escape("DAY 30 UART OPTIMIZED LOOPBACK: PASS"),
            "DAY 30 UART HYBRID LOOPBACK: PASS",
        ),
        (
            re.escape("DAY 30 UART OPTIMIZED LOOPBACK: FAIL"),
            "DAY 30 UART HYBRID LOOPBACK: FAIL",
        ),
    ]

    for pattern, replacement in replacements:
        code, count = re.subn(
            pattern,
            replacement,
            code,
            count=1,
        )

        if count != 1:
            print(
                "[FAIL] Source testbench structure differs "
                "from expected format"
            )
            print("Unmatched pattern:", pattern)
            return 1

    HYBRID_TB.write_text(code, encoding="utf-8")

    print("[PASS] Hybrid testbench generated")
    print("[PASS] Original RTL files unchanged")
    print("Testbench:", HYBRID_TB)

    results = []
    all_passed = True

    for cpb in (8, 16, 32, 64):
        print(
            f"\n========== HYBRID UART CPB={cpb} ==========",
            flush=True,
        )

        executable = OUT / f"hybrid_{cpb}.out"
        log = OUT / f"hybrid_{cpb}.log"

        compile_command = [
            "iverilog",
            "-g2012",
            "-s",
            TOP,
            "-P",
            f"{TOP}.CPB={cpb}",
            "-o",
            str(executable),
            str(BASELINE_TX),
            str(OPTIMIZED_RX),
            str(HYBRID_TB),
        ]

        compilation = subprocess.run(
            compile_command,
            text=True,
            capture_output=True,
        )

        if compilation.returncode != 0:
            print("[FAIL] Compilation")
            print(compilation.stdout)
            print(compilation.stderr)
            all_passed = False
            continue

        print("[PASS] Compilation")

        try:
            simulation = subprocess.run(
                ["vvp", str(executable)],
                capture_output=True,
                text=True,
                timeout=180,
            )
        except subprocess.TimeoutExpired:
            print("[FAIL] Simulation timeout")
            all_passed = False
            continue

        output = simulation.stdout + simulation.stderr

        log.write_text(output, encoding="utf-8")

        values = {}

        for label in EXPECTED:
            match = re.search(
                rf"^{re.escape(label)}:\s*(\d+)\s*$",
                simulation.stdout,
                re.MULTILINE,
            )

            if match:
                values[label] = int(match.group(1))
                print(f"{label}: {values[label]}")
            else:
                print(f"[FAIL] Missing result: {label}")

        passed = (
            simulation.returncode == 0
            and all(
                values.get(label) == expected
                for label, expected in EXPECTED.items()
            )
            and "DAY 30 UART HYBRID LOOPBACK: PASS"
                in simulation.stdout
            and "[FAIL]" not in output
        )

        results.append({
            "clks_per_bit": cpb,
            "status": "PASS" if passed else "FAIL",
            **values,
            "log": str(log.relative_to(ROOT)),
        })

        if passed:
            print(f"[PASS] HYBRID UART CPB={cpb}")
        else:
            print(f"[FAIL] HYBRID UART CPB={cpb}")
            print("Log:", log)
            print(output[-2000:])
            all_passed = False

    summary = {
        "step": "Day 30 Step 4E-6",
        "architecture": "Baseline TX + Optimized RX",
        "status": (
            "PASS"
            if all_passed and len(results) == 4
            else "FAIL"
        ),
        "results": results,
    }

    report = OUT / "day30_uart_hybrid_summary.json"

    report.write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )

    print("\n========== HYBRID UART FINAL RESULT ==========")

    passed_count = sum(
        row["status"] == "PASS"
        for row in results
    )

    print(f"CONFIGURATIONS PASSED: {passed_count}/4")
    print("JSON:", report)

    if summary["status"] == "PASS":
        print("TOTAL CHECKS PASSED: 776")
        print("DAY 30 UART HYBRID LOOPBACK: PASS")
        return 0

    print("DAY 30 UART HYBRID LOOPBACK: FAIL")
    return 1


if __name__ == "__main__":
    sys.exit(main())
