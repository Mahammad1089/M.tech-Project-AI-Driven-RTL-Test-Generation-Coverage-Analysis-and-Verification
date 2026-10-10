#!/usr/bin/env python3
"""Finalize an existing, verified M.Tech phase-based UART review view.

Read-only to historical source and results, except updating derived review-facing
Markdown and metadata under phase_workflow. Creates separate reviewer and
reproducibility ZIPs with checksum manifests. Does not run Hermes or simulation.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path.cwd().resolve()
WF = ROOT / 'phase_workflow'
R = WF / 'phase_03_ai_verification' / 'results'
EV = WF / 'evaluation'
P4 = WF / 'phase_04_uart_novelty'
EXPECTED_CPBS = [8, 16, 32, 64]
EXPECTED = {
    'directed': (30116, 60.0, 14984),
    'random': (30116, 20.0, 14984),
    'ai_initial': (36408, 100.0, 18144),
}
BLOCKED = {'.env', '.pem', '.key', '.p12', '.pfx', '.out', '.vcd', '.pyc', '.bin'}


def need(condition, message):
    if not condition:
        raise RuntimeError(message)


def read_json(path):
    need(path.is_file(), f'Missing required file: {path}')
    return json.loads(path.read_text(encoding='utf-8'))


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for part in iter(lambda: f.read(1024 * 1024), b''):
            h.update(part)
    return h.hexdigest()


def validate():
    need((ROOT / 'rtl' / 'alu.v').is_file(), 'Start inside the full project repository root')
    audit = read_json(EV / 'workflow_status.json')
    need(audit.get('status') == 'PASS' and audit.get('passed') == 12 and audit.get('total') == 12,
         'Required technical workflow audit is not 12/12 PASS')
    need(all(item.get('status') == 'PASS' for item in audit.get('checks', [])),
         'Technical workflow has a non-PASS requirement')
    legacy = EV / 'reference' / 'master_requirements.csv'
    with legacy.open(encoding='utf-8', newline='') as f:
        historic = list(csv.DictReader(f))
    need(len(historic) == 18 and all(x.get('reconciled_status') == 'PASS' for x in historic),
         'Original 18/18 technical evidence not validated')
    evaluation = read_json(R / 'evaluation_summary.json')
    need(evaluation.get('status') == 'PASS' and
         evaluation.get('ai_generation') == 'HERMES_CHAT_ONESHOT' and
         evaluation.get('closure_target_met') is True and
         evaluation.get('final_ai_coverage') == 100.0 and
         evaluation.get('ai_total_scenarios') == 10,
         'New Hermes UART evidence does not meet expected completion criteria')
    suites = evaluation.get('suites', {})
    for name, (checks, coverage, cycles) in EXPECTED.items():
        suite = suites.get(name, {})
        need(suite.get('all_pass') is True and suite.get('failed_checks') == 0
             and suite.get('tested_cpbs') == EXPECTED_CPBS
             and suite.get('checks') == checks
             and suite.get('cycles') == cycles
             and suite.get('min_coverage_pct') == coverage
             and evaluation.get('comparisons', {}).get(name, {}).get('scenario_budget') == 10,
             f'{name} aggregate evidence differs from the verified output')
        for cpb in EXPECTED_CPBS:
            sim = R / 'simulation' / f'{name}_cpb{cpb}'
            record = read_json(sim / 'result.json')
            need(record.get('status') == 'PASS' and record.get('failed') == 0 and
                 record.get('scenarios') == 10 and record.get('checks', 0) > 0,
                 f'Incomplete simulation evidence: {name} CPB={cpb}')
            need((sim / 'simulation.log').is_file() and (sim / 'tb_uart_phase.v').is_file() and
                 (sim / 'scenarios.json').is_file(),
                 f'Missing simulation trace or testbench for {name} CPB={cpb}')
            if name == 'ai_initial':
                need(record.get('covered_bins') == 10 and
                     len(record.get('coverage', {})) == 10 and
                     all(v == 1 for v in record['coverage'].values()),
                     f'AI coverage incomplete for CPB={cpb}')
    raw = read_json(R / 'hermes' / 'initial_prompt_raw.json')
    need(raw.get('status') == 'PASS' and raw.get('return_code') == 0 and
         raw.get('hermes_exit_code') == 0,
         'Live Hermes model call evidence not PASS')
    validated = read_json(R / 'hermes' / 'validated_ai_scenarios.json')
    need(len(validated.get('scenarios', [])) == 10 and
         validated.get('origin') == 'HERMES_CHAT_ONESHOT',
         'Validated Hermes scenario evidence is missing')
    ppa = read_json(P4 / 'reference' / 'uart_report.json')
    need(ppa.get('status') == 'PASS', 'Original UART architecture report not PASS')
    combined = read_json(P4 / 'UART_INTEGRATED_RESEARCH_REPORT.json')
    need(combined.get('status') == 'PASS', 'Combined UART research report not PASS')
    need((P4 / 'reference' / 'uart_architecture_comparison.csv').is_file(),
         'Mapped UART comparison CSV missing')
    return evaluation, audit


def write_review_files(data, audit):
    suites = data['suites']
    ts = datetime.now(timezone.utc).isoformat()
    summary = '''# Phase-Oriented M.Tech RTL Verification: Verified Results

## Research design flow

**Phase 1 — RTL design:** baseline/optimized ALU, FIFO, FSM and UART architectures.
**Phase 2 — RTL-to-Python knowledge:** UART PyVerilog AST extraction, validated structural/protocol knowledge.
**Phase 3 — AI-assisted verification:** UART objectives → real Hermes scenarios → whitelist validator → generated self-checking Verilog TB → Icarus simulation → functional coverage.
**Phase 4 — UART evaluation:** AI-vs-directed-vs-random experiments plus independently established pre-layout UART architecture/PPA results.
**Evaluation:** verification evidence, reproducibility, technical gates and thesis readiness.

## Technical verification status

- Original historical technical requirements: **18/18 PASS** (separate evidence).
- New four-phase workflow acceptance gates: **12/12 PASS**.
- Hermes model source: **live HERMES_CHAT_ONESHOT**; 10 generated and validated initial test scenarios.
- All three strategies simulated at **CLKS_PER_BIT = 8, 16, 32, 64**, with **zero failed checks**.

| Experimental strategy | Initial scenarios | Functional bins | Checks | Failed checks | Total simulation cycles |
|---|---:|---:|---:|---:|---:|
'''
    for label, key in [('Directed', 'directed'), ('Deterministic random', 'random'), ('Hermes AI initial', 'ai_initial')]:
        s = suites[key]
        summary += (f"| {label} | 10 | {s['min_coverage_pct']:g}% "
                    f"| {s['checks']:,} | {s['failed_checks']} | {s['cycles']:,} |\n")
    summary += '''
**Closure observation:** all ten defined functional bins were covered in the first AI test set. No uncovered bins remained, so no new feedback-generated scenarios were required. This is **first-pass coverage completion**, not experimental proof that multiple feedback rounds improved coverage.

**Evidence:** `phase_02_parsing/results/uart_knowledge.json`, `phase_03_ai_verification/results/evaluation_summary.json`, `phase_03_ai_verification/results/simulation/`, `phase_03_ai_verification/results/hermes/`, `phase_04_uart_novelty/UART_INTEGRATED_RESEARCH_REPORT.md`, `evaluation/workflow_status.json`.

## Independently verified UART architecture observations

- Baseline TX + baseline RX: **450.604 µm²** combined mapped area; **370.282 µW** estimated power.
- Hybrid baseline TX + optimized RX: **425.600 µm²** combined mapped area; **366.547 µW** estimated power.
- Difference: approximately **5.55% less mapped area** and **1.01% less estimated power** for the hybrid. These are **archived pre-layout, assumed-activity estimates**. No hardware improvement is attributed to Hermes.

## Research and submission limitations

- 100% refers to the **ten defined scenario-based functional bins**, not formal state-space coverage, structural code coverage or full protocol compliance.
- All methods received ten initial scenarios, but AI used more total simulation cycles; test count alone does not establish equal runtime or resource cost.
- The random strategy currently uses one fixed seed; repeated-seed statistics and independent AI trials remain outstanding.
- The Hermes prompt explicitly enumerates target coverage bins. This supports AI-directed test generation but should **not** be described as autonomous discovery of unknown defects.
- Research novelty relative to peer-reviewed literature, thesis editing and final clean-room reproduction remain **pending**.
- Original historical test/output paths remain unmodified for integrity. Phase-named files are a separate review view.
'''
    (EV / 'PHASE_REVIEW_SUMMARY.md').write_text(summary, encoding='utf-8')
    (WF / 'README.md').write_text('''# M.Tech AI-Driven RTL Verification — Phase-Based Review

**Verified technical status: original historical audit 18/18 PASS; new UART AI workflow 12/12 PASS.**

| Phase | Purpose | Outcome |
|---|---|---|
| 1 — RTL | ALU, FIFO, sequence detector and UART baseline/optimized designs | Verified archived RTL and tests |
| 2 — Python knowledge | PyVerilog UART structural extraction | Four UART modules parsed |
| 3 — Hermes AI verification | AI scenario generation, whitelist, Verilog TB, Icarus and coverage | Ten scenarios; 100% of ten defined UART bins across four CPBs |
| 4 — UART research | Verification strategy comparison + historic pre-layout UART optimization | Integrated report PASS; distinct evidence streams |
| Evaluation | Automated acceptance and research/submission checks | 12/12 technical gates PASS; publication/submission tasks pending |

Start with `evaluation/PHASE_REVIEW_SUMMARY.md` and `docs/PHASE_EXECUTION_GUIDE.md`.

**Boundary:** This is simulation-only. AI-generated scenarios do not change the RTL. Historic evidence and path mappings are preserved. The review ZIP is for presentation; a separate evidence ZIP contains traceable new UART simulation artifacts. The original technology library is not redistributed.
''', encoding='utf-8')
    (WF / 'docs' / 'RESEARCH_SCOPE.md').write_text('''# Research Evidence, Claimed Contribution and Remaining Work

## Completed and measured

The original project verified ALU, FIFO, FSM and UART design families; its historical master audit is **18/18 PASS**. The additional phase-based UART experiment is now **12/12 PASS** and includes genuine PyVerilog parsing, live Hermes scenario generation, deterministic scenario validation, Icarus testbenches, observed functional coverage, and an integrated report.

At an equal initial **ten scenarios per strategy**, coverage across the defined ten UART bins was **60% directed, 20% deterministic random, and 100% Hermes AI**. The initial AI suite passed **36,408 checks** across CLKS_PER_BIT 8/16/32/64 with no failed checks. The missing-bin set was empty, so additional AI feedback trials were **not required**.

Original archived hybrid UART pre-layout mapping reduced combined area from 450.604 to 425.600 µm² and assumed-activity estimated power from 370.282 to 366.547 µW. These are architecture results and **not caused by Hermes**.

## Remaining research and submission validation

- Re-run random tests with multiple independent seeds, preserving a clearly specified scenario budget, and report mean, dispersion, and worst/best coverage.
- Repeat Hermes scenario generation with documented model/provider and multiple independent requests if feasible; compare variation and runtime/cost.
- Analyze independent coverage strength and negative tests; ten scenario bins are not complete UART protocol proof.
- Verify precise novelty and distinctions through a dated IEEE/Springer/Elsevier related-work table.
- Complete thesis/review document revision, including figures, reproducibility instructions and limitations.
- Conduct a clean WSL reproduction and validate checksums of final evidence ZIP. Do not include licensed standard-cell library, credential files or old machine-specific private data.

## Reviewer-friendly organization

Only phase names are used in review-facing paths. Original experiment/source paths are retained separately for transparent provenance; no mass-renaming or deletion is applied to validated historical evidence.
''', encoding='utf-8')
    readiness = {
        'generated_utc': ts,
        'technical_12_gate_audit': 'PASS',
        'technical_gates_passed': audit['passed'],
        'historical_18_gate_audit': 'PASS',
        'thesis_or_publication_submission_ready': False,
        'remaining_submission_work': {
            'EV_02_thesis_revision': 'PENDING',
            'EV_03_prior_art_review': 'PENDING',
            'EV_04_phase_evidence_package': 'READY_AFTER_EXPORT',
            'EV_05_clean_reproducibility_and_statistical_validation': 'PENDING',
        },
    }
    (EV / 'REVIEW_READINESS.json').write_text(json.dumps(readiness, indent=2)+'\n', encoding='utf-8')
    (WF / 'docs' / 'REVIEW_DEMONSTRATION.md').write_text('''# Review Demonstration — Architecture to Evidence

1. Show Phase 1 UART Verilog and explain 8N1 TX/RX, reset, CPB and baseline-versus-optimized architectures.
2. Show Phase 2 `uart_knowledge.json` generated by PyVerilog AST and the four source fingerprints.
3. Explain Phase 3 `objectives.json`, the 10 functional bins and the whitelist of five scenario kinds.
4. Show the original Hermes request/response evidence and the 10 validated scenario records. The language model proposes inputs; it is not the oracle.
5. Show generated Verilog testbenches and simulator logs at CPB 8, 16, 32, 64. Compare transmitted and received bytes and TX/RX cycle behavior.
6. Display directed (60%), deterministic random (20%) and AI (100%) functional-bin coverage; zero failed checks.
7. Explain that the initial AI batch already closed the 10 bins, so no additional feedback queries were required in this experiment.
8. Present baseline versus hybrid UART pre-layout mapped area and estimated power independently of AI verification results.
9. Open `evaluation/workflow_status.json` (12/12 PASS) and the historical 18/18 reconciliation (separate validation).
10. Explain remaining multi-seed statistics, related work, protocol coverage limitations, university thesis preparation and clean reproduction.

**Do not claim:** formal completeness, post-layout silicon PPA, improved PPA caused by AI, statistically general AI superiority, or feedback-round benefit not observed.
''', encoding='utf-8')
    # This source-generated historical-only JSON was written by the original organizer.
    # Refresh it here so the review view cannot contradict the live 12/12 audit.
    previous = EV / 'verification_summary.json'
    ver = {
        'generated_utc': ts,
        'historical_audit': {'passed': 18, 'total': 18},
        'uart_phase_workflow_audit': {'passed': 12, 'total': 12},
        'uart_ai_integration': 'VERIFIED_HERMES_AND_ICARUS',
        'functional_bin_coverage': 100.0,
        'university_submission_readiness': 'PENDING_RESEARCH_VALIDATION',
    }
    previous.write_text(json.dumps(ver,indent=2)+'\n', encoding='utf-8')


def selected_files(kind):
    paths = []
    for p in WF.rglob('*'):
        if not p.is_file() or p.is_symlink():
            continue
        rel = p.relative_to(WF).as_posix()
        if any(x in p.name.lower() for x in ['credential', 'token', 'secret', 'password']):
            continue
        if p.suffix.lower() in BLOCKED or p.name.startswith('.') or '__pycache__' in p.parts:
            continue
        if any(x in rel for x in ('/snapshots/','/.legacy_file_map.json','/reference/uart_report_raw/')):
            continue
        if kind == 'review':
            allowed = (
                rel == 'README.md' or
                (rel.startswith('phase_01_rtl/') and p.suffix == '.v') or
                (rel.startswith('phase_02_parsing/') and p.suffix == '.py') or
                (rel.startswith('phase_03_ai_verification/') and p.suffix == '.py') or
                (rel.startswith('phase_04_uart_novelty/') and (p.suffix in {'.py','.md'})) or
                rel in {
                    'evaluation/PHASE_REVIEW_SUMMARY.md',
                    'evaluation/workflow_status.json',
                    'evaluation/REVIEW_READINESS.json',
                    'evaluation/verification_summary.json',
                    'docs/PHASE_EXECUTION_GUIDE.md',
                    'docs/RESEARCH_SCOPE.md',
                    'docs/REVIEW_DEMONSTRATION.md',
                } or
                (rel.startswith('evaluation/figures/') and p.suffix.lower()=='.png')
            )
            # Exclude incomplete older editable review guide; a refreshed Word
            # document must be produced separately from the verified Markdown.
            if not allowed: continue
        else:
            allowed = (
                rel in {
                    'evaluation/workflow_status.json',
                    'evaluation/PHASE_REVIEW_SUMMARY.md',
                    'evaluation/REVIEW_READINESS.json',
                    'phase_04_uart_novelty/UART_INTEGRATED_RESEARCH_REPORT.md',
                    'phase_04_uart_novelty/UART_INTEGRATED_RESEARCH_REPORT.json',
                } or
                rel.startswith('phase_02_parsing/results/') or
                rel.startswith('phase_03_ai_verification/results/') or
                rel.startswith('evaluation/reference/') or
                rel.startswith('phase_04_uart_novelty/reference/')
            )
            if not allowed: continue
        need(p.resolve().is_relative_to(WF), f'External-path file blocked: {rel}')
        need(not re.search(r'(?i)(?:^|/)(?:day|extension_day)[_-]?\d+', rel),
             f'Chronological path found in phase package: {rel}')
        paths.append((rel,p))
    return sorted(paths)


def make_zip(output, kind):
    files = selected_files(kind)
    need(files, f'No {kind} package files selected')
    hashes = {f'phase_workflow/{rel}': digest(p) for rel,p in files}
    manifest = {
        'package_type': kind,
        'created_utc': datetime.now(timezone.utc).isoformat(),
        'file_count': len(files),
        'sha256': hashes,
        'scope': 'Presentation/source summary' if kind=='review' else 'Selected experiment logs/results and historical mapped evidence',
        'research_status': 'Technical audit PASS; broader research submission tasks pending',
    }
    with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=8) as z:
        for rel,p in files:
            z.write(p,arcname=f'phase_workflow/{rel}')
        z.writestr('phase_workflow/PACKAGE_MANIFEST.json',json.dumps(manifest,indent=2)+'\n')
    with zipfile.ZipFile(output) as z:
        need(z.testzip() is None, f'Archive CRC failed: {output}')
        need(len(z.namelist())==len(files)+1, f'Unexpected archive contents: {output}')
        for rel,expected in hashes.items():
            need(hashlib.sha256(z.read(rel)).hexdigest() == expected,
                 f'File checksum validation failed: {rel}')
    return len(files)


def main():
    print('========== PHASE 4B: TECHNICAL EVIDENCE VALIDATION ==========')
    data,audit=validate()
    print('[PASS] All 12 phase-gate checks and original 18/18 audit')
    print('[PASS] Actual Hermes response + 10 validated scenarios')
    print('[PASS] 12 simulation result JSON files and self-checking testbenches')
    print('[PASS] All initial AI bins covered at four CPB settings')
    print('[PASS] Historic mapped UART architecture results')
    print('\n========== REFRESH PHASE REVIEW DOCUMENTATION ==========')
    write_review_files(data,audit)
    print('[PASS] Project README, review summary, research scope and demonstration guide')
    print('[PASS] Old pending status replaced in review-facing metadata')
    print('\n========== CREATE SEPARATE REVIEW AND EVIDENCE PACKAGES ==========')
    review=Path.home()/'MTech_Phase_Review_Files.zip'
    evidence=Path.home()/'MTech_Phase_Verification_Evidence.zip'
    for path,kind in ((review,'review'),(evidence,'evidence')):
        count=make_zip(path,kind)
        print(f'[PASS] {kind.upper()}: {count} files; SHA256 manifest verified: {path}')
    print('\n========== PHASE 4B STATUS ==========')
    print('TECHNICAL VERIFICATION: PASS (12/12)')
    print('REVIEW-FACING STRUCTURE: UPDATED')
    print('THESIS/PRIOR-ART/REPEATABILITY: PENDING')
    print('PHASE 4B PACKAGING: PASS')


if __name__=='__main__':
    try:
        main()
    except (OSError, KeyError, ValueError, TypeError, RuntimeError) as exc:
        print('[FAIL] Phase 4B:', exc, file=sys.stderr)
        sys.exit(1)
