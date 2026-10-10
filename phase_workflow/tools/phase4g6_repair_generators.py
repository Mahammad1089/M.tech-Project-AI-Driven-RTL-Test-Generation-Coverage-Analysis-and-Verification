#!/usr/bin/env python3
"""Repair stale phase review status generators without touching experiment data.

Usage (from AI_RTL_Verification repository root):
 python3 phase_workflow/tools/phase4g6_repair_generators.py --dry-run
 python3 phase_workflow/tools/phase4g6_repair_generators.py --apply

Inspects known package interfaces, backups old scripts and summaries into /tmp,
updates only two generators, and refreshes the Git candidate SHA-256 manifest.
Does NOT git add/commit/push or modify UART RTL/evidence/results.
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
import py_compile
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path.cwd().resolve()
WF = ROOT / "phase_workflow"
ORGANIZER = WF / "tools/organize.py"
BUILDER = WF / "evaluation/build_review_summary.py"
SUMMARY = WF / "evaluation/PHASE_REVIEW_SUMMARY.md"
METADATA = WF / "evaluation/verification_summary.json"
MANIFEST = Path("/tmp/phase4g_reviewed_manifest.txt")
DIGESTS = Path("/tmp/phase4g_reviewed_sha256.txt")

BUILDER_REPLACEMENT = r'''#!/usr/bin/env python3
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
'''


def revised_organizer(original: str) -> str:
    anchors = [
        "    pub=WF/'evaluation/verification_summary.json'\n",
        "             'status':'HISTORICALLY_VERIFIED',\n",
        "             'uart_ai_integration':'NOT_YET_VERIFIED',\n",
        "             'audit_note':'Recorded evidence has been copied without altering it. New AI-UART experiments require fresh simulation.',\n",
        "    print('[PENDING] AI-guided UART integration requires live Hermes and Icarus results')\n",
    ]
    for anchor in anchors:
        if original.count(anchor) != 1:
            raise RuntimeError('Organizer changed from inspected package: expected anchor missing. Stop for manual inspection: ' + anchor.strip()[:75])

    state = '''    audit_path=WF/'evaluation/workflow_status.json'
    ai_path=WF/'phase_03_ai_verification/results/evaluation_summary.json'
    phase_verified=False
    try:
        w=json.loads(audit_path.read_text(encoding='utf-8'))
        a=json.loads(ai_path.read_text(encoding='utf-8'))
        phase_verified=(
            w.get('status')=='PASS' and w.get('passed')==w.get('total')==12
            and len(w.get('checks',[]))==12
            and all(x.get('status')=='PASS' for x in w['checks'])
            and a.get('status')=='PASS' and a.get('ai_generation')=='HERMES_CHAT_ONESHOT'
            and a.get('closure_target_met') is True
            and a.get('final_ai_coverage')==100.0
            and all(a.get('suites',{}).get(k,{}).get('all_pass') is True
                    for k in ('directed','random','ai_initial')))
    except (OSError,ValueError,TypeError):
        pass
'''
    out = original.replace(anchors[0], state + anchors[0], 1)
    out = out.replace(anchors[1], "             'status':'PHASE_WORKFLOW_VERIFIED' if phase_verified else 'HISTORICALLY_VERIFIED',\n", 1)
    out = out.replace(anchors[2], "             'uart_ai_integration':'VERIFIED_12_OF_12' if phase_verified else 'PENDING_FRESH_VERIFICATION',\n", 1)
    out = out.replace(anchors[3], "             'audit_note':'Archived 18/18 evidence preserved; new four-phase audit and live Hermes UART results validated.' if phase_verified else 'Historical 18/18 evidence preserved; new UART AI evidence is incomplete or absent.',\n", 1)
    out = out.replace(anchors[4], "    print('[PASS] New AI UART integration verified (12/12)' if phase_verified else '[PENDING] New AI UART integration requires valid local evidence')\n", 1)
    return out


def verify_environment():
    if not (ROOT / '.git').exists():
        raise RuntimeError('Run from the repository root (.git missing)')
    for p in (ORGANIZER, BUILDER, MANIFEST):
        if not p.is_file() or p.is_symlink():
            raise RuntimeError('Required file missing/symlink: ' + str(p))
    builder = BUILDER.read_text(encoding='utf-8')
    organizer = ORGANIZER.read_text(encoding='utf-8')
    if ('UART-specific run pending' not in builder or
            'evaluation/reference' not in builder or
            'PHASE_REVIEW_SUMMARY.md' not in builder):
        raise RuntimeError('Current builder differs from expected legacy file; no changes made.')
    if "'NOT_YET_VERIFIED'" not in organizer:
        raise RuntimeError('Organizer differs from expected legacy file; no changes made.')
    return {BUILDER: builder, ORGANIZER: organizer}


def main():
    parser = argparse.ArgumentParser()
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument('--dry-run', action='store_true')
    modes.add_argument('--apply', action='store_true')
    args = parser.parse_args()

    old = verify_environment()
    new = {BUILDER: BUILDER_REPLACEMENT,
           ORGANIZER: revised_organizer(old[ORGANIZER])}
    print('========== PHASE 4G-6: REPAIR STALE STATUS GENERATORS ==========')
    print('[CHECK] Existing file patterns verified')
    for path, contents in new.items():
        compile(contents, str(path), 'exec')
        print('[PASS] Proposed syntax:', path.relative_to(ROOT))

    for path in (BUILDER, ORGANIZER):
        delta = list(difflib.unified_diff(
            old[path].splitlines(), new[path].splitlines(),
            fromfile='before/' + path.name,
            tofile='after/' + path.name,
            lineterm=''))
        print('[REVIEW]', path.relative_to(ROOT), 'modified lines:', len(delta))
        for line in delta[:15]:
            print(line)
        if len(delta) > 15:
            print(f'  ... {len(delta)-15} more diff lines not displayed')

    if args.dry_run:
        print('PHASE 4G-6 PREFLIGHT: PASS (nothing modified)')
        return

    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    backups = Path('/tmp') / ('phase4g6_backup_' + stamp)
    backups.mkdir(parents=True, exist_ok=False)
    for path in (BUILDER, ORGANIZER, SUMMARY, METADATA):
        if path.is_file():
            shutil.copy2(path, backups / path.name)
    print('[PASS] Original scripts/review metadata backed up:', backups)

    try:
        for path, contents in new.items():
            fd, temporary = tempfile.mkstemp(prefix='.phase4g6_', dir=path.parent)
            try:
                with os.fdopen(fd, 'w', encoding='utf-8') as handle:
                    handle.write(contents)
                os.chmod(temporary, path.stat().st_mode & 0o777)
                os.replace(temporary, path)
            finally:
                if os.path.exists(temporary):
                    os.unlink(temporary)
            py_compile.compile(str(path), doraise=True)
    except Exception:
        for path in (BUILDER, ORGANIZER):
            shutil.copy2(backups / path.name, path)
        raise

    print('[PASS] Two generators updated; original experiment evidence unchanged')
    entries = {line for line in MANIFEST.read_text(encoding='utf-8').splitlines() if line}
    entries.add('phase_workflow/tools/phase4g6_repair_generators.py')
    missing = [p for p in entries if not (ROOT / p).is_file()]
    if missing:
        raise RuntimeError('Manifest has missing paths: ' + ', '.join(missing[:6]))
    MANIFEST.write_text('\n'.join(sorted(entries)) + '\n', encoding='utf-8')
    DIGESTS.write_text(''.join(
        hashlib.sha256((ROOT / p).read_bytes()).hexdigest() + '  ' + p + '\n'
        for p in sorted(entries)), encoding='utf-8')
    print('[PASS] Manifest and checksums refreshed,', len(entries), 'candidate files')
    print('PHASE 4G-6: PATCH APPLIED (not yet committed)')
    print('BACKUP LOCATION:', backups)
    print('NEXT: run updated organizer/check-only, build summary, and audit')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, RuntimeError, SyntaxError, py_compile.PyCompileError) as exc:
        print('[FAIL]', exc, file=sys.stderr)
        raise SystemExit(1)
