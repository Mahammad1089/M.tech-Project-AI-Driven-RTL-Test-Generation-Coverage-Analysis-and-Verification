#!/usr/bin/env python3
"""Phase 4D — UART mutation/fault-detection study.

Read-only with respect to existing RTL, Phase 3 evidence and Phase 4C results.
Mutates *copies* of optimized UART TX/RX; reference UART TX/RX remain frozen.
Each 10-scenario suite receives exactly the same mutants and CPB conditions.
Counts only correctly compiled, executed, assertion-detected mutants as killed.

Suggested WSL commands:
    python3 phase_workflow/tools/phase4d_mutation_test.py --dry-run
    python3 phase_workflow/tools/phase4d_mutation_test.py --cpbs 16
    python3 phase_workflow/tools/phase4d_mutation_test.py --cpbs 8 16 32 64
"""

import argparse
import csv
import difflib
import hashlib
import json
import re
import shutil
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

WF = Path(__file__).resolve().parents[1]
EVAL = WF / 'evaluation'
AI = WF / 'phase_03_ai_verification'
RTL = WF / 'phase_01_rtl' / 'uart'
KNOWLEDGE = WF / 'phase_02_parsing' / 'results' / 'uart_knowledge.json'
REFERENCE = AI / 'results' / 'evaluation_summary.json'
FRESH_ROOT = EVAL / 'repeatability' / 'hermes_trials'
RESULT_ROOT = EVAL / 'fault_injection'
SRC_NAMES = ('uart_tx.v', 'uart_tx_opt.v', 'uart_rx.v', 'uart_rx_opt.v')
SEEDS = [10007 + i * 104729 for i in range(10)]

# Exactly one targeted textual replacement per mutant; source is checked before patching.
# All patches affect only the optimized DUT while the baseline stays as the oracle.
MUTANTS = [
    dict(id='TX_START_DISABLED', file='uart_tx_opt.v', category='transaction',
         old='if (start) begin', new="if (1'b0 && start) begin",
         defect='TX never responds to start'),
    dict(id='TX_FIRST_DATA_BIT_INVERTED', file='uart_tx_opt.v', category='payload',
         old='tx<=shift_data[0]; state<=DATA;',
         new='tx<=~shift_data[0]; state<=DATA;',
         defect='First transmitted payload bit inverted'),
    dict(id='TX_EARLY_STOP', file='uart_tx_opt.v', category='protocol',
         old='if (bit_idx==7) begin tx<=1; state<=STOP; end',
         new='if (bit_idx==6) begin tx<=1; state<=STOP; end',
         defect='TX exits DATA after seven data bits'),
    dict(id='TX_DONE_SUPPRESSED', file='uart_tx_opt.v', category='handshake',
         old='tick<=0; state<=IDLE; busy<=0; done<=1; tx<=1;',
         new='tick<=0; state<=IDLE; busy<=0; done<=0; tx<=1;',
         defect='TX done pulse lost'),
    dict(id='TX_RESET_BUSY_FAULT', file='uart_tx_opt.v', category='reset',
         old="tx<=1'b1; busy<=0; done<=0;",
         new="tx<=1'b1; busy<=0; done<=0; if (busy) tx<=1'b0;",
         defect='TX reset drives incorrect idle level during active transfer'),
    dict(id='TX_55_PAYLOAD_CORRUPT', file='uart_tx_opt.v', category='data_corner',
         old='shift_data<=data_in; busy<=1; tx<=0; state<=START;',
         new="shift_data<=(data_in == 8'h55) ? (data_in ^ 8'h01) : data_in; busy<=1; tx<=0; state<=START;",
         defect='Only payload 0x55 corrupted'),
    dict(id='TX_BUSY_START_GLITCH', file='uart_tx_opt.v', category='busy_start',
         old='done<=0;\n            case (state)',
         new="done<=0;\n            if (start && busy) tx<=~tx;\n            case (state)",
         defect='Unexpected TX glitch when start is asserted while busy'),
    dict(id='RX_VALID_SUPPRESSED', file='uart_rx_opt.v', category='handshake',
         old='valid <= 1;', new='valid <= 0;',
         defect='RX valid pulse lost'),
    dict(id='RX_DATA_BIT_INVERTED', file='uart_rx_opt.v', category='payload',
         old='payload <= {rx_sync, payload[7:1]};',
         new='payload <= {~rx_sync, payload[7:1]};',
         defect='Received data bit inverted during shift'),
    dict(id='RX_FRAMING_FLAG_SUPPRESSED', file='uart_rx_opt.v', category='framing_error',
         old='framing_error <= 1;', new='framing_error <= 0;',
         defect='Invalid stop bit does not raise framing_error'),
    dict(id='RX_START_BUSY_SUPPRESSED', file='uart_rx_opt.v', category='handshake',
         old='busy <= 1;\n                        state <= START;',
         new='busy <= 0;\n                        state <= START;',
         defect='RX busy stays low when start bit detected'),
    dict(id='RX_AA_PAYLOAD_REJECTED', file='uart_rx_opt.v', category='data_corner',
         old='if (rx_sync) begin\n                            data_out <= payload;',
         new="if (rx_sync && payload != 8'hAA) begin\n                            data_out <= payload;",
         defect='Valid payload 0xAA incorrectly rejected'),
    dict(id='RX_BAD_STOP_ACCEPTED', file='uart_rx_opt.v', category='framing_error',
         old='if (rx_sync) begin\n                            data_out <= payload;',
         new="if (1'b1) begin\n                            data_out <= payload;",
         defect='Receiver incorrectly accepts invalid stop bit'),
    dict(id='RX_ZERO_PAYLOAD_CORRUPT', file='uart_rx_opt.v', category='data_corner',
         old='data_out <= payload;',
         new="data_out <= (payload == 8'h00) ? 8'h01 : payload;",
         defect='Only received payload 0x00 corrupted'),
]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def store(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def preflight():
    for p in [KNOWLEDGE, REFERENCE, EVAL / 'workflow_status.json']:
        if not p.is_file():
            raise RuntimeError(f'Required verified evidence missing: {p}')
    status = json.loads((EVAL / 'workflow_status.json').read_text())
    if (status.get('status'), status.get('passed'), status.get('total')) != ('PASS', 12, 12):
        raise RuntimeError('Historical 12/12 audit is not PASS')
    ai = json.loads(REFERENCE.read_text())
    if (ai.get('status'), ai.get('ai_generation')) != ('PASS', 'HERMES_CHAT_ONESHOT'):
        raise RuntimeError('Archived real Hermes UART reference is not PASS')
    knowledge = json.loads(KNOWLEDGE.read_text())
    hashes = {}
    for f in SRC_NAMES:
        path = RTL / f
        if not path.is_file():
            raise RuntimeError(f'Missing frozen RTL: {path}')
        actual = sha(path)
        expected = knowledge['source_analysis'][f[:-2]]['sha256']
        if actual != expected:
            raise RuntimeError(f'Frozen RTL hash mismatch: {f}')
        hashes[f] = actual
    if not FRESH_ROOT.is_dir():
        raise RuntimeError(f'Phase 4C-2 Hermes trials directory missing: {FRESH_ROOT}')
    candidates = sorted(p for p in FRESH_ROOT.glob('phase4c2_*') if p.is_dir() and (p/'phase4c2_summary.json').is_file())
    if not candidates:
        raise RuntimeError('No recorded Phase 4C-2 experiment found')
    fresh = candidates[-1]
    recorded = json.loads((fresh/'phase4c2_summary.json').read_text())
    if (recorded.get('planned_trials'), recorded.get('passed_trials'), recorded.get('failed_trials')) != (5, 5, 0):
        raise RuntimeError('Latest Phase 4C-2 does not contain five passing fresh trials')
    return hashes, fresh


def load_suites(fresh):
    sys.path.insert(0, str(AI))
    from testbench_generator import validate_scenarios
    import uart_ai_pipeline as pipeline
    # Load Phase 4C-1 generator from its actual installed path; do not implement a
    # different random distribution from the one already studied.
    tools = WF / 'tools'
    sys.path.insert(0, str(tools))
    import phase4c_repeatability as baseline

    suites = []
    for i in range(1, 6):
        p = fresh / 'calls' / f'ai_fresh_{i:02d}' / 'validated_scenarios.json'
        if not p.is_file():
            raise RuntimeError(f'Missing fresh Hermes validated scenarios: {p}')
        scenarios = validate_scenarios(json.loads(p.read_text()), maximum=10)
        if len(scenarios) != 10:
            raise RuntimeError(f'AI trial {i}: not exactly ten scenarios')
        suites.append(dict(name=f'hermes_fresh_{i:02d}', method='hermes_ai',
                           provenance=p.as_posix(), scenarios=scenarios))
    archived = AI / 'results' / 'hermes' / 'validated_ai_scenarios.json'
    if not archived.is_file():
        raise RuntimeError(f'Missing archived original Hermes scenarios: {archived}')
    scenarios = validate_scenarios(json.loads(archived.read_text()), maximum=10)
    if len(scenarios) != 10:
        raise RuntimeError('Archived Hermes trial: not exactly ten scenarios')
    suites.append(dict(name='hermes_archived', method='hermes_archived',
                       provenance=archived.as_posix(), scenarios=scenarios))

    balanced = baseline.balanced_directed()
    suites.append(dict(name='balanced_directed', method='balanced_directed',
                       provenance='phase4c_repeatability.balanced_directed', scenarios=balanced))
    for seed in SEEDS:
        suites.append(dict(name=f'protocol_random_{seed}', method='protocol_random',
                           provenance=f'phase4c_repeatability.protocol_random seed {seed}',
                           scenarios=baseline.protocol_random(seed)))
        suites.append(dict(name=f'payload_random_{seed}', method='payload_random',
                           provenance=f'uart_ai_pipeline.randomized seed {seed}',
                           scenarios=pipeline.randomized(seed)))
    for suite in suites:
        suite['scenarios'] = validate_scenarios(suite['scenarios'], maximum=10)
        if len(suite['scenarios']) != 10:
            raise RuntimeError(f'Non-10 scenario suite: {suite["name"]}')
    return suites


def materialize_mutants(out, originals):
    mutants = {}
    for m in MUTANTS:
        source = originals[m['file']]
        n = source.count(m['old'])
        if n != 1:
            raise RuntimeError(f'{m["id"]}: expected exactly 1 match, found {n}; source not modified')
        target = source.replace(m['old'], m['new'], 1)
        if target == source:
            raise RuntimeError(f'{m["id"]}: mutation did not change source')
        mutants[m['id']] = dict(m, mutated_sha256=hashlib.sha256(target.encode()).hexdigest(),
                                new_source=target)
        if out is not None:
            base = out / 'mutants' / m['id']
            base.mkdir(parents=True)
            for fname, text in originals.items():
                (base / fname).write_text(target if fname == m['file'] else text, encoding='utf-8')
            diff = ''.join(difflib.unified_diff(
                source.splitlines(keepends=True), target.splitlines(keepends=True),
                fromfile=m['file'] + ' (frozen)', tofile=m['file'] + ' (mutant)'))
            (base / 'mutation.patch').write_text(diff, encoding='utf-8')
    return mutants


def parse_sim(stdout, stderr, return_code):
    def match(label):
        m = re.search(r'^' + re.escape(label) + r'=(\d+)\s*$', stdout, re.M)
        return int(m.group(1)) if m else None
    failed = match('FAILED_CHECKS')
    checks = match('TOTAL_CHECKS')
    cycles = match('CYCLES')
    v = re.search(r'^VERDICT=(PASS|FAIL)\s*$', stdout, re.M)
    if return_code != 0 or v is None or checks is None or failed is None or cycles is None or checks <= 0 or cycles <= 0:
        return ('INVALID', checks, failed, cycles)
    if (failed == 0 and v.group(1) == 'PASS'):
        return ('SURVIVED', checks, failed, cycles)
    if (failed > 0 and v.group(1) == 'FAIL' and 'ASSERT_FAIL:' in stdout):
        return ('KILLED', checks, failed, cycles)
    return ('INVALID', checks, failed, cycles)


def execute_case(out, suite, cpb, mutant_id, mutant_folder, max_seconds):
    from testbench_generator import make_tb
    group = 'clean_controls' if mutant_id == 'CONTROL' else 'mutation_runs'
    folder = out / group / suite['name'] / f'cpb{cpb}' / mutant_id
    folder.mkdir(parents=True, exist_ok=False)
    tb = folder / 'tb_uart_phase.v'
    tb.write_text(make_tb(suite['scenarios'], cpb), encoding='utf-8')
    exe = folder / 'uart_sim.out'
    cmd = ['iverilog', '-g2012', '-s', 'tb_uart_phase', '-o', str(exe), str(tb)]
    cmd.extend(str(mutant_folder / name) if mutant_folder else str(RTL / name) for name in SRC_NAMES)
    try:
        comp = subprocess.run(cmd, capture_output=True, text=True, timeout=max_seconds)
        (folder / 'compile.log').write_text(comp.stdout + '\n' + comp.stderr, encoding='utf-8')
        if comp.returncode != 0:
            classification, checks, failed, cycles = 'INVALID', None, None, None
            (folder / 'simulation.log').write_text('NOT RUN — compilation failed\n', encoding='utf-8')
        else:
            proc = subprocess.run(['vvp', str(exe)], capture_output=True, text=True, timeout=max_seconds)
            (folder / 'simulation.log').write_text(proc.stdout + '\n' + proc.stderr, encoding='utf-8')
            classification, checks, failed, cycles = parse_sim(proc.stdout, proc.stderr, proc.returncode)
    except subprocess.TimeoutExpired as ex:
        classification, checks, failed, cycles = 'INVALID', None, None, None
        (folder / 'timeout.log').write_text(f'TIMEOUT after {max_seconds}s: {ex}\n', encoding='utf-8')
    return dict(suite=suite['name'], method=suite['method'], cpb=cpb,
                mutant=mutant_id, outcome=classification, checks=checks,
                failed_checks=failed, cycles=cycles,
                logs=folder.relative_to(out).as_posix())


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = ['suite', 'method', 'cpb', 'mutant', 'outcome',
               'checks', 'failed_checks', 'cycles', 'logs']
    with path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def summarise(rows, suite_names, cpbs):
    mutant_names = [m['id'] for m in MUTANTS]
    by_suite = []
    for suite in suite_names:
        selected = [r for r in rows if r['suite'] == suite and r['mutant'] != 'CONTROL']
        killed = sorted(set(r['mutant'] for r in selected if r['outcome'] == 'KILLED'))
        survived = sorted(set(r['mutant'] for r in selected if r['outcome'] == 'SURVIVED'))
        invalid = sorted(set(r['mutant'] for r in selected if r['outcome'] == 'INVALID'))
        count_by_mutant = defaultdict(list)
        for r in selected: count_by_mutant[r['mutant']].append(r['outcome'])
        fully_killed = [m for m in mutant_names if len(count_by_mutant[m]) == len(cpbs) and
                        all(status == 'KILLED' for status in count_by_mutant[m])]
        any_killed = [m for m in mutant_names if 'KILLED' in count_by_mutant[m]]
        by_suite.append(dict(suite=suite, method=selected[0]['method'] if selected else None,
                             killed_any_cpb=len(any_killed), killed_all_cpbs=len(fully_killed),
                             survived_any_cpb=len(survived), invalid_any_cpb=len(invalid),
                             mutation_score_pct=round(100 * len(fully_killed) / len(mutant_names), 2),
                             fully_killed_mutants=fully_killed))
    by_method = {}
    for method in sorted(set(row['method'] for row in by_suite)):
        records = [r for r in by_suite if r['method'] == method]
        by_method[method] = dict(trials=len(records),
                                mean_mutation_score_pct=round(sum(r['mutation_score_pct'] for r in records) / len(records), 2),
                                scores_pct=[r['mutation_score_pct'] for r in records],
                                full_mutant_kill_trials=sum(r['killed_all_cpbs'] == len(mutant_names) for r in records))
    return by_suite, by_method


def report_text(summary):
    lines = [
        '# Phase 4D — UART mutation-based fault-detection evaluation', '',
        '## Experimental design', '',
        '- Mutation testing is performed **only in generated copies of optimized UART TX/RX RTL**.',
        '- Original baseline TX/RX are unchanged, serving as the differential reference.',
        '- The same deterministic 10-scenario test suites are used against each mutant.',
        '- Mutation kill requires successful compilation, normal simulation exit, and a self-checking assertion FAIL.',
        '- Compile failures and simulator timeouts are INVALID mutants, **never** counted as kills.',
        '- Each suite has a clean-RTL control that must pass before any mutation experiment runs.',
        '- Results are fault sensitivity to the particular mutation operators and checker; not formal proof of functional correctness.',
        '- Comparing scenario counts does not equalize simulation cycles, human effort or AI inference cost.',
        '- The fixed testbench contains per-cycle baseline/candidate equivalence assertions; this is a strong oracle,',
        '  so both manual and AI scenarios benefit from the **same** oracle. This must be disclosed in the thesis.',
        '- Mutation score counts a mutant as fully killed only if detected at every selected CPB.',
        '', f"CPBs: {summary['cpbs']}; mutants: {summary['mutant_count']}; suites: {summary['suite_count']}",
        '', '## Mutation score by verification method', '',
        '| Method | Trials | Mean mutation score | All-mutants-killed trials |',
        '|---|---:|---:|---:|',
    ]
    for method, s in summary['method_statistics'].items():
        lines.append(f"| {method} | {s['trials']} | {s['mean_mutation_score_pct']}% | {s['full_mutant_kill_trials']}/{s['trials']} |")
    lines += ['', '## Interpretation and limitations', '',
              'Mutation score is a controlled sensitivity metric for the specified artificial defects.',
              'Undetected mutants may be functionally equivalent, outside the test stimulus, or missed by the oracle.',
              'This study does not compare against untested commercial verification tools or establish AI superiority.',
              'All per-mutant differential patches, testbench sources, compile logs and simulation logs are retained.',
              '', '## Artifacts', '',
              '- `mutation_matrix.csv`: every suite/CPB/mutant result',
              '- `mutation_summary.json`: machine-readable result and provenance',
              '- `mutants/<ID>/mutation.patch`: exact edit for each mutant',
              '- `clean_controls/`: expected passing simulations',
              '- `mutation_runs/`: independent mutant trials',
              '']
    return '\n'.join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--dry-run', action='store_true', help='Validate frozen RTL, scenario sources, and mutation patches without simulating')
    ap.add_argument('--cpbs', nargs='+', type=int, default=[16], help='Choose CPB 8 16 32 64; default screening CPB16')
    ap.add_argument('--timeout', type=int, default=60, help='Per compile/simulation timeout (seconds)')
    args = ap.parse_args()
    if not args.cpbs or len(args.cpbs) != len(set(args.cpbs)) or any(x not in (8, 16, 32, 64) for x in args.cpbs):
        raise RuntimeError('CPBs must be unique and drawn from 8, 16, 32, 64')
    if not 10 <= args.timeout <= 300:
        raise RuntimeError('--timeout must be from 10 to 300 seconds')
    hashes, fresh = preflight()
    suites = load_suites(fresh)
    originals = {n: (RTL / n).read_text(encoding='utf-8') for n in SRC_NAMES}
    patches = materialize_mutants(None, originals)
    print('========== PHASE 4D — UART FAULT INJECTION / MUTATION STUDY ==========', flush=True)
    print('[PASS] Historical 12/12 audit retained; RTL four SHA256 hashes match knowledge model', flush=True)
    print(f'[PASS] Latest Hermes repeatability study: {fresh.name}; loaded 5 fresh AI scenario sets', flush=True)
    print('[PASS] Loaded archived AI, balanced directed, 10 protocol-random and 10 payload-random suites', flush=True)
    print(f'[PASS] Validated {len(patches)} unique fault operators and {len(suites)} ten-scenario suites', flush=True)
    print('CPBs:', args.cpbs, flush=True)
    print('Planned controls:', len(suites) * len(args.cpbs), flush=True)
    print('Planned mutant simulations:', len(patches) * len(suites) * len(args.cpbs), flush=True)
    if args.dry_run:
        print('PHASE 4D PREFLIGHT: PASS (no simulations; no RTL modified)', flush=True)
        return
    if not shutil.which('iverilog') or not shutil.which('vvp'):
        raise RuntimeError('Missing iverilog/vvp in WSL PATH')

    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    out = RESULT_ROOT / f'phase4d_{stamp}'
    out.mkdir(parents=True, exist_ok=False)
    patches = materialize_mutants(out, originals)
    manifests = [{k: v for k, v in m.items() if k != 'new_source'} for m in patches.values()]
    store(out/'mutation_manifest.json', {'rtl_sha256': hashes, 'mutants': manifests,
                                          'fresh_hermes_evidence': str(fresh), 'cpbs': args.cpbs})
    store(out/'suite_manifest.json', [{k:v for k,v in s.items()} for s in suites])
    rows = []
    print('Evidence directory:', out, flush=True)
    print('\n========== CLEAN RTL CONTROLS ==========', flush=True)
    for suite in suites:
        for cpb in args.cpbs:
            result = execute_case(out, suite, cpb, 'CONTROL', None, args.timeout)
            rows.append(result)
            if result['outcome'] != 'SURVIVED':
                store(out/'partial_results.json', rows)
                raise RuntimeError(f'CLEAN RTL CONTROL FAILED: {suite["name"]} CPB {cpb}; see {out / result["logs"]}')
        print(f'[PASS] Control {suite["name"]}: {len(args.cpbs)} CPB configurations', flush=True)
    print(f'[PASS] All {len(suites) * len(args.cpbs)} clean controls', flush=True)

    print('\n========== MUTANT SENSITIVITY EXPERIMENT ==========', flush=True)
    for mutant in MUTANTS:
        folder = out / 'mutants' / mutant['id']
        outcomes = {'KILLED': 0, 'SURVIVED': 0, 'INVALID': 0}
        for suite in suites:
            for cpb in args.cpbs:
                result = execute_case(out, suite, cpb, mutant['id'], folder, args.timeout)
                rows.append(result)
                outcomes[result['outcome']] += 1
        write_csv(out / 'mutation_matrix.csv', rows)
        print(f"{mutant['id']}: killed={outcomes['KILLED']}, survived={outcomes['SURVIVED']}, invalid={outcomes['INVALID']}", flush=True)

    experiment = [r for r in rows if r['mutant'] != 'CONTROL']
    invalid = [r for r in experiment if r['outcome'] == 'INVALID']
    per_suite, per_method = summarise(rows, [s['name'] for s in suites], args.cpbs)
    result = dict(status='PASS' if not invalid else 'PARTIAL_INVALID_MUTANTS',
                  created_utc=datetime.now(timezone.utc).isoformat(),
                  cpbs=args.cpbs, mutant_count=len(MUTANTS), suite_count=len(suites),
                  clean_control_runs=len(suites)*len(args.cpbs),
                  mutated_simulations=len(experiment), invalid_mutant_runs=len(invalid),
                  source_sha256_before=hashes,
                  source_sha256_after={n: sha(RTL / n) for n in SRC_NAMES},
                  source_unchanged=all(sha(RTL / n) == hashes[n] for n in SRC_NAMES),
                  scenario_budget_per_suite=10, method_statistics=per_method, suites=per_suite,
                  mutant_definitions=manifests,
                  notes='Mutation kill requires assertion failure; mutant source is isolated from original RTL.')
    if not result['source_unchanged']:
        result['status'] = 'FAIL_ORIGINAL_SOURCE_CHANGED'
    store(out/'mutation_summary.json', result)
    (out/'PHASE4D_RESEARCH_REPORT.md').write_text(report_text(result), encoding='utf-8')
    print('\n========== PHASE 4D MUTATION SUMMARY ==========', flush=True)
    print('Clean controls:', result['clean_control_runs'], 'PASS', flush=True)
    print('Mutants:', result['mutant_count'], flush=True)
    print('Mutant simulations:', result['mutated_simulations'], flush=True)
    print('Invalid mutant runs:', result['invalid_mutant_runs'], flush=True)
    for method, stats in per_method.items():
        print(f"{method}: n={stats['trials']}, mean mutation score={stats['mean_mutation_score_pct']}%, "
              f"full kills={stats['full_mutant_kill_trials']}/{stats['trials']}", flush=True)
    print('Original RTL unchanged:', result['source_unchanged'], flush=True)
    print('Report:', out / 'PHASE4D_RESEARCH_REPORT.md', flush=True)
    print('PHASE 4D:', result['status'], flush=True)
    if result['status'] != 'PASS':
        raise SystemExit(1)


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, ValueError, OSError, KeyError, json.JSONDecodeError) as error:
        print('[FAIL] PHASE 4D:', error, file=sys.stderr, flush=True)
        sys.exit(1)
