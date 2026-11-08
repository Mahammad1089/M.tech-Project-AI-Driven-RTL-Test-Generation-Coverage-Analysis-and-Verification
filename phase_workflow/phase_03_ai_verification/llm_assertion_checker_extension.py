#!/usr/bin/env python3
"""Optional Phase-3 LLM-authored UART property-checker experiment.

Authorship/provenance: three candidate property families authored in ChatGPT (GPT-6)
from the documented UART 8N1 behavior and local RTL signal interfaces. They are
not claimed to have been mined by Hermes, and are NOT formal SVA proof.

The existing testbench_generator makes the baseline TB. This adds guarded
immediate assertions to a COPY in a new directory outside the repository.
Historical RTL, source testbenches, AI results and PPA evidence are unchanged.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import inspect
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PHASE = Path(__file__).resolve().parent
ROOT = PHASE.parents[1]
RTL = ROOT / "phase_workflow" / "phase_01_rtl" / "uart"
RESULTS = PHASE / "results" / "hermes" / "validated_ai_scenarios.json"
SOURCE = [RTL / n for n in (
    "uart_tx.v", "uart_tx_opt.v", "uart_rx.v", "uart_rx_opt.v"
)]

# The DUT ports below are present in the verified project snapshot. The checks
# are independent of baseline/optimized equivalence and use the 8N1 contract.
# These conditions are intended as LLM-authored, REVIEWABLE CANDIDATES, not
# automatically mined assertions or a proof of their functional completeness.
LLM_ASSERTIONS = r'''
    integer llm_tx_done_hits = 0;
    integer llm_rx_valid_hits = 0;
    integer llm_rx_error_hits = 0;
    // AI-authored candidate P1: completion implies deasserted busy and idle TX.
    // AI-authored candidate P2: valid RX must be nonbusy and non-error.
    // AI-authored candidate P3: framing error must not mark a valid/busy frame.
    always @(negedge clk) begin
        #2; // allow nonblocking DUT assignments from the previous posedge
        if (!rst) begin
            if (done_ref) begin
                llm_tx_done_hits = llm_tx_done_hits + 1;
                assert (!busy_ref && tx_ref === 1'b1)
                    else $fatal(1,"LLM_TX_DONE_CHECK baseline");
            end
            if (done_tx_opt) begin
                llm_tx_done_hits = llm_tx_done_hits + 1;
                assert (!busy_tx_opt && tx_opt === 1'b1)
                    else $fatal(1,"LLM_TX_DONE_CHECK optimized");
            end
            if (valid_ref) begin
                llm_rx_valid_hits = llm_rx_valid_hits + 1;
                assert (!busy_rx_ref && !error_ref)
                    else $fatal(1,"LLM_RX_VALID_CHECK baseline");
            end
            if (valid_opt) begin
                llm_rx_valid_hits = llm_rx_valid_hits + 1;
                assert (!busy_rx_opt && !error_opt)
                    else $fatal(1,"LLM_RX_VALID_CHECK optimized");
            end
            if (error_ref) begin
                llm_rx_error_hits = llm_rx_error_hits + 1;
                assert (!busy_rx_ref && !valid_ref)
                    else $fatal(1,"LLM_RX_ERROR_CHECK baseline");
            end
            if (error_opt) begin
                llm_rx_error_hits = llm_rx_error_hits + 1;
                assert (!busy_rx_opt && !valid_opt)
                    else $fatal(1,"LLM_RX_ERROR_CHECK optimized");
            end
        end
    end
'''


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_generator():
    path = PHASE / "testbench_generator.py"
    if not path.is_file():
        raise RuntimeError(f"Required existing generator missing: {path}")
    spec = importlib.util.spec_from_file_location("phase3_original_tb_generator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot import the original testbench generator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    signature = inspect.signature(module.make_tb)
    if "spec_assertions" not in signature.parameters:
        raise RuntimeError("The existing make_tb() lacks spec_assertions; refuse to change it automatically")
    return module


def extract_int(text: str, key: str) -> int:
    m = re.search(r"^" + re.escape(key) + r"=(\d+)\s*$", text, flags=re.M)
    if not m:
        raise RuntimeError(f"Missing {key} marker in simulator output")
    return int(m.group(1))


def run(cpbs: list[int], out: Path) -> int:
    if out.resolve().is_relative_to(ROOT.resolve()):
        raise RuntimeError("Output path must remain outside the project repository")
    if not shutil.which("iverilog") or not shutil.which("vvp"):
        raise RuntimeError("Required tools iverilog and vvp must be available in WSL")
    for p in [*SOURCE, RESULTS]:
        if not p.is_file():
            raise RuntimeError(f"Required existing evidence missing: {p}")
    mod = load_generator()
    blob = json.loads(RESULTS.read_text(encoding="utf-8"))
    raw_scenarios = blob.get("scenarios") if isinstance(blob, dict) else blob
    scenarios = mod.validate_scenarios(raw_scenarios, maximum=24)
    if len(scenarios) != 10:
        raise RuntimeError(f"Expected the archived 10-scenario initial AI set, got {len(scenarios)}")
    out.mkdir(parents=True, exist_ok=True)
    entries = []
    for cpb in cpbs:
        d = out / f"cpb_{cpb}"
        d.mkdir(parents=True, exist_ok=True)
        tb_str = mod.make_tb(scenarios, cpb, spec_assertions=True)
        if "SPEC_MONITORED_CYCLES" not in tb_str:
            raise RuntimeError("Existing assertion mode did not provide its monitor marker")
        if "endmodule" not in tb_str:
            raise RuntimeError("Generated testbench has no endmodule")
        tb_str = tb_str.rsplit("endmodule", 1)[0] + LLM_ASSERTIONS + "\nendmodule\n"
        needle = '        $display("TOTAL_CHECKS=%0d",checks);'
        if tb_str.count(needle) != 1:
            raise RuntimeError("Cannot locate the exact summary marker; source may have changed")
        tb_str = tb_str.replace(needle, '''        $display("LLM_TX_DONE_HITS=%0d",llm_tx_done_hits);
        $display("LLM_RX_VALID_HITS=%0d",llm_rx_valid_hits);
        $display("LLM_RX_ERROR_HITS=%0d",llm_rx_error_hits);
''' + needle)
        tb_path = d / "tb_ai_with_llm_assertions.sv"
        tb_path.write_text(tb_str, encoding="utf-8")
        exe = d / "run.out"
        compile_cmd = ["iverilog", "-g2012", "-gassertions", "-s", "tb_uart_phase", "-o", str(exe), str(tb_path), *(str(p) for p in SOURCE)]
        cp = subprocess.run(compile_cmd, capture_output=True, text=True, timeout=120)
        (d / "compile.log").write_text(cp.stdout + cp.stderr, encoding="utf-8")
        row = {"cpb": cpb, "compile_returncode": cp.returncode, "simulation_returncode": None, "status": "FAIL", "source_tb_sha256": sha256(tb_path)}
        entries.append(row)
        if cp.returncode:
            row["reason"] = "compile failed; see compile.log"
            continue
        sim = subprocess.run(["vvp", str(exe)], capture_output=True, text=True, timeout=120)
        combined = sim.stdout + sim.stderr
        (d / "simulation.log").write_text(combined, encoding="utf-8")
        row["simulation_returncode"] = sim.returncode
        try:
            row.update({
                "failed_checks": extract_int(sim.stdout, "FAILED_CHECKS"),
                "existing_spec_monitored_cycles": extract_int(sim.stdout, "SPEC_MONITORED_CYCLES"),
                "tx_done_activations": extract_int(sim.stdout, "LLM_TX_DONE_HITS"),
                "rx_valid_activations": extract_int(sim.stdout, "LLM_RX_VALID_HITS"),
                "rx_framing_error_activations": extract_int(sim.stdout, "LLM_RX_ERROR_HITS"),
            })
            verdict = re.search(r"^VERDICT=(PASS|FAIL)\s*$", sim.stdout, re.M)
            row["verdict"] = verdict.group(1) if verdict else "MISSING"
            nonvacuous = all(row[k] > 0 for k in ("tx_done_activations", "rx_valid_activations", "rx_framing_error_activations"))
            row["nonvacuous_all_three_groups"] = nonvacuous
            row["status"] = "PASS" if (sim.returncode == 0 and row["failed_checks"] == 0 and row["verdict"] == "PASS" and row["existing_spec_monitored_cycles"] > 0 and nonvacuous) else "FAIL"
            if row["status"] != "PASS":
                row["reason"] = "simulation verdict, monitored-cycle or non-vacuity gate failed"
        except RuntimeError as e:
            row["reason"] = str(e)
        print(f"CPB={cpb} STATUS={row['status']} TX_DONE_HITS={row.get('tx_done_activations', '-')} RX_VALID_HITS={row.get('rx_valid_activations', '-')} RX_ERROR_HITS={row.get('rx_framing_error_activations', '-')}", flush=True)

    report = {
        "task": "Step 4 optional LLM-authored module-level simulation assertion checkers",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS" if len(entries) == len(cpbs) and all(r["status"] == "PASS" for r in entries) else "FAIL",
        "provenance": "Candidate property expressions authored in ChatGPT (GPT-6) from a reviewed UART contract; not generated by Hermes; no formal SVA mining or model invocation",
        "source_scenario_file": str(RESULTS.relative_to(ROOT)),
        "source_scenario_sha256": sha256(RESULTS),
        "rtl_source_sha256": {str(p.relative_to(ROOT)): sha256(p) for p in SOURCE},
        "assertion_families": ["TX_DONE implies idle high and busy low", "RX_VALID implies busy low and no framing error", "RX_FRAMING_ERROR implies busy low and no valid frame"],
        "scope": "Simulation-only immediate assertions on baseline and optimized TX/RX; existing spec_assertions monitor also enabled; not formal correctness, not benchmarked against AssertMiner-pro",
        "results": entries,
    }
    (out / "step4_assertion_results.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("REPORT:", out / "step4_assertion_results.json")
    print("FINAL STATUS:", report["status"])
    return 0 if report["status"] == "PASS" else 2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, required=True, help="New output directory outside repository")
    ap.add_argument("--cpbs", nargs="+", type=int, default=[8, 16, 32, 64])
    args = ap.parse_args()
    if sorted(set(args.cpbs)) != args.cpbs or any(not 8 <= c <= 256 for c in args.cpbs):
        ap.error("--cpbs must be sorted unique integers from 8 to 256")
    try:
        return run(args.cpbs, args.output)
    except Exception as exc:
        print("[ERROR]", exc, file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
