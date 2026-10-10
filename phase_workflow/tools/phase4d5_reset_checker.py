#!/usr/bin/env python3
"""Phase 4D-5: Corrected UART reset-cycle assertions (isolated experiment).

This program does NOT alter existing RTL, verified testbench generators, mutation
results, or archived metrics. Instead it imports the exact previously validated
scenario sources, regenerates tests with additional reset-cycle assertions,
and compares a clean candidate with the TX_RESET_BUSY_FAULT mutant (default), or
all 14 original mutants (--scope all).

Commands (inside WSL repository root):
    python3 phase_workflow/tools/phase4d5_reset_checker.py --dry-run
    python3 phase_workflow/tools/phase4d5_reset_checker.py --scope reset --cpbs 8 16 32 64
    python3 phase_workflow/tools/phase4d5_reset_checker.py --scope all --cpbs 8 16 32 64
"""

import argparse
import csv
import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

WORKFLOW = Path(__file__).resolve().parents[1]
TOOLS = WORKFLOW / 'tools'
AI = WORKFLOW / 'phase_03_ai_verification'
RTL = WORKFLOW / 'phase_01_rtl' / 'uart'
OUTROOT = WORKFLOW / 'evaluation' / 'fault_injection'
MUTATION_SCRIPT = TOOLS / 'phase4d_mutation_test.py'

# The original checker already compares TX/RX on non-reset cycles. We add
# checks only on reset cycles, retaining the original measurement semantics.
RESET_ASSERTIONS = '''        if (rst) begin
            assert_true({tx_ref,busy_ref,done_ref} ===
                        {tx_opt,busy_tx_opt,done_tx_opt},
                        "TX reset-cycle equivalence");
            assert_true({received_ref,valid_ref,busy_rx_ref,error_ref} ===
                        {received_opt,valid_opt,busy_rx_opt,error_opt},
                        "RX reset-cycle equivalence");
            assert_true(tx_ref === 1'b1 && busy_ref === 1'b0 &&
                        done_ref === 1'b0,
                        "Reference TX reset outputs");
            assert_true(tx_opt === 1'b1 && busy_tx_opt === 1'b0 &&
                        done_tx_opt === 1'b0,
                        "Candidate TX reset outputs");
        end
'''
MARKER = '        cycles = cycles + 1;\n        if (!rst) begin'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_json(path, data):
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def build_fixed_tb(text):
    if text.count(MARKER) != 1:
        raise RuntimeError('Original generated TB reset assertion anchor missing/changed')
    result = text.replace(MARKER, '        cycles = cycles + 1;\n' + RESET_ASSERTIONS + '        if (!rst) begin', 1)
    if result.count('TX reset-cycle equivalence') != 1:
        raise RuntimeError('Reset assertion was not injected exactly once')
    return result


def load_module():
    if not MUTATION_SCRIPT.is_file():
        raise RuntimeError(f'Phase 4D mutation script missing: {MUTATION_SCRIPT}')
    spec = importlib.util.spec_from_file_location('phase4d_reference', MUTATION_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_sim(out, suite, cpb, mutation, originals, mutant_folders, generator, reference, timeout):
    tag = mutation['id'] if mutation else 'CONTROL'
    dest = out / 'runs' / suite['name'] / f'cpb{cpb}' / tag
    dest.mkdir(parents=True, exist_ok=False)
    tb_text = build_fixed_tb(generator.make_tb(suite['scenarios'], cpb))
    tb = dest / 'tb_uart_phase.v'
    tb.write_text(tb_text, encoding='utf-8')
    exe = dest / 'sim.out'
    folder = mutant_folders[mutation['id']] if mutation else None
    cmd = ['iverilog', '-g2012', '-s', 'tb_uart_phase', '-o', str(exe), str(tb)]
    cmd += [str((folder / x) if folder else (RTL / x)) for x in reference.SRC_NAMES]
    result = dict(suite=suite['name'], method=suite['method'], cpb=cpb,
                  mutant=tag, outcome='INVALID', checks=None, failed_checks=None,
                  cycles=None, log_folder=dest.relative_to(out).as_posix(),
                  reason='not executed')
    try:
        compiled = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        (dest / 'compile.log').write_text(compiled.stdout + '\n' + compiled.stderr, encoding='utf-8')
        if compiled.returncode != 0:
            result['reason'] = f'iverilog exit={compiled.returncode}'
            return result
        ran = subprocess.run(['vvp', str(exe)], capture_output=True, text=True, timeout=timeout)
        (dest / 'simulation.log').write_text(ran.stdout + '\n' + ran.stderr, encoding='utf-8')
        result['outcome'], result['checks'], result['failed_checks'], result['cycles'] = reference.parse_sim(
            ran.stdout, ran.stderr, ran.returncode)
        result['reason'] = f'vvp exit={ran.returncode}'
    except subprocess.TimeoutExpired:
        result['reason'] = f'timed out after {timeout}s'
        (dest / 'timeout.log').write_text(result['reason'] + '\n')
    return result


def old_reset_counts():
    # Optional, informational only: original scores are never changed.
    candidates = sorted(p for p in OUTROOT.glob('phase4d_*') if p.is_dir() and (p / 'mutation_matrix.csv').exists())
    if not candidates:
        return None
    original = candidates[-1]
    with (original / 'mutation_matrix.csv').open(newline='', encoding='utf-8') as f:
        rows = [r for r in csv.DictReader(f) if r['mutant'] == 'TX_RESET_BUSY_FAULT']
    if not rows:
        return None
    d = defaultdict(lambda: defaultdict(int))
    for r in rows:
        d[r['method']][r['outcome']] += 1
    return original, {k: dict(v) for k, v in d.items()}


def write_table(path, rows):
    columns = ['suite', 'method', 'cpb', 'mutant', 'outcome', 'checks', 'failed_checks', 'cycles', 'log_folder', 'reason']
    with path.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=columns)
        w.writeheader()
        w.writerows(rows)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--dry-run', action='store_true')
    p.add_argument('--scope', choices=('reset', 'all'), default='reset', help='Default: reset mutant only; all: 14 mutants')
    p.add_argument('--cpbs', nargs='+', type=int, default=[8, 16, 32, 64])
    p.add_argument('--timeout', type=int, default=60)
    args = p.parse_args()
    if len(set(args.cpbs)) != len(args.cpbs) or not args.cpbs or any(c not in (8,16,32,64) for c in args.cpbs):
        raise SystemExit('[FAIL] CPB list must contain unique values from 8,16,32,64')
    if not 10 <= args.timeout <= 300:
        raise SystemExit('[FAIL] --timeout must be between 10 and 300 seconds')

    reference = load_module()
    hashes, fresh = reference.preflight()
    suites = reference.load_suites(fresh)
    sys.path.insert(0, str(AI))
    import testbench_generator as generator
    originals = {n: (RTL / n).read_text(encoding='utf-8') for n in reference.SRC_NAMES}
    mutants = [m for m in reference.MUTANTS if args.scope == 'all' or m['id'] == 'TX_RESET_BUSY_FAULT']
    if not mutants:
        raise RuntimeError('Reset mutant definition not found')
    for mutation in mutants:
        if originals[mutation['file']].count(mutation['old']) != 1:
            raise RuntimeError(f"Fault operator invalid: {mutation['id']}")
    example = generator.make_tb(suites[0]['scenarios'], args.cpbs[0])
    changed = build_fixed_tb(example)
    if changed == example:
        raise RuntimeError('Reset assertion injection unsuccessful')
    print('========== PHASE 4D-5 — CORRECTED RESET CHECKER ==========', flush=True)
    print('[PASS] Historical 12/12 audit and original UART RTL fingerprints validated', flush=True)
    print('[PASS] Original testbench generation and mutation sources loaded', flush=True)
    print('[PASS] Reset-cycle differential assertions inserted in NEW testbench copies', flush=True)
    print(f'Suites: {len(suites)}, CPBs: {args.cpbs}, mutants: {len(mutants)}', flush=True)
    print(f'Planned clean controls: {len(suites)*len(args.cpbs)}', flush=True)
    print(f'Planned mutant simulations: {len(suites)*len(args.cpbs)*len(mutants)}', flush=True)
    if args.dry_run:
        print('PHASE 4D-5 PREFLIGHT: PASS (no simulations, no original files changed)', flush=True)
        return 0
    if not shutil.which('iverilog') or not shutil.which('vvp'):
        raise RuntimeError('iverilog and vvp must be installed in WSL')

    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    out = OUTROOT / f'phase4d5_reset_checker_{stamp}'
    out.mkdir(parents=True, exist_ok=False)
    mutations_materialized = reference.materialize_mutants(out, originals)
    mutant_folders = {m['id']: out / 'mutants' / m['id'] for m in mutants}
    save_json(out/'study_manifest.json', dict(checked_original_sha256=hashes, scope=args.scope, cpbs=args.cpbs,
        suites=[dict(name=s['name'], method=s['method'], provenance=s['provenance'], scenarios=s['scenarios']) for s in suites],
        mutants=[m['id'] for m in mutants], modified_testbench_only=True,
        reference_mutation_script=str(MUTATION_SCRIPT), old_scores_unchanged=True))
    (out / 'patched_tb_example.v').write_text(changed, encoding='utf-8')
    print('New independent evidence folder:', out, flush=True)
    rows = []
    print('\n========== CLEAN CONTROLS WITH NEW ASSERTIONS ==========', flush=True)
    for suite in suites:
        for cpb in args.cpbs:
            res = run_sim(out, suite, cpb, None, originals, mutant_folders, generator, reference, args.timeout)
            rows.append(res)
            if res['outcome'] != 'SURVIVED':
                write_table(out/'partial_results.csv', rows)
                raise RuntimeError(f"Clean control failed: {suite['name']} CPB{cpb}; check {out/res['log_folder']}")
        print(f"[PASS] {suite['name']} clean control: {len(args.cpbs)} CPB settings", flush=True)

    print('\n========== MUTANT DETECTION WITH NEW ASSERTIONS ==========', flush=True)
    for mutation in mutants:
        totals = defaultdict(int)
        for suite in suites:
            for cpb in args.cpbs:
                res = run_sim(out, suite, cpb, mutation, originals, mutant_folders, generator, reference, args.timeout)
                rows.append(res)
                totals[res['outcome']] += 1
        write_table(out/'results_matrix.csv', rows)
        print(f"{mutation['id']}: killed={totals['KILLED']}, survived={totals['SURVIVED']}, invalid={totals['INVALID']}", flush=True)

    for name, digest in hashes.items():
        if sha(RTL / name) != digest:
            raise RuntimeError(f'Frozen RTL changed unexpectedly: {name}')
    summary = defaultdict(lambda: defaultdict(int))
    per_suite_mutant = defaultdict(dict)
    for row in rows:
        if row['mutant'] != 'CONTROL':
            summary[row['method']][row['outcome']] += 1
            per_suite_mutant[(row['suite'],row['mutant'])][row['cpb']] = row['outcome']
    total_invalid = sum(v.get('INVALID',0) for v in summary.values())
    scores = defaultdict(list)
    by_name = {s['name']:s['method'] for s in suites}
    for suite in suites:
        n = sum(all(per_suite_mutant[(suite['name'], m['id'])].get(c) == 'KILLED' for c in args.cpbs) for m in mutants)
        scores[suite['method']].append(round(100 * n / len(mutants), 2))

    prior = old_reset_counts()
    report = {
        'status': 'PASS' if total_invalid == 0 else 'PARTIAL_INVALID',
        'checks': dict(clean_controls=len(suites)*len(args.cpbs), mutant_simulations=len(suites)*len(args.cpbs)*len(mutants), invalid=total_invalid),
        'method_counts': {k: dict(v) for k,v in summary.items()},
        'method_score_pct': {method: dict(trials=len(s), mean=round(sum(s)/len(s),2), scores=s) for method,s in scores.items()},
        'original_rtl_unchanged': True,
        'old_experiment_unchanged': True,
        'old_reset_mutant_summary': dict(path=str(prior[0]), by_method=prior[1]) if prior else None,
        'note': 'Same scenarios, extended oracle. Changes in score are caused by stronger assertions, not additional AI test generation.',
    }
    save_json(out/'corrected_checker_summary.json', report)
    print('\n========== PHASE 4D-5 SUMMARY ==========', flush=True)
    print('Original RTL unchanged: True', flush=True)
    print('Old mutation results preserved: True', flush=True)
    print('Invalid mutant simulations:', total_invalid, flush=True)
    for method,s in sorted(report['method_score_pct'].items()):
        print(f"{method}: n={s['trials']}, mean corrected-oracle mutant score={s['mean']}%", flush=True)
    if prior:
        print('Original reset fault outcomes:', prior[1], flush=True)
    print('Independent report:', out/'corrected_checker_summary.json', flush=True)
    print('PHASE 4D-5:', report['status'], flush=True)
    return 0 if total_invalid == 0 else 1


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (RuntimeError, ValueError, OSError) as exc:
        print('[FAIL] Phase 4D-5:', str(exc), file=sys.stderr)
        sys.exit(1)
