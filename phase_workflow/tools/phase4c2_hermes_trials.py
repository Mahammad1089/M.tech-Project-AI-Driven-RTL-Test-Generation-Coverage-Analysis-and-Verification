#!/usr/bin/env python3
"""Phase 4C-2: fresh Hermes UART scenario trials, isolated from passed evidence.

Each trial makes a NEW Hermes one-shot model call with the same fixed prompt,
validates exactly ten whitelisted scenarios, and simulates CPB 8/16/32/64.
A trial failing generation, validation or simulation remains a failure in the
report; it is never silently repaired or counted as successful.

Run from the project root after Phase 4C-1; see --help.
"""
import argparse
import csv
import hashlib
import importlib.util
import json
import shutil
import statistics
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

WF = Path(__file__).resolve().parents[1]
PROJECT = WF.parent
AI = WF / 'phase_03_ai_verification'
EVAL = WF / 'evaluation'
PARSED = WF / 'phase_02_parsing' / 'results' / 'uart_knowledge.json'
REFERENCE = AI / 'results' / 'evaluation_summary.json'
HERMES = AI / 'hermes_bridge.py'
PROMPT = AI / 'results' / 'hermes' / 'initial_prompt.txt'
CPBS = [8, 16, 32, 64]
SOURCES = {'uart_tx':'uart_tx.v', 'uart_tx_opt':'uart_tx_opt.v',
           'uart_rx':'uart_rx.v', 'uart_rx_opt':'uart_rx_opt.v'}


def save_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, default=str) + '\n', encoding='utf-8')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_prerequisites():
    for prog in ('hermes', 'iverilog', 'vvp'):
        if shutil.which(prog) is None:
            raise RuntimeError(f'Required program not found in PATH: {prog}')
    for p in (PARSED, REFERENCE, HERMES, PROMPT, EVAL / 'workflow_status.json'):
        if not p.is_file() or p.stat().st_size == 0:
            raise RuntimeError(f'Required existing evidence missing: {p}')
    audit = json.loads((EVAL / 'workflow_status.json').read_text(encoding='utf-8'))
    if (audit.get('status'), audit.get('passed'), audit.get('total')) != ('PASS', 12, 12):
        raise RuntimeError('Original 12/12 workflow audit must remain PASS')
    baseline = json.loads(REFERENCE.read_text(encoding='utf-8'))
    if baseline.get('status') != 'PASS' or baseline.get('ai_generation') != 'HERMES_CHAT_ONESHOT':
        raise RuntimeError('Original live Hermes AI result is not verified PASS')
    if baseline.get('suites', {}).get('ai_initial', {}).get('min_coverage_pct') != 100.0:
        raise RuntimeError('Original Hermes reference no longer shows 100% coverage')
    knowledge = json.loads(PARSED.read_text(encoding='utf-8'))
    hashes = {}
    for key, name in SOURCES.items():
        p = WF / 'phase_01_rtl' / 'uart' / name
        if not p.is_file():
            raise RuntimeError(f'Frozen RTL source missing: {p}')
        actual = sha(p)
        expected = knowledge['source_analysis'][key]['sha256']
        if actual != expected:
            raise RuntimeError(f'Frozen RTL source hash differs from parser evidence: {name}')
        hashes[key] = actual
    if 'Generate exactly 10 scenarios' not in PROMPT.read_text(encoding='utf-8'):
        raise RuntimeError('The fixed original prompt has unexpectedly changed')
    return baseline, hashes


def load_bridge():
    spec = importlib.util.spec_from_file_location('phase4c2_hermes_bridge', HERMES)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not callable(getattr(module, 'run_hermes', None)):
        raise RuntimeError('Hermes bridge does not expose run_hermes')
    return module


def stats(values):
    if not values:
        return {'n': 0, 'mean': None, 'median': None, 'std_dev_sample': None,
                'range': None, 'full_coverage_trials': 0}
    return {'n': len(values),
            'mean': round(statistics.mean(values), 3),
            'median': round(statistics.median(values), 3),
            'std_dev_sample': round(statistics.stdev(values), 3) if len(values) > 1 else None,
            'range': [min(values), max(values)],
            'full_coverage_trials': sum(x == 100.0 for x in values)}


def markdown_report(data):
    lines = [
        '# Phase 4C-2 — Independent Hermes UART generation trials', '',
        '## Protocol', '',
        '- Every trial starts a fresh Hermes one-shot call with the **same frozen prompt**.',
        '- Exactly ten JSON scenarios are required and checked by the project whitelist validator.',
        '- Each accepted set is independently simulated with Icarus at CPB 8, 16, 32, and 64.',
        '- Frozen UART RTL source hashes are checked; original reports, scenarios and audits are not overwritten.',
        '- Failed Hermes calls, invalid scenarios or failed simulations count as **unsuccessful trials**, not discarded samples.',
        '- Same scenario budget does not equalize simulation cycles, model latency, inference cost or human engineering effort.',
        '', '## Results', '',
        '| Trial | Hermes | Valid 10 | Simulation | Min coverage | Checks | Cycles | Hermes elapsed (s) |',
        '|---|---|---|---|---:|---:|---:|---:|',
    ]
    for r in data['trials']:
        s = ('N/A' if r.get('min_coverage_pct') is None else str(r['min_coverage_pct']) + '%')
        lines.append(f"| {r['trial']:02d} | {r.get('hermes_status','not run')} | "
                     f"{r.get('scenario_validation','not run')} | {r.get('simulation_status','not run')} | "
                     f"{s} | {r.get('checks','N/A')} | {r.get('cycles','N/A')} | "
                     f"{r.get('hermes_wall_seconds','N/A')} |")
    s = data['statistics']
    lines += ['', '## Statistics and interpretation', '',
              f"- Planned Hermes trials: **{data['planned_trials']}**",
              f"- Complete passing trials: **{data['passed_trials']}**",
              f"- Failed/incomplete trials: **{data['failed_trials']}**",
              f"- Mean coverage among successful simulations only: **{s['mean']}%** (n={s['n']}).",
              f"- Complete 10/10 functional-bin coverage: **{s['full_coverage_trials']}** successful trial(s).",
              '- Invalid/malformed model outputs are excluded from the coverage mean but INCLUDED in failure counts.',
              '- The archived initial Hermes AI result of 100% is a separate earlier trial and is not counted again.',
              '- Protocol-aware random mean (ten seeds) was 69%; balanced directed attained 100% in one trial.',
              '- A 100% functional-bin score is not mutation coverage, formal completeness or proof of zero RTL defects.',
              '- Calling the same model repeatedly does not ensure statistically independent samples if the provider is deterministic.',
              '- Record the model/provider and costs manually if known; this script does not expose API configuration.',
              '', f"Overall execution status: **{data['status']}**", '',
              '## Research follow-ups', '',
              '- Negative/mutation testing to quantify actual fault detection.',
              '- Compare with stronger directed strategies, and account for simulation cycles and model usage.',
              '- Literature-based prior-art and novelty study; final submission reproduction.', '']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--trials', type=int, default=5, help='Number of fresh Hermes calls (1..20), default 5')
    parser.add_argument('--timeout', type=int, default=300, help='Per-model-call timeout seconds')
    parser.add_argument('--dry-run', action='store_true', help='Only validate inputs; no model calls or simulations')
    args = parser.parse_args()
    if not 1 <= args.trials <= 20:
        raise ValueError('--trials must be from 1 to 20')
    if not 30 <= args.timeout <= 900:
        raise ValueError('--timeout must be from 30 to 900 seconds')

    baseline, hashes = check_prerequisites()
    sys.path.insert(0, str(AI))
    import uart_ai_pipeline as pipeline
    from testbench_generator import validate_scenarios
    bridge = load_bridge()

    print('========== PHASE 4C-2 — FRESH HERMES TRIALS ==========', flush=True)
    print('[PASS] Historical 12/12 audit unchanged', flush=True)
    print('[PASS] 4 UART RTL SHA-256 fingerprints unchanged', flush=True)
    print('[PASS] Existing 100% AI reference preserved', flush=True)
    print('Planned new AI calls:', args.trials, flush=True)
    print('Estimated new Icarus simulations:', args.trials * 4, flush=True)
    print('AI provider usage may be billed; no extra feedback requests are made.', flush=True)
    if args.dry_run:
        print('PHASE 4C-2 PREFLIGHT: PASS (no Hermes calls made)', flush=True)
        return

    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    out = EVAL / 'repeatability' / 'hermes_trials' / f'phase4c2_{stamp}'
    out.mkdir(parents=True, exist_ok=False)
    pipeline.RESULTS = out / 'simulations'  # IMPORTANT: isolate new results from original Phase 3.
    fixed_prompt = PROMPT.read_text(encoding='utf-8')
    rows = []
    print('Evidence directory:', out, flush=True)
    for i in range(1, args.trials + 1):
        label = f'ai_fresh_{i:02d}'
        trial_dir = out / 'calls' / label
        trial_dir.mkdir(parents=True)
        prompt_file = trial_dir / 'uart_prompt.txt'
        prompt_file.write_text(fixed_prompt, encoding='utf-8')
        row = {'trial': i, 'call_label': label,
               'prompt_sha256': sha(prompt_file),
               'scenario_budget': 10, 'cpbs': CPBS,
               'hermes_status': 'not run', 'scenario_validation': 'not run',
               'simulation_status': 'not run', 'min_coverage_pct': None}
        print(f'\n========== HERMES FRESH TRIAL {i}/{args.trials} ==========', flush=True)
        try:
            before = time.monotonic()
            response = bridge.run_hermes(str(prompt_file), timeout_seconds=args.timeout)
            row['hermes_wall_seconds'] = round(time.monotonic() - before, 3)
            row['hermes_status'] = response.get('status', 'UNKNOWN')
            row['hermes_exit_code'] = response.get('hermes_exit_code')
            row['event_count'] = response.get('event_count')
            row['session_id'] = response.get('session_id')
            save_json(trial_dir / 'hermes_response_raw.json', response)
            if response.get('status') != 'PASS':
                raise RuntimeError('Hermes call unsuccessful: ' + str(response.get('error') or response.get('response_text', '')[:250]))
            scenarios = pipeline.parse_hermes_response(response, require_count=10)
            scenarios = validate_scenarios({'scenarios': scenarios}, maximum=10)
            row['scenario_validation'] = 'PASS'
            row['scenario_signature_sha256'] = hashlib.sha256(
                json.dumps([{'kind': q['kind'], 'value': q.get('value')} for q in scenarios],
                           sort_keys=True).encode('utf-8')).hexdigest()
            save_json(trial_dir / 'validated_scenarios.json', {'scenarios': scenarios, 'source':'LIVE_HERMES_NEW_ONESHOT'})
            records = pipeline.evaluate(label, scenarios, CPBS)
            ag = pipeline.aggregate(records)
            row.update({'simulation_status': 'PASS' if ag['all_pass'] and ag['failed_checks'] == 0 else 'FAIL',
                        'min_coverage_pct': ag['min_coverage_pct'],
                        'checks': ag['checks'], 'failed_checks': ag['failed_checks'],
                        'cycles': ag['cycles'], 'simulation_seconds': ag['seconds'],
                        'per_cpb': records})
            if row['simulation_status'] != 'PASS':
                raise RuntimeError('Icarus simulation failed on at least one CPB')
            print(f"[PASS] Trial {i}: {ag['min_coverage_pct']}% coverage, "
                  f"{ag['checks']} checks, 0 failures, {ag['cycles']} cycles", flush=True)
        except (ValueError, RuntimeError, OSError, subprocess.TimeoutExpired) as error:
            row['error'] = f'{type(error).__name__}: {str(error)[:500]}'
            print(f'[FAIL] Trial {i}: {row["error"]}', flush=True)
            # Save the failed trial and continue, so failure rate is not understated.
        rows.append(row)
        save_json(out / 'trial_log.json', rows)

    passed = [r for r in rows if r.get('hermes_status') == 'PASS' and
              r.get('scenario_validation') == 'PASS' and r.get('simulation_status') == 'PASS']
    values = [r['min_coverage_pct'] for r in passed]
    stats_out = stats(values)
    signatures = [r.get('scenario_signature_sha256') for r in rows if r.get('scenario_signature_sha256')]
    distinct = len(set(signatures))
    data = {'status': 'PASS' if len(passed) == args.trials else 'PARTIAL_FAILURE',
            'generated_utc': datetime.now(timezone.utc).isoformat(),
            'planned_trials': args.trials, 'passed_trials': len(passed),
            'failed_trials': args.trials - len(passed),
            'protocol': 'fresh one-shot calls, fixed initial UART prompt, 10 scenarios each, CPB 8/16/32/64',
            'frozen_uart_source_sha256': hashes, 'fixed_prompt_sha256': sha(PROMPT),
            'original_12_gate_audit': 'PASS',
            'archived_ai_reference_coverage_pct': baseline['suites']['ai_initial']['min_coverage_pct'],
            'statistics': stats_out, 'distinct_valid_scenario_signatures': distinct,
            'validated_scenario_trials': len(signatures),
            'note': 'Distinct calls are not necessarily statistically independent; provider/model and generation temperature not controlled.',
            'trials': rows}
    save_json(out / 'phase4c2_summary.json', data)
    (out / 'PHASE4C2_RESEARCH_REPORT.md').write_text(markdown_report(data), encoding='utf-8')
    with (out / 'trial_comparison.csv').open('w', newline='', encoding='utf-8') as f:
        fields = ['trial', 'hermes_status', 'scenario_validation', 'simulation_status',
                  'min_coverage_pct', 'checks', 'failed_checks', 'cycles',
                  'hermes_wall_seconds', 'scenario_signature_sha256', 'error']
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k) for k in fields})

    print('\n========== PHASE 4C-2 HERMES REPEATABILITY SUMMARY ==========', flush=True)
    print(f'Live Hermes attempts: {args.trials}', flush=True)
    print(f'Valid and passing trials: {len(passed)}', flush=True)
    print(f'Failed / rejected trials: {args.trials - len(passed)}', flush=True)
    print(f'Distinct valid scenario sequences: {distinct}/{len(signatures)}', flush=True)
    print(f'Mean coverage (only passing trials): {stats_out["mean"]}%', flush=True)
    print(f'Coverage range: {stats_out["range"]}', flush=True)
    print(f'Full coverage: {stats_out["full_coverage_trials"]}/{len(passed)} passing trials', flush=True)
    print('Original AI experiment: 100% in 1 separate archived trial', flush=True)
    print('Report:', out / 'PHASE4C2_RESEARCH_REPORT.md', flush=True)
    print('PHASE 4C-2:', data['status'], flush=True)
    if data['status'] != 'PASS':
        raise SystemExit(1)


if __name__ == '__main__':
    try:
        main()
    except (ValueError, RuntimeError, OSError, KeyError, json.JSONDecodeError) as exc:
        print('[FAIL] Phase 4C-2:', exc, file=sys.stderr)
        sys.exit(1)
