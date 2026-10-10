#!/usr/bin/env python3
"""Phase 4C-1: reproducible UART baseline robustness experiments.

Runs fresh seeds for the legacy payload-only random baseline and a
protocol-aware random baseline; also tests a coverage-balanced directed suite.
Keeps original Hermes response/results and the historical audits untouched.
No live Hermes calls are made by this script.
"""
import argparse
import csv
import hashlib
import json
import random
import shutil
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

WF = Path(__file__).resolve().parents[1]
PROJECT = WF.parent
AI = WF / 'phase_03_ai_verification'
EVAL = WF / 'evaluation'
ROOT = EVAL / 'repeatability'
CPBS = [8, 16, 32, 64]

# Ten known-valid operations covering each defined functional-bin category.
# The coverage-aware random baseline draws WITH REPLACEMENT from these entries.
POOL = [
    ('loopback', 0),
    ('loopback', 255),
    ('loopback', 85),
    ('loopback', 170),
    ('loopback', 129),
    ('loopback', 55),
    ('bad_stop', None),
    ('reset_mid_tx', None),
    ('busy_start', 129),
    ('paired_frames', 17),
]


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def fingerprint(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_case(identifier, kind, value):
    case = {'id': identifier, 'kind': kind}
    if value is not None:
        case['value'] = value
    return case


def balanced_directed():
    return [make_case(f'balanced_{i:02d}', kind, value)
            for i, (kind, value) in enumerate(POOL)]


def protocol_random(seed):
    rng = random.Random(seed)
    return [make_case(f'protocol_random_{i:02d}', *rng.choice(POOL))
            for i in range(10)]


def validate_environment():
    if not shutil.which('iverilog') or not shutil.which('vvp'):
        raise RuntimeError('Both iverilog and vvp are required in your WSL PATH')
    previous = EVAL / 'workflow_status.json'
    reference = AI / 'results' / 'evaluation_summary.json'
    knowledge = WF / 'phase_02_parsing' / 'results' / 'uart_knowledge.json'
    for p in (previous, reference, knowledge):
        if not p.is_file():
            raise RuntimeError(f'Required verified evidence missing: {p}')
    audit = json.loads(previous.read_text(encoding='utf-8'))
    if (audit.get('status'), audit.get('passed'), audit.get('total')) != ('PASS', 12, 12):
        raise RuntimeError('Historical 12/12 phase audit is not PASS')
    base = json.loads(reference.read_text(encoding='utf-8'))
    if base.get('status') != 'PASS' or base.get('ai_generation') != 'HERMES_CHAT_ONESHOT':
        raise RuntimeError('Existing live-AI UART evaluation is not verified PASS')
    for name in ('directed', 'random', 'ai_initial'):
        s = base.get('suites', {}).get(name, {})
        if (s.get('tested_cpbs') != CPBS or s.get('all_pass') is not True
                or s.get('failed_checks') != 0):
            raise RuntimeError(f'Previously verified suite is invalid: {name}')
    know = json.loads(knowledge.read_text(encoding='utf-8'))
    rtl = WF / 'phase_01_rtl' / 'uart'
    source_map = {
        'uart_tx': 'uart_tx.v', 'uart_tx_opt': 'uart_tx_opt.v',
        'uart_rx': 'uart_rx.v', 'uart_rx_opt': 'uart_rx_opt.v'
    }
    hashes = {}
    for key, filename in source_map.items():
        path = rtl / filename
        if not path.is_file():
            raise RuntimeError(f'UART RTL missing: {path}')
        hashes[key] = fingerprint(path)
        expected = know['source_analysis'][key]['sha256']
        if hashes[key] != expected:
            raise RuntimeError(f'Frozen UART RTL changed unexpectedly: {filename}')
    return base, hashes


def summarize_records(suite, scenario_count, seed, results, aggregation):
    return {
        'suite': suite,
        'seed': seed,
        'scenario_budget': scenario_count,
        'cpbs': CPBS,
        'all_pass': aggregation['all_pass'],
        'failed_checks': aggregation['failed_checks'],
        'total_checks': aggregation['checks'],
        'total_cycles': aggregation['cycles'],
        'min_coverage_pct': aggregation['min_coverage_pct'],
        'coverage_by_cpb': {str(r['cpb']): r['coverage'] for r in results},
        'per_cpb': [
            {'cpb': r['cpb'], 'coverage_pct': r['coverage_pct'],
             'checks': r['checks'], 'failed_checks': r['failed'],
             'cycles': r['cycles'], 'wall_seconds': r['wall_seconds']}
            for r in results
        ],
    }


def stats(values):
    return {
        'n': len(values),
        'mean': round(statistics.mean(values), 3),
        'median': round(statistics.median(values), 3),
        'sample_std_dev': round(statistics.stdev(values), 3) if len(values) > 1 else None,
        'min': min(values),
        'max': max(values),
        'full_coverage_trials': sum(v == 100 for v in values),
    }


def report_md(summary):
    lines = [
        '# Phase 4C — UART verification repeatability and stronger baselines',
        '',
        '## Scope and provenance',
        '',
        '- All experiments are simulation-only; frozen UART RTL is unmodified.',
        '- Each run uses exactly 10 initial scenarios and CPB 8,16,32,64.',
        '- The archived Hermes-AI result is **one earlier independent model call**, not a multi-trial distribution.',
        '- Original payload-only random baseline cannot exercise framing, reset, busy or paired-frame operations.',
        '- The protocol-aware random baseline has access to the same five scenario kinds as Hermes and a pool of coverage-targeted payloads.',
        '- The balanced directed baseline explicitly targets the ten known bins, so it is a stronger human-directed comparator.',
        '- Protocol-aware random draws are with replacement and may repeat scenarios.',
        '- Simulation cycle counts and model inference time/cost are not equalized by a ten-scenario budget.',
        '',
        '## Results',
        '',
        '| Suite | Seeds/trials | Mean coverage | Std. dev. | Range | 100% coverage trials |',
        '|---|---:|---:|---:|---:|---:|',
    ]
    for key, title in (
        ('payload_random', 'Payload-only random'),
        ('protocol_random', 'Protocol-aware random'),
        ('balanced_directed', 'Balanced directed')
    ):
        s = summary['statistics'][key]
        sd = 'N/A' if s['sample_std_dev'] is None else str(s['sample_std_dev'])
        lines.append(f"| {title} | {s['n']} | {s['mean']}% | {sd} | {s['min']}–{s['max']}% | {s['full_coverage_trials']}/{s['n']} |")
    ai = summary['archived_ai_reference']
    lines += [
        f"| Original Hermes AI (single call) | 1 | {ai['min_coverage_pct']}% | N/A | N/A | 1/1 |",
        '',
        '## Interpretation limits',
        '',
        'One successful Hermes AI call is insufficient for a claim of statistically superior model performance.',
        'The balanced-directed and protocol-aware random comparisons expose the limitations of the original payload-only baselines.',
        'The ten functional bins are coverage objectives, not formal completeness or discovery of real design faults.',
        'Independent Hermes generations, model/provider identification, inference time/cost, literature review,',
        'negative tests, and clean-environment reproducibility remain separate evidence tasks.',
        '',
        'The full machine-readable simulation evidence and scenario files are under `simulation_runs/`.',
    ]
    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seeds', type=int, default=10,
                        help='Independent PRNG seeds per random suite; 10 recommended')
    args = parser.parse_args()
    if args.seeds < 5 or args.seeds > 50:
        raise ValueError('Choose between 5 and 50 seeds')

    previous, hashes = validate_environment()
    sys.path.insert(0, str(AI))
    import uart_ai_pipeline as pipeline
    from testbench_generator import validate_scenarios

    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    out = ROOT / f'phase4c_{stamp}'
    if out.exists():
        raise RuntimeError(f'Unique experiment folder already exists: {out}')
    out.mkdir(parents=True)
    pipeline.RESULTS = out / 'simulation_runs'  # Do not change original simulation results.
    print('========== PHASE 4C — REPEATABILITY / FAIR BASELINES ==========', flush=True)
    print('Evidence folder:', out, flush=True)
    print('Frozen UART RTL fingerprints:', len(hashes), 'verified', flush=True)
    print('Archived 12/12 audit: PASS; existing Hermes AI results preserved', flush=True)

    seeds = [10007 + i * 104729 for i in range(args.seeds)]
    rows = []

    def run(label, seed, scenarios):
        validate_scenarios({'scenarios': scenarios}, maximum=10)
        if len(scenarios) != 10:
            raise RuntimeError('Experiment must contain exactly ten scenarios')
        name = label if seed is None else f'{label}_{seed}'
        records = pipeline.evaluate(name, scenarios, CPBS)
        agg = pipeline.aggregate(records)
        row = summarize_records(label, len(scenarios), seed, records, agg)
        if not row['all_pass'] or row['failed_checks'] != 0:
            raise RuntimeError(f'Nonpassing independent verification: {name}')
        rows.append(row)
        save_json(out / 'completed_runs.json', rows)
        print(f"[PASS] {name}: {row['min_coverage_pct']}% minimum coverage, "
              f"{row['total_checks']} checks, {row['total_cycles']} cycles", flush=True)

    for seed in seeds:
        run('payload_random', seed, pipeline.randomized(seed))
        run('protocol_random', seed, protocol_random(seed))
    run('balanced_directed', None, balanced_directed())

    groups = {}
    for label in ('payload_random', 'protocol_random', 'balanced_directed'):
        vals = [r['min_coverage_pct'] for r in rows if r['suite'] == label]
        groups[label] = stats(vals)

    ai = previous['suites']['ai_initial']
    result = {
        'status': 'PASS',
        'generated_utc': datetime.now(timezone.utc).isoformat(),
        'scope': 'repeatability_of_non_AI_baselines_and_balanced_directed_reference',
        'frozen_uart_source_sha256': hashes,
        'original_technical_12_gate_audit': 'PASS',
        'random_seeds': seeds,
        'scenario_budget_per_trial': 10,
        'cpb_values': CPBS,
        'statistics': groups,
        'archived_ai_reference': {
            'trial_count': 1,
            'min_coverage_pct': ai['min_coverage_pct'],
            'total_checks': ai['checks'],
            'total_sim_cycles': ai['cycles'],
            'real_hermes_generation': True,
        },
        'fresh_hermes_trials': 0,
        'limitations': [
            'Only one prior AI response; fresh independent model generations pending',
            'Methodologies share test count, not equal total simulation cycles',
            'Defined functional bins are not formal coverage or mutation score',
            'Payload-only random cannot hit error/reset/busy/paired-frame bins',
        ],
        'runs': rows,
    }
    save_json(out / 'phase4c_summary.json', result)
    (out / 'PHASE4C_RESEARCH_REPORT.md').write_text(report_md(result), encoding='utf-8')

    with (out / 'trial_comparison.csv').open('w', newline='', encoding='utf-8') as fh:
        fieldnames = ['suite', 'seed', 'scenario_budget', 'min_coverage_pct',
                      'total_checks', 'failed_checks', 'total_cycles', 'all_pass']
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row[k] for k in fieldnames})
    print('\n========== PHASE 4C REPEATABILITY SUMMARY ==========', flush=True)
    for label, stat in groups.items():
        print(f"{label}: n={stat['n']}, mean={stat['mean']}%, "
              f"range={stat['min']}–{stat['max']}%, "
              f"full-coverage={stat['full_coverage_trials']}/{stat['n']}", flush=True)
    print('Archived AI: 100% on one prior live-Hermes trial; independent AI repeats PENDING')
    print('Report:', out / 'PHASE4C_RESEARCH_REPORT.md')
    print('PHASE 4C-1: PASS')


if __name__ == '__main__':
    try:
        main()
    except (ValueError, RuntimeError, OSError) as exc:
        print('[FAIL] PHASE 4C-1:', exc, file=sys.stderr)
        sys.exit(1)
