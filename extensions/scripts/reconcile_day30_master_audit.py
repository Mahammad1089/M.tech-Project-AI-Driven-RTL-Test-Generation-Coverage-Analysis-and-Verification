#!/usr/bin/env python3
"""Non-destructive reconciliation of the 18 original M.Tech master requirements.

Run from the AI_RTL_Verification repository root.
Writes ONLY to extensions/results/day30/master_audit_reconciled/.
"""
from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path.cwd()
OLD = Path('extensions/results/day30/master_audit/master_requirements_audit.csv')
OUT = Path('extensions/results/day30/master_audit_reconciled')

PATHS = {
    'alu_base': 'rtl/alu.v',
    'alu_opt': 'extensions/rtl/optimized/alu_opt.v',
    'alu_tb': 'extensions/testbench/tb_alu_equivalence.v',
    'alu_eq': 'extensions/results/day25/alu_equivalence.log',
    'alu_report': 'extensions/results/day30/alu_final_report/day30_alu_final_report.json',
    'alu_5ff': 'extensions/results/day30/alu_5ff_sensitivity/day30_alu_5ff_comparison.json',
    'fifo_base': 'rtl/fifo.v',
    'fifo_opt': 'extensions/rtl/optimized/fifo_opt.v',
    'fifo_report': 'extensions/results/day30/fifo_final_report/day30_fifo_final_report.json',
    'fifo_table': 'extensions/results/day30/fifo_final_report/day30_fifo_final_comparison.csv',
    'fsm_orig': 'rtl/fsm_1011.v',
    'fsm_mealy': 'extensions/rtl/fsm_variants/fsm_mealy_ext.v',
    'fsm_moore': 'extensions/rtl/fsm_variants/fsm_moore_ext.v',
    'fsm_old_audit': 'extensions/results/day30/day30_fsm_functional_audit.log',
    'fsm_matrix': 'extensions/results/day30/fsm_20_matrix/day30_fsm_20_matrix_results.csv',
    'fsm_independent': 'extensions/results/day30/fsm_independent_coverage/day30_fsm_independent_coverage.json',
    'fsm_independent_csv': 'extensions/results/day30/fsm_independent_coverage/day30_fsm_independent_coverage.csv',
    'fsm_ppa20': 'extensions/results/day30/fsm_ppa_extension/day30_fsm_20_ppa_summary.csv',
    'fsm_ppa13': 'extensions/results/day26/day26_fsm_ppa_summary.csv',
    'day27_eff': 'extensions/results/day27/day27_efficiency_metrics.csv',
    'day27_mealy': 'extensions/results/day27/day27_mealy_moore_comparison.csv',
    'day27_pareto': 'extensions/results/day27/day27_pareto_analysis.csv',
    'uart_tx': 'extensions/rtl/uart/uart_tx.v',
    'uart_rx': 'extensions/rtl/uart/uart_rx.v',
    'uart_tx_opt': 'extensions/rtl/uart/optimized/uart_tx_opt.v',
    'uart_rx_opt': 'extensions/rtl/uart/optimized/uart_rx_opt.v',
    'uart_report': 'extensions/results/day30/uart/final_report/day30_uart_final_report.json',
    'uart_comparison': 'extensions/results/day30/uart/final_report/day30_uart_architecture_comparison.csv',
}

def present(key: str) -> bool:
    p = ROOT / PATHS[key]
    return p.is_file() and p.stat().st_size > 0

def load_json(key):
    if not present(key):
        return None
    try:
        return json.loads((ROOT / PATHS[key]).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None

def load_csv(key):
    if not present(key):
        return None
    try:
        with (ROOT / PATHS[key]).open(newline='', encoding='utf-8') as f:
            return list(csv.DictReader(f))
    except (OSError, UnicodeError, csv.Error):
        return None

def report_pass(data):
    """Only explicit status fields count, never a lone PASS inside incidental text."""
    if not isinstance(data, dict):
        return False
    for key in ('status', 'overall_status', 'final_status', 'result', 'verdict'):
        value = data.get(key)
        if isinstance(value, str) and value.strip().upper() in ('PASS', 'PASSED', 'SUCCESS'):
            return True
    return False

def find_numeric(data, target):
    if isinstance(data, dict):
        return any(find_numeric(v, target) for v in data.values())
    if isinstance(data, list):
        return any(find_numeric(v, target) for v in data)
    if isinstance(data, (int, float)) and not isinstance(data, bool):
        return data == target
    if isinstance(data, str):
        try:
            return float(data.replace(',', '').strip()) == target
        except ValueError:
            pass
    return False

def has_positive_numeric(row, field):
    try:
        return float(row[field]) > 0
    except (KeyError, ValueError, TypeError):
        return False

def status_row(req_id, module, requirement, old_status, good, evidence, note='', *, historical=False):
    if historical and good:
        state = 'HISTORICAL_SCOPE'
    elif good:
        state = 'PASS'
    else:
        state = 'REVIEW'
    return {
        'id': req_id,
        'module': module,
        'requirement': requirement,
        'old_status': old_status,
        'reconciled_status': state,
        'evidence': '; '.join(PATHS[k] for k in evidence),
        'notes': note,
    }

def main():
    if not (ROOT / OLD).is_file():
        sys.exit(f'[FAIL] Run from repository root. Missing: {OLD}')
    with (ROOT / OLD).open(newline='', encoding='utf-8') as f:
        old_rows = list(csv.DictReader(f))
    if len(old_rows) != 18:
        sys.exit(f'[FAIL] Expected 18 original audit records, found {len(old_rows)}')
    old_by_id = {r.get('id'): r for r in old_rows}
    if len(old_by_id) != 18:
        sys.exit('[FAIL] Duplicate or missing original audit IDs')

    eqlog = (ROOT / PATHS['alu_eq']).read_text(errors='replace') if present('alu_eq') else ''
    alu_eq = (
        re.search(r'TOTAL CHECKS\s*:\s*2048\b', eqlog)
        and re.search(r'PASSED CHECKS\s*:\s*2048\b', eqlog)
        and re.search(r'FAILED CHECKS\s*:\s*0\b', eqlog)
        and 'DAY 25 ALU EQUIVALENCE: PASS' in eqlog
    )
    alu_report, alu5 = load_json('alu_report'), load_json('alu_5ff')
    alu_ppa = (
        report_pass(alu_report) and report_pass(alu5)
        and len(alu5.get('results', [])) == 2
        and all(r.get('timing_status') == 'MET' for r in alu5['results'])
        and all(has_positive_numeric(r, 'mapped_area_um2') and has_positive_numeric(r, 'total_power_uw') for r in alu5['results'])
    )

    fifo_report = load_json('fifo_report')
    fifo_rows = load_csv('fifo_table')
    fifo_strict = (
        report_pass(fifo_report)
        and isinstance(fifo_rows, list) and len(fifo_rows) == 4
        and all(row and any(str(v).strip() for v in row.values()) for row in fifo_rows)
    )
    fifo_full = fifo_strict and find_numeric(fifo_report, 124008)

    matrix = load_csv('fsm_matrix')
    patterns = ('1011', '1101', '1001', '10101', '1110')
    wanted_matrix = {f'{a}_{p}_{m}' for p in patterns for a in ('mealy', 'moore') for m in ('overlap', 'nonoverlap')}
    matrix_good = False
    mealy_good = moore_good = False
    if matrix is not None:
        ids = [r.get('case_id') for r in matrix]
        matrix_good = len(matrix) == 20 and set(ids) == wanted_matrix and len(set(ids)) == 20 and all(r.get('result') == 'PASS' for r in matrix)
        mealy_good = matrix_good and sum(r['architecture'] == 'mealy' for r in matrix) == 10
        moore_good = matrix_good and sum(r['architecture'] == 'moore' for r in matrix) == 10
    coverage = load_json('fsm_independent')
    coverage_csv = load_csv('fsm_independent_csv')
    coverage_good = (
        present('fsm_independent') and isinstance(coverage_csv, list) and len(coverage_csv) == 5
        and find_numeric(coverage, 147844)
    )
    fsm_audit_log = (ROOT / PATHS['fsm_old_audit']).read_text(errors='replace') if present('fsm_old_audit') else ''
    fsm_old_good = 'PASS' in fsm_audit_log.upper() and not re.search(r'(?m)^\s*\[FAIL\]', fsm_audit_log)

    ppa_old = load_csv('fsm_ppa13')
    ppa20 = load_csv('fsm_ppa20')
    wanted_ppa = {f'{a}_{p}_overlap_{o}' for p in patterns for a in ('mealy', 'moore') for o in (0,1)}
    ppa_good = False
    if ppa20 is not None:
        names = [r.get('configuration') for r in ppa20]
        ppa_good = (
            len(ppa20) == 20 and set(names) == wanted_ppa and len(set(names)) == 20
            and all(has_positive_numeric(r, 'area_um2') and has_positive_numeric(r, 'total_power_uw')
                    and float(r.get('setup_slack_ns', '-1')) >= 0 and r.get('timing_status') == 'MET'
                    for r in ppa20)
        )
    ppa13_good = ppa_old is not None and len(ppa_old) == 13
    day27 = {key: load_csv(key) for key in ('day27_eff','day27_mealy','day27_pareto')}
    day27_expected = {'day27_eff': 13, 'day27_mealy': 6, 'day27_pareto': 13}
    day27_good = {key: isinstance(value, list) and len(value) == day27_expected[key]
                  and all(bool(row) for row in value)
                  for key, value in day27.items()}

    uart_json = load_json('uart_report')
    uart_csv = load_csv('uart_comparison')
    uart_report_good = report_pass(uart_json)
    uart_data_good = uart_report_good and isinstance(uart_csv, list) and len(uart_csv) > 0
    # The final UART JSON generator did not necessarily use uniform counter field names.
    # This audit marks UART functional evidence as REVIEW if PASS isn't explicit.

    checks = {
        'ALU-01': (present('alu_base') and bool(alu_eq), ['alu_base','alu_eq'], 'Baseline module verified against optimized ALU.'),
        'ALU-02': (present('alu_opt') and bool(alu_eq) and alu_ppa, ['alu_opt','alu_eq','alu_5ff'], 'Area/timing/power validated at 5 fF.'),
        'ALU-03': (present('alu_tb') and bool(alu_eq), ['alu_tb','alu_eq'], '2048/2048 exhaustive input combinations passed.'),
        'FIFO-01': (present('fifo_base') and fifo_full, ['fifo_base','fifo_report','fifo_table'], 'Requires 124008 checks encoded in final JSON.'),
        'FIFO-02': (present('fifo_opt') and fifo_full, ['fifo_opt','fifo_report','fifo_table'], 'Four configurations; 124008 checks.'),
        'FSM-01': (present('fsm_orig') and fsm_old_good, ['fsm_orig','fsm_old_audit'], 'Original 1011 regression audit.'),
        'FSM-02': (present('fsm_mealy') and mealy_good and coverage_good, ['fsm_mealy','fsm_matrix','fsm_independent'], '10 Mealy variants passed; independent coverage validated.'),
        'FSM-03': (present('fsm_moore') and moore_good and coverage_good, ['fsm_moore','fsm_matrix','fsm_independent'], '10 Moore variants passed; independent coverage validated.'),
        'FSM-04': (fsm_old_good, ['fsm_old_audit'], 'Existing Day 30 original FSM audit.'),
        'FSM-05': (matrix_good and coverage_good, ['fsm_matrix','fsm_independent','fsm_independent_csv'], '20 functional variants and 147844 independent checks.'),
        'PPA-01': (ppa13_good and ppa_good, ['fsm_ppa13','fsm_ppa20'], '13 historic original+extended records; 20 extended variants in Day 30.'),
        'PPA-02': (day27_good['day27_eff'], ['day27_eff'], 'HISTORICAL: 13 records; not expanded to 20 variants.'),
        'PPA-03': (day27_good['day27_mealy'], ['day27_mealy'], 'HISTORICAL: 6 pair comparisons; not expanded to 10.'),
        'PPA-04': (day27_good['day27_pareto'], ['day27_pareto'], 'HISTORICAL: 13 records; not expanded to 20 variants.'),
        'UART-01': (all(present(k) for k in ('uart_tx','uart_rx','uart_tx_opt','uart_rx_opt')), ['uart_tx','uart_rx','uart_tx_opt','uart_rx_opt'], 'Baseline and optimized TX/RX RTL.'),
        'UART-02': (uart_report_good, ['uart_report'], 'Final report must contain an explicit top-level PASS status.'),
        'UART-03': (uart_report_good and all(present(k) for k in ('uart_tx_opt','uart_rx_opt')), ['uart_tx_opt','uart_rx_opt','uart_report'], 'Optimization and equivalence report.'),
        'UART-04': (uart_data_good, ['uart_report','uart_comparison'], 'Architecture comparison and final report.'),
    }
    expected_ids = set(checks)
    if set(old_by_id) != expected_ids:
        sys.exit('[FAIL] Original audit requirement IDs have changed; manual reconciliation needed')

    results = []
    for row in old_rows:
        rid = row['id']
        good, files, note = checks[rid]
        results.append(status_row(rid, row['module'], row['requirement'], row['status'], good, files, note,
                                  historical=(rid in ('PPA-02','PPA-03','PPA-04'))))

    OUT.mkdir(parents=True, exist_ok=True)
    out_csv = OUT / 'day30_master_requirements_reconciled.csv'
    out_json = OUT / 'day30_master_requirements_reconciled.json'
    out_md = OUT / 'day30_master_requirements_reconciled.md'
    with out_csv.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)
    tally = dict(Counter(x['reconciled_status'] for x in results))
    overall = 'REVIEW' if tally.get('REVIEW', 0) else 'PASS_WITH_HISTORICAL_SCOPE'
    payload = {
        'generated_utc': datetime.now(timezone.utc).isoformat(),
        'source': str(OLD), 'scope': 'Reconciliation of 18 original requirements only',
        'overall_status': overall, 'status_counts': tally, 'requirements': results,
        'limitations': [
            'Day27 comparative reports remain historical at 13/6/13 rows.',
            'File existence plus a reported PASS is not a clean-room reproducibility test.',
            'Original 18 requirements do not include thesis documentation/publication readiness.',
            'Any REVIEW result requires checking report schema or underlying evidence before closing.',
            'No RTL, source reports or original master audit changed.',
        ],
    }
    out_json.write_text(json.dumps(payload, indent=2) + '\n', encoding='utf-8')
    md = [
        '# Day 30 — Reconciled Master Requirements', '',
        f'Overall: **{overall}**', '',
        f'Status counts: **{tally}**', '',
        '| ID | Module | Old status | Reconciled | Note |',
        '|---|---|---|---|---|',
    ]
    for r in results:
        md.append(f"| {r['id']} | {r['module']} | {r['old_status']} | {r['reconciled_status']} | {r['notes']} |")
    md.extend(['', '## Interpretation', '',
               '- `PASS` means the explicitly checked evidence was found and passed the defined checks.',
               '- `HISTORICAL_SCOPE` means the original Day 27 file is structurally present, but covers only its older configuration set.',
               '- `REVIEW` is a conservative signal; it may reflect an unknown JSON schema rather than a design failure.',
               '- This is **not** a clean-room end-to-end regeneration or publication-readiness certificate.', ''])
    out_md.write_text('\n'.join(md), encoding='utf-8')

    print('========== DAY 30 STEP 8A-3 — RECONCILED MASTER AUDIT ==========')
    for r in results:
        print(f"{r['id']:<9} {r['reconciled_status']:<18} {r['requirement']}")
    print('\nSTATUS COUNTS:', tally)
    print('OVERALL:', overall)
    print('CSV:', out_csv)
    print('JSON:', out_json)
    print('MARKDOWN:', out_md)
    print('ORIGINAL MASTER AUDIT: UNCHANGED')
    if overall == 'REVIEW':
        print('ACTION: Review flagged rows and underlying report fields.')
    else:
        print('ACTION: Historical Day 27 scope remains; final thesis deliverables require separate review.')
    return 0

if __name__ == '__main__':
    sys.exit(main())
