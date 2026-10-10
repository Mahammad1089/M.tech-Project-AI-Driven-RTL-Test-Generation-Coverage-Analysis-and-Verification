#!/usr/bin/env python3
"""Phase-based project review summary derived from actual verified evidence.

Never says UART AI is pending when the audited workflow and AI experiment PASS.
Historical evidence and new AI research are reported separately.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

WF = Path(__file__).resolve().parents[1]
EV = WF / 'evaluation'
REF = EV / 'reference'
OUT = EV / 'PHASE_REVIEW_SUMMARY.md'
AI = WF / 'phase_03_ai_verification/results/evaluation_summary.json'
AUDIT = EV / 'workflow_status.json'
UART = WF / 'phase_04_uart_novelty/reference/uart_report.json'
CPBS = [8, 16, 32, 64]


def load_json(path):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError, TypeError):
        return {}


def read_csv(path):
    with path.open(newline='', encoding='utf-8') as handle:
        return list(csv.DictReader(handle))


def evidence_pass(audit, ai):
    if not (audit.get('status') == 'PASS' and
            audit.get('passed') == audit.get('total') == 12 and
            len(audit.get('checks', [])) == 12 and
            all(item.get('status') == 'PASS' for item in audit['checks'])):
        return False
    if not (ai.get('status') == 'PASS' and
            ai.get('ai_generation') == 'HERMES_CHAT_ONESHOT' and
            ai.get('closure_target_met') is True and
            ai.get('final_ai_coverage') == 100.0 and
            ai.get('ai_total_scenarios') == 10):
        return False
    suites = ai.get('suites', {})
    for key in ('directed', 'random', 'ai_initial'):
        s = suites.get(key, {})
        if not (s.get('all_pass') is True and
                s.get('failed_checks') == 0 and
                s.get('tested_cpbs') == CPBS and
                s.get('checks', 0) > 0):
            return False
    return True


def main():
    historic = read_csv(REF / 'master_requirements.csv')
    if len(historic) != 18 or any(
            row.get('reconciled_status') != 'PASS' for row in historic):
        raise SystemExit('[FAIL] Historical 18/18 technical audit is not valid')
    uart = load_json(UART)
    if uart.get('status') != 'PASS':
        raise SystemExit('[FAIL] Archived UART architecture result is unavailable')

    audit = load_json(AUDIT)
    ai = load_json(AI)
    verified = evidence_pass(audit, ai)
    lines = [
        '# Phase-Oriented M.Tech RTL Verification — Research Review', '',
        '## Development flow', '',
        '| Phase | Function | Verified source |',
        '|---|---|---|',
        '| Phase 1 — RTL Design | Baseline and optimized ALU, FIFO, FSM, UART | `phase_01_rtl/` |',
        '| Phase 2 — RTL Parsing | PyVerilog AST to UART knowledge JSON | `phase_02_parsing/` |',
        '| Phase 3 — AI Verification | Hermes scenarios, independent oracle, Icarus simulation, coverage | `phase_03_ai_verification/` |',
        '| Phase 4 — Research Evaluation | PPA, repeatability, fault sensitivity and gap closure | `phase_04_uart_novelty/`, `evaluation/` |',
        '', '## Evidence-verified status', '',
        '- Original technical audit: **18/18 PASS** (archived ALU, FIFO, FSM and UART evidence).',
    ]
    if verified:
        lines.append('- Integrated RTL/PyVerilog/Hermes/UART workflow: **12/12 PASS**.')
        lines.append('- AI-generated UART scenario run: **verified live model call, validated scenarios, passing simulations, and 10/10 defined functional bins**.')
        lines.extend(['', '| Method | Scenarios | Minimum bin coverage | Checks | Failed checks |',
                      '|---|---:|---:|---:|---:|'])
        for title, key in [('Directed', 'directed'),
                           ('Deterministic random', 'random'),
                           ('Hermes AI initial', 'ai_initial')]:
            s = ai['suites'][key]
            budget = ai.get('comparisons', {}).get(key, {}).get('scenario_budget', '—')
            lines.append(f"| {title} | {budget} | {s['min_coverage_pct']:g}% | "
                         f"{s['checks']:,} | {s['failed_checks']} |")
    else:
        lines.extend([
            '- New UART Hermes integration: **PENDING fresh audited evidence in this checkout**.',
            '- The historical audit must not be interpreted as a new Hermes/UART PASS.',
        ])

    lines.extend([
        '', '## Historical results (independent evidence)', '',
        '- ALU equivalence: 2,048/2,048 checks; 5-fF mapped area/power improvements: 13.28%/14.78%.',
        '- FIFO equivalence: 124,008/124,008 checks, four configurations.',
        '- FSM: 20 functionally verified variants and 147,844 independent checks.',
        '- UART architecture: archived baseline/optimized/hybrid mapping and pre-layout estimates.',
        '', '## Extended research evidence', '',
        'The following follow-up studies are archived independently under `evaluation/`:',
        '- `repeatability/`: ten-seed random strategies and independent Hermes generations.',
        '- `fault_injection/`: original and corrected-oracle UART mutation tests.',
        '- `feedback_closure/`: targeted feedback experiment and matched directed control.',
        '- `phase_04_uart_novelty/research/`: literature report and evidence audit.',
        '', 'The evidence archive—not this summary—is authoritative for repeatability, mutation',
        'score, feedback cost and confidence limitations. The selected Git source tree does not',
        'include all original simulation outputs.',
        '', '## Responsible research claims', '',
        '- AI coverage is defined against ten scenario-based functional bins; not formal proof.',
        '- Balanced-directed verification can match the observed AI coverage and fault sensitivity.',
        '- Correcting reset-cycle assertions improves observability; it does not make a model smarter.',
        '- UART mapped area and estimated power are independent of the Hermes verification result.',
        '- The project remains simulation-only; no physical silicon or post-route proof is claimed.',
        '- Reproducing fresh AI calls requires a supported provider/model; reports are not guaranteed identical.',
        '', '## Reviewer documents', '',
        '- `docs/MTech_Phase_4F_Research_Thesis_Draft.docx`',
        '- `docs/MTech_Phase_4F_Review_Presentation.pptx`',
        '- `evaluation/workflow_status.json` (generated local technical gate)',
        '- `phase_04_uart_novelty/research/PHASE4E_EVIDENCE_TRACE.md` (research evidence map)',
        '', 'Old execution-era paths are retained internally solely for historical traceability.',
        ''
    ])
    OUT.write_text('\n'.join(lines), encoding='utf-8')
    print('[PASS] Phase-oriented summary refreshed:', OUT)
    print('PROJECT STATUS:', '12/12 PASS' if verified else 'NEW AI EVIDENCE PENDING IN THIS CHECKOUT')


if __name__ == '__main__':
    main()
