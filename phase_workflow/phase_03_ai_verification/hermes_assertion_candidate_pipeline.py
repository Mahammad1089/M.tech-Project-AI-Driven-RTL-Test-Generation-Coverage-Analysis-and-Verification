#!/usr/bin/env python3
"""Optional Hermes-driven Phase-3 assertion candidate experiment.

Actually invokes the project's existing Hermes bridge. Hermes proposes structured
module-level implication properties. Only a strict, contract-reviewed subset is
compiled into SystemVerilog immediate assertions. No raw LLM code is executed.

This is simulation-based checking, NOT formal assertion mining or JasperGold SVA.
Existing RTL, historical Phase-3 data, and Phase-4 experiments are untouched.
All run artifacts must be written outside the repository.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PHASE = Path(__file__).resolve().parent
WORKFLOW = PHASE.parent
PROJECT = WORKFLOW.parent
RTL = WORKFLOW / "phase_01_rtl" / "uart"
KNOWLEDGE = WORKFLOW / "phase_02_parsing" / "results" / "uart_knowledge.json"
SCENARIOS = PHASE / "results" / "hermes" / "validated_ai_scenarios.json"
SOURCES = {k: RTL / (k + ".v") for k in
           ("uart_tx", "uart_tx_opt", "uart_rx", "uart_rx_opt")}
CPBS = (8, 16, 32, 64)

# A separately reviewed 8N1 interface contract limits what can be checked.
# These are allowable implications, not prewritten Verilog assertion statements.
# Hermes must actually return the identifiers and predicates accepted below.
REVIEWED = {
    ("tx", "done"): {"busy": 0, "tx": 1},
    ("rx", "valid"): {"busy": 0, "framing_error": 0},
    ("rx", "framing_error"): {"busy": 0, "valid": 0},
}
SIGNALS = {
    "tx": {"tx": ("tx_ref", "tx_opt"),
           "busy": ("busy_ref", "busy_tx_opt"),
           "done": ("done_ref", "done_tx_opt")},
    "rx": {"valid": ("valid_ref", "valid_opt"),
           "busy": ("busy_rx_ref", "busy_rx_opt"),
           "framing_error": ("error_ref", "error_opt")},
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_module(name: str, file: Path):
    spec = importlib.util.spec_from_file_location(name, file)
    if not file.is_file() or spec is None or spec.loader is None:
        raise RuntimeError(f"Required existing source missing: {file}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_source_fingerprints(knowledge: dict) -> None:
    source_analysis = knowledge.get("source_analysis")
    if not isinstance(source_analysis, dict):
        raise RuntimeError("Phase-2 knowledge is missing source_analysis")
    for module, path in SOURCES.items():
        if not path.is_file():
            raise RuntimeError(f"Missing frozen RTL: {path}")
        record = source_analysis.get(module)
        if not isinstance(record, dict) or not isinstance(record.get("sha256"), str):
            raise RuntimeError(f"Missing Phase-2 SHA-256 for {module}")
        if record["sha256"].lower() != digest(path):
            raise RuntimeError(f"RTL/AST SHA-256 mismatch for {module}; refusing to evaluate stale assertions")


def build_prompt(knowledge: dict) -> str:
    protocol = knowledge.get("protocol")
    specs = knowledge.get("module_specifications", {})
    analysis = knowledge.get("source_analysis")
    if not isinstance(protocol, dict) or not isinstance(analysis, dict):
        raise RuntimeError("Structured Phase-2 protocol/source analysis is required")
    if not isinstance(specs, dict):
        specs = {}
    requirements = {
        k: v.get("requirements", []) for k, v in specs.items()
        if k in SOURCES and isinstance(v, dict)
    }
    module_ports = {
        k: v.get("ports", []) for k, v in analysis.items()
        if k in SOURCES and isinstance(v, dict)
    }
    # Requirements are optional candidate context. The older, valid PyVerilog
    # JSON schema supplies AST ports/parameters but no module_specifications.
    return (
        "You are Hermes, generating candidate module-level hardware CHECKER PROPERTIES.\n"
        "Return ONLY one JSON object, no code blocks, no Markdown, no Verilog, no tools.\n"
        "Your output MUST have exactly one key: assertions, a list of EXACTLY THREE objects.\n"
        "Each object has exactly keys: id, module, when, require, rationale.\n"
        "id: unique lowercase alphanumeric underscore identifier, 4..32 characters.\n"
        "module: either tx or rx. when: a single output signal name.\n"
        "require: list of one or two objects, each with keys signal and value, "
        "where value is JSON integer 0 or 1. rationale: short explanatory sentence.\n"
        "Provide one nontrivial property for EACH event: tx.done, rx.valid, "
        "and rx.framing_error. Consequents must concern OTHER signals.\n"
        "Use only the reviewed independent protocol relationships below.\n"
        "Do NOT invent protocol requirements or assert every condition is formally proved.\n"
        "Reviewed consequence rules (possible values; choose meaningful conjunctions):\n"
        + json.dumps([{"module": m, "when": w, "allow_require": rules}
                      for (m, w), rules in REVIEWED.items()], sort_keys=True) + "\n"
        "Phase-2 protocol context (may describe candidates, not authoritative):\n"
        + json.dumps(protocol, sort_keys=True)[:9000] + "\n"
        "Phase-2 AST-extracted module ports:\n"
        + json.dumps(module_ports, sort_keys=True)[:9000] + "\n"
        "Phase-2 candidate module requirements, if recorded (untrusted until checked):\n"
        + json.dumps(requirements, sort_keys=True)[:12000] + "\n"
        "Your assertions will be validated by an allowlisted schema and then checked "
        "as simulation-time immediate assertions on both baseline and optimized designs.\n"
    )


def parse_response(response: str) -> list[dict]:
    if not isinstance(response, str):
        raise ValueError("Hermes result text is missing")
    text = response.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
    obj = json.loads(text)
    if not isinstance(obj, dict) or set(obj) != {"assertions"}:
        raise ValueError("Hermes response must contain exactly {assertions: [...]}")
    values = obj["assertions"]
    if not isinstance(values, list) or len(values) != 3:
        raise ValueError("Exactly three Hermes-generated assertions are required")
    result = []
    seen_ids = set()
    seen_events = set()
    for index, item in enumerate(values, 1):
        if not isinstance(item, dict) or set(item) != {"id", "module", "when", "require", "rationale"}:
            raise ValueError(f"Candidate {index}: invalid object keys")
        ident, mod, when = item["id"], item["module"], item["when"]
        if not isinstance(ident, str) or not re.fullmatch(r"[a-z][a-z0-9_]{3,31}", ident):
            raise ValueError(f"Candidate {index}: invalid identifier")
        if ident in seen_ids:
            raise ValueError(f"Candidate {index}: duplicate identifier {ident}")
        if (mod, when) not in REVIEWED or (mod, when) in seen_events:
            raise ValueError(f"Candidate {index}: unsupported/duplicate trigger {mod}.{when}")
        req = item["require"]
        if not isinstance(req, list) or not 1 <= len(req) <= 2:
            raise ValueError(f"Candidate {ident}: require must contain 1 or 2 predicates")
        normalized = []
        used = set()
        for atom in req:
            if not isinstance(atom, dict) or set(atom) != {"signal", "value"}:
                raise ValueError(f"Candidate {ident}: invalid consequent schema")
            signal, value = atom["signal"], atom["value"]
            if not isinstance(signal, str) or signal in used or signal == when:
                raise ValueError(f"Candidate {ident}: duplicate/trivial consequent")
            if type(value) is not int or value not in (0, 1):
                raise ValueError(f"Candidate {ident}: consequent must be integer 0 or 1")
            if REVIEWED[(mod, when)].get(signal) != value:
                raise ValueError(f"Candidate {ident}: {signal}={value} not supported by reviewed contract")
            used.add(signal)
            normalized.append({"signal": signal, "value": value})
        rationale = item["rationale"]
        if not isinstance(rationale, str) or not 5 <= len(rationale.strip()) <= 240:
            raise ValueError(f"Candidate {ident}: rationale is missing or too long")
        seen_ids.add(ident)
        seen_events.add((mod, when))
        result.append({"id": ident, "module": mod, "when": when,
                       "require": normalized, "rationale": rationale.strip()})
    if seen_events != set(REVIEWED):
        raise ValueError("Missing one or more required module-level event types")
    return result


def build_checker(properties: list[dict]) -> tuple[str, str, list[str]]:
    # Build Verilog from validated structural data only. No LLM-supplied Verilog is copied.
    lines = ["    // Hermes proposed; independently schema/contract filtered. NOT formal proof."]
    markers = []
    for prop in properties:
        for index, variant in enumerate(("REF", "OPT")):
            counter = f"hermes_hits_{prop['id']}_{variant.lower()}"
            lines.append(f"    integer {counter} = 0;")
            markers.append(f"HERMES_HITS_{prop['id']}_{variant}")
    lines += ["    always @(negedge clk) begin", "        #2;", "        if (!rst) begin"]
    for prop in properties:
        module = prop["module"]
        for index, variant in enumerate(("REF", "OPT")):
            trigger = SIGNALS[module][prop["when"]][index]
            expr = " && ".join(
                f"({SIGNALS[module][item['signal']][index]} === 1'b{item['value']})"
                for item in prop["require"]
            )
            counter = f"hermes_hits_{prop['id']}_{variant.lower()}"
            label = f"HERMES_{prop['id']}_{variant}"
            lines += [f"            if ({trigger} === 1'b1) begin",
                      f"                {counter} = {counter} + 1;",
                      f"                assert ({expr}) else $fatal(1, \"{label}\");",
                      "            end"]
    lines += ["        end", "    end"]
    reports = [f'        $display("HERMES_HITS_{prop["id"]}_{variant}=%0d",hermes_hits_{prop["id"]}_{variant.lower()});'
               for prop in properties for variant in ("REF", "OPT")]
    return "\n".join(lines) + "\n", "\n".join(reports) + "\n", markers


def run_one(cpb: int, properties: list[dict], scenarios: list[dict], generator,
            output: Path) -> dict:
    dest = output / f"cpb_{cpb}"
    dest.mkdir(parents=True, exist_ok=True)
    checker, reports, markers = build_checker(properties)
    tb = generator.make_tb(scenarios, cpb, spec_assertions=True)
    insert = '        $display("TOTAL_CHECKS=%0d",checks);'
    if tb.count(insert) != 1 or tb.count("endmodule") != 1:
        raise RuntimeError("Existing testbench generator contract changed")
    tb = tb.replace(insert, reports + insert)
    tb = tb.rsplit("endmodule", 1)[0] + checker + "endmodule\n"
    tb_file = dest / "tb_hermes_assertions.sv"
    tb_file.write_text(tb, encoding="utf-8")
    exe = dest / "run.out"
    compile_cmd = ["iverilog", "-g2012", "-gassertions", "-s", "tb_uart_phase",
                   "-o", str(exe), str(tb_file), *(str(p) for p in SOURCES.values())]
    cp = subprocess.run(compile_cmd, capture_output=True, text=True, timeout=120)
    (dest / "compile.log").write_text(cp.stdout + "\n" + cp.stderr, encoding="utf-8")
    row = {"cpb": cpb, "compile_returncode": cp.returncode,
           "simulation_returncode": None, "status": "FAIL", "testbench_sha256": digest(tb_file)}
    if cp.returncode:
        row["reason"] = "Icarus compile failed (see compile.log)"
        return row
    try:
        sim = subprocess.run(["vvp", str(exe)], capture_output=True, text=True, timeout=120)
    except subprocess.TimeoutExpired:
        row["reason"] = "Icarus simulation timeout"
        return row
    (dest / "simulation.log").write_text(sim.stdout + "\n" + sim.stderr, encoding="utf-8")
    row["simulation_returncode"] = sim.returncode
    m = re.search(r"^VERDICT=(PASS|FAIL)\s*$", sim.stdout, re.MULTILINE)
    row["verdict"] = m.group(1) if m else "MISSING"
    for key in ("FAILED_CHECKS", "SPEC_MONITORED_CYCLES", *markers):
        v = re.search(r"^" + re.escape(key) + r"=(\d+)\s*$", sim.stdout, re.MULTILINE)
        row[key] = int(v.group(1)) if v else None
    activated = all(isinstance(row[k], int) and row[k] > 0 for k in markers)
    row["all_properties_nonvacuous_on_both_variants"] = activated
    row["status"] = ("PASS" if sim.returncode == 0 and row["verdict"] == "PASS"
                     and row["FAILED_CHECKS"] == 0
                     and isinstance(row["SPEC_MONITORED_CYCLES"], int)
                     and row["SPEC_MONITORED_CYCLES"] > 0 and activated else "FAIL")
    if row["status"] == "FAIL":
        row["reason"] = "Simulator failed, required markers missing, or assertion vacuity detected"
    return row


def check_inputs() -> tuple[dict, list[dict], object]:
    if not shutil.which("iverilog") or not shutil.which("vvp"):
        raise RuntimeError("Icarus tools missing")
    if not KNOWLEDGE.is_file() or not SCENARIOS.is_file():
        raise RuntimeError("Saved Phase-2 knowledge or Hermes validated scenario file missing")
    knowledge = json.loads(KNOWLEDGE.read_text(encoding="utf-8"))
    check_source_fingerprints(knowledge)
    generator = load_module("existing_phase3_tb_generator", PHASE / "testbench_generator.py")
    original = json.loads(SCENARIOS.read_text(encoding="utf-8"))
    data = original.get("scenarios") if isinstance(original, dict) else original
    scenarios = generator.validate_scenarios(data, maximum=24)
    if len(scenarios) != 10:
        raise RuntimeError("Expected exactly ten saved original Hermes scenarios")
    return knowledge, scenarios, generator


def self_test() -> None:
    sample = {"assertions": [
        {"id": "tx_done_idle", "module": "tx", "when": "done",
         "require": [{"signal": "busy", "value": 0}, {"signal": "tx", "value": 1}],
         "rationale": "Transmit completion indicates idle and no busy."},
        {"id": "rx_valid_clear", "module": "rx", "when": "valid",
         "require": [{"signal": "framing_error", "value": 0}],
         "rationale": "A valid frame excludes a framing error."},
        {"id": "rx_error_invalid", "module": "rx", "when": "framing_error",
         "require": [{"signal": "valid", "value": 0}],
         "rationale": "A framing error must not validate that frame."},
    ]}
    props = parse_response(json.dumps(sample))
    checker, reports, keys = build_checker(props)
    assert len(props) == 3 and len(keys) == 6
    assert "assert" in checker and "HERMES_HITS" in reports
    bad = json.loads(json.dumps(sample))
    bad["assertions"][0]["require"][0]["signal"] = "`system('rm -rf')"
    try:
        parse_response(json.dumps(bad))
    except ValueError:
        pass
    else:
        raise AssertionError("Unsafe LLM predicate was not rejected")
    print("[PASS] Schema/contract filtering and code-generation unit checks")
    print("[NOT RUN] No Hermes call, RTL compile or simulation in self-test")


def main() -> int:
    ap = argparse.ArgumentParser(description="Live Hermes-generated immediate-assertion checks")
    ap.add_argument("--output", type=Path, help="Dedicated output directory outside repository")
    ap.add_argument("--timeout", type=int, default=240)
    ap.add_argument("--self-test", action="store_true", help="Offline parser/codegen test only")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return 0
    if args.timeout < 30 or args.timeout > 900:
        ap.error("--timeout must be 30..900 seconds")
    if args.output is None:
        ap.error("--output is required for live run")
    output = args.output.expanduser().resolve()
    if output == PROJECT.resolve() or PROJECT.resolve() in output.parents:
        ap.error("Output must be outside the project repository")
    if output.exists() and any(output.iterdir()):
        ap.error("Output directory must be new or empty, to preserve previous evidence")
    report = {"task": "Hermes-generated module-level simulation assertion candidates",
              "status": "FAIL", "created_utc": datetime.now(timezone.utc).isoformat(),
              "experiment_scope": "Phase 3 optional, no change to frozen RTL or Phase 4",
              "assertion_kind": "Simulation-time SystemVerilog immediate assertions, not formal SVA",
              "hermes_called": False, "candidates_source": "NOT_GENERATED", "results": []}
    output.mkdir(parents=True, exist_ok=True)
    try:
        knowledge, scenarios, generator = check_inputs()
        prompt_path = output / "hermes_assertion_prompt.txt"
        prompt_path.write_text(build_prompt(knowledge), encoding="utf-8")
        report["input_sha256"] = {
            "knowledge": digest(KNOWLEDGE), "saved_hermes_scenarios": digest(SCENARIOS),
            **{name: digest(path) for name, path in SOURCES.items()}}
        bridge = load_module("existing_phase3_hermes_bridge", PHASE / "hermes_bridge.py")
        print("[CALL] Actual Hermes chat --oneshot through existing hermes_bridge.py", flush=True)
        report["hermes_called"] = True
        result = bridge.run_hermes(str(prompt_path), timeout_seconds=args.timeout)
        # Preserve provenance without replacing any existing Hermes evidence.
        write_json(output / "hermes_raw_result.json", result)
        if result.get("status") != "PASS":
            raise RuntimeError("Hermes call failed: " + str(result.get("error") or result.get("stage")))
        report["candidates_source"] = "HERMES_LIVE_CALL"
        report["hermes_session_id"] = result.get("session_id")
        report["hermes_tokens"] = result.get("tokens")
        report["hermes_duration_ms"] = result.get("duration_ms")
        props = parse_response(result.get("response_text"))
        write_json(output / "validated_hermes_assertions.json", {"assertions": props})
        report["assertion_ids"] = [p["id"] for p in props]
        for cpb in CPBS:
            row = run_one(cpb, props, scenarios, generator, output)
            report["results"].append(row)
            print(f"CPB={cpb} STATUS={row['status']} NONVACUOUS={row.get('all_properties_nonvacuous_on_both_variants')} REASON={row.get('reason','none')}", flush=True)
        if len(report["results"]) == len(CPBS) and all(x["status"] == "PASS" for x in report["results"]):
            report["status"] = "PASS"
    except Exception as exc:
        report["error"] = str(exc)
        print("[FAIL]", exc, file=sys.stderr)
    write_json(output / "hermes_assertion_evaluation.json", report)
    print("REPORT:", output / "hermes_assertion_evaluation.json")
    print("FINAL STATUS:", report["status"])
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
