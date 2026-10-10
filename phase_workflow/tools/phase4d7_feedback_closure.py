#!/usr/bin/env python3
"""Phase 4D-7: single-gap LIVE Hermes closure for the archived Trial 5.

This script NEVER changes previously verified RTL, Phase 3 artifacts or
Phase 4C-2 trial evidence. It makes ONE real Hermes call (unless --dry-run),
requires one valid loopback(129) suggestion for edge_81, and independently
replays: original Trial 5 (10 tests), AI-extended (11 tests), and matched
human-directed extension (11 tests), at CPB 8/16/32/64.

Research caveat: The model prompt discloses the exact missing bin and the
known deterministic stimulus mapping. The additional AI-generated test is
therefore equivalent to a rule-based directed test, not proof of AI superiority.
"""
import argparse
import hashlib
import importlib.util
import json
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

WF = Path(__file__).resolve().parents[1]
AI = WF / 'phase_03_ai_verification'
EVAL = WF / 'evaluation'
RTL = WF / 'phase_01_rtl' / 'uart'
KNOWLEDGE = WF / 'phase_02_parsing' / 'results' / 'uart_knowledge.json'
AUDIT = EVAL / 'workflow_status.json'
BRIDGE = AI / 'hermes_bridge.py'
TRIALS_ROOT = EVAL / 'repeatability' / 'hermes_trials'
DEST_ROOT = EVAL / 'feedback_closure'
CPBS = (8, 16, 32, 64)
BIN = 'edge_81'
RTL_SOURCES = {'uart_tx':'uart_tx.v','uart_tx_opt':'uart_tx_opt.v',
               'uart_rx':'uart_rx.v','uart_rx_opt':'uart_rx_opt.v'}


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True, default=str) + '\n', encoding='utf-8')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def expect(condition, message):
    if not condition:
        raise RuntimeError(message)


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    expect(spec is not None and spec.loader is not None, f'Cannot load {path}')
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


def get_inputs():
    for name in ('hermes', 'iverilog', 'vvp'):
        expect(shutil.which(name), f'Missing executable: {name}')
    for path in (AUDIT, KNOWLEDGE, BRIDGE):
        expect(path.is_file(), f'Missing evidence file: {path}')
    audit = read_json(AUDIT)
    expect((audit.get('status'),audit.get('passed'),audit.get('total')) == ('PASS',12,12),
           'Original workflow audit is not PASS 12/12')
    knowledge = read_json(KNOWLEDGE)
    hashes = {}
    for key, name in RTL_SOURCES.items():
        path = RTL / name
        expect(path.is_file(), f'Missing frozen UART RTL: {path}')
        actual = sha(path)
        expect(actual == knowledge['source_analysis'][key]['sha256'],
               f'RTL hash mismatch: {path}')
        hashes[name] = actual
    folders = sorted(TRIALS_ROOT.glob('phase4c2_*'), reverse=True)
    expect(bool(folders), 'No Phase 4C-2 repeatability experiment found')
    trial_root = None
    trial = None
    for folder in folders:
        summary_path = folder / 'phase4c2_summary.json'
        if not summary_path.is_file():
            continue
        summary = read_json(summary_path)
        entries = [r for r in summary.get('trials', []) if r.get('trial') == 5]
        if entries and entries[0].get('simulation_status') == 'PASS':
            trial_root, trial = folder, entries[0]
            break
    expect(trial is not None, 'Trial 5 PASS evidence not found in Phase 4C-2')
    expect(trial.get('min_coverage_pct') == 90.0, 'Expected Trial 5 at 90%')
    per_cpb = trial.get('per_cpb', [])
    expect(len(per_cpb) == 4, 'Trial 5 must include four CPB result records')
    by_cpb = {r.get('cpb'):r for r in per_cpb}
    expect(set(by_cpb) == set(CPBS), 'Trial 5 CPB records incomplete')
    for cpb in CPBS:
        record = by_cpb[cpb]
        expect(record.get('status') == 'PASS' and record.get('failed') == 0,
               f'Trial 5 recorded failure at CPB {cpb}')
        coverage = record.get('coverage', {})
        missing = sorted(k for k,v in coverage.items() if v == 0)
        expect(missing == [BIN],
               f'Expected only edge_81 missing at CPB {cpb}, found {missing}')
    scenarios_path = trial_root / 'calls' / 'ai_fresh_05' / 'validated_scenarios.json'
    expect(scenarios_path.is_file(), f'Missing trial scenario evidence: {scenarios_path}')
    sys.path.insert(0, str(AI))
    from testbench_generator import validate_scenarios, BINS
    expect(BIN in BINS, 'Required coverage bin no longer defined')
    scenarios = validate_scenarios(read_json(scenarios_path), maximum=10)
    expect(len(scenarios) == 10, 'Expected exactly 10 original Trial 5 scenarios')
    expect(not any(s['kind']=='loopback' and s.get('value')==129 for s in scenarios),
           'Trial 5 already contains loopback(129); investigate inconsistent coverage')
    return trial_root, trial, scenarios, hashes, scenarios_path


def feedback_prompt(prior):
    # Deliberately explicit: measures feedback integration, not independent AI discovery.
    prior_without_ids = [{'kind':s['kind'], **({'value':s['value']} if 'value' in s else {})}
                         for s in prior]
    return (
        'You are generating one safe, structured UART verification scenario.\n'
        'Return ONLY a JSON object, no Markdown, in exactly this shape:\n'
        '{"scenarios":[{"id":"unique_identifier","kind":"allowed_kind","value":0}]}\n'
        'The project has 10 predefined functional coverage bins. A verified previous\n'
        'trial hit 9/10 bins and missed only edge_81 in CPB 8, 16, 32, and 64.\n'
        'The deterministic testbench credits edge_81 ONLY when loopback transmits\n'
        'byte 0x81 (decimal 129) and its self-checking receive oracle passes.\n'
        'Allowed kinds are loopback, bad_stop, reset_mid_tx, busy_start, paired_frames.\n'
        'Generate EXACTLY ONE scenario that satisfies the missing bin.\n'
        'Use a unique simple alphanumeric underscore id not present in the list.\n'
        'Do not return code, commands, explanations or additional scenarios.\n'
        f'Previously tested scenario IDs: {[s["id"] for s in prior]}\n'
        f'Previously tested scenario operations: {json.dumps(prior_without_ids)}\n'
    )


def valid_feedback(response, original, pipeline):
    new = pipeline.parse_hermes_response(response, require_count=1)
    item = new[0]
    expect(item['kind'] == 'loopback' and item.get('value') == 129,
           'Live model suggestion does NOT hit missing edge_81 (need loopback value 129)')
    expect(item['id'] not in {s['id'] for s in original},
           'Live model reused a Trial 5 scenario ID')
    expect(not any(x['kind']=='loopback' and x.get('value')==129 for x in original),
           'Duplicate semantic coverage scenario')
    return item


def aggregate(pipeline, label, scenarios, where):
    pipeline.RESULTS = where / 'simulations'
    print(f'\n========== {label.upper()} (SCENARIOS={len(scenarios)}) ==========', flush=True)
    records = pipeline.evaluate(label, scenarios, list(CPBS))
    summary = pipeline.aggregate(records)
    expect(summary['all_pass'] and summary['failed_checks']==0,
           f'Self-checking simulation failed in {label}')
    return summary, records


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--dry-run', action='store_true', help='Only check evidence and schema; no model calls/simulations')
    ap.add_argument('--timeout', type=int, default=300, help='Hermes timeout, 30..900 seconds')
    args = ap.parse_args()
    expect(30 <= args.timeout <= 900, 'Timeout must be in range 30..900')
    trial_root, trial, original, hashes, original_path = get_inputs()
    print('========== PHASE 4D-7: TARGETED EDGE_81 FEEDBACK ==========', flush=True)
    print('[PASS] Historical workflow audit 12/12', flush=True)
    print('[PASS] All four frozen UART RTL hashes', flush=True)
    print('[PASS] Trial 5: 10 scenarios; missing ONLY edge_81 at all CPBs', flush=True)
    print('Source experiment:', trial_root, flush=True)
    print('Trial 5 evidence:', original_path, flush=True)
    print('Planned LIVE Hermes calls: 1 (unless dry-run)', flush=True)
    print('Planned new Icarus simulations: 12 (three scenario sets x four CPBs)', flush=True)
    print('Note: feedback prompt explicitly provides mapping 0x81 => loopback(129)', flush=True)
    if args.dry_run:
        print('PHASE 4D-7 PREFLIGHT: PASS (no model calls; no simulations)', flush=True)
        return
    sys.path.insert(0,str(AI))
    import uart_ai_pipeline as pipeline
    bridge = load_module(BRIDGE, 'phase4d7_bridge')
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    out = DEST_ROOT / f'phase4d7_{stamp}'
    out.mkdir(parents=True,exist_ok=False)
    evidence = {
        'stage':'Phase 4D-7', 'created_utc':datetime.now(timezone.utc).isoformat(),
        'status':'IN_PROGRESS', 'source_trial5':str(trial_root),
        'source_scenarios_sha256':sha(original_path),
        'source_scenario_count':len(original), 'source_min_coverage_pct':trial['min_coverage_pct'],
        'source_missing_bins':[BIN], 'frozen_uart_sha256':hashes,
        'hermes_calls':0, 'additional_ai_scenarios':0,
        'research_limitations':[
            'The prompt discloses the missing functional bin and exact loopback(129) remedy.',
            'This test demonstrates one targeted feedback integration, not autonomous discovery.',
            'The same additional scenario can be generated deterministically by a directed rule.',
            'Final 100% is over 10 predefined bins only, not all possible UART faults.'
        ]
    }
    write_json(out/'experiment_status.json',evidence)
    prompt_path = out/'hermes_feedback_prompt.txt'
    prompt_path.write_text(feedback_prompt(original),encoding='utf-8')
    print('Evidence directory:',out, flush=True)
    try:
        # Exact original baseline replay happens before the model request, so source
        # evidence and oracle must agree on the 90% baseline.
        baseline,baseline_records=aggregate(pipeline,'trial5_replayed',original,out)
        expect(baseline['min_coverage_pct']==90.0,'Trial5 replay not 90%; stop before AI call')
        for row in baseline_records:
            expect(row['coverage'][BIN]==0 and sum(row['coverage'].values())==9,
                   'Baseline replay did not reproduce only the edge_81 gap')
        evidence['replayed_baseline']=baseline
        write_json(out/'experiment_status.json',evidence)
        print('\n========== ONE LIVE HERMES GAP-FEEDBACK CALL ==========',flush=True)
        t0=time.monotonic()
        response=bridge.run_hermes(str(prompt_path),timeout_seconds=args.timeout)
        evidence['hermes_calls']=1
        evidence['hermes_seconds']=round(time.monotonic()-t0,3)
        write_json(out/'hermes_response_raw.json',response)
        expect(response.get('status')=='PASS',
               'Hermes failed: '+str(response.get('error') or response.get('response_text','')[:200]))
        suggested=valid_feedback(response,original,pipeline)
        evidence['additional_ai_scenarios']=1
        evidence['hermes_status']='PASS'
        write_json(out/'hermes_validated_extra_scenario.json',
                   {'scenarios':[suggested],'origin':'LIVE_HERMES_SINGLE_FEEDBACK'})
        print('[PASS] Live Hermes supplied one validated edge_81 loopback scenario',flush=True)
        ai_extended=original+[suggested]
        # Matched deterministic rule: use the same known loopback(129) stimulus.
        directed=original+[{'id':'directed_edge_81','kind':'loopback','value':129}]
        ai_agg,ai_records=aggregate(pipeline,'trial5_ai_feedback',ai_extended,out)
        directed_agg,directed_records=aggregate(pipeline,'trial5_directed_feedback',directed,out)
        expect(ai_agg['min_coverage_pct']==100.0,'AI gap closure not achieved')
        expect(directed_agg['min_coverage_pct']==100.0,'Directed control not closed')
        for row in ai_records+directed_records:
            expect(row['coverage'][BIN]==1 and sum(row['coverage'].values())==10,
                   f'Coverage closure missing at CPB {row["cpb"]}')
        # Equal stimuli should create equal deterministic sim metrics.
        expect(ai_agg['cycles']==directed_agg['cycles'] and
               ai_agg['checks']==directed_agg['checks'],
               'Matched directed and AI tests generated different cycles/checks')
        for name,items in [('original_trial5',original),('hermes_feedback_11',ai_extended),
                           ('matched_directed_11',directed)]:
            write_json(out/f'{name}.json',{'scenarios':items})
        evidence.update({'status':'PASS','feedback_kind':suggested['kind'],
                         'feedback_value':suggested['value'],
                         'final_ai_scenario_count':len(ai_extended),
                         'baseline_replay_coverage_pct':baseline['min_coverage_pct'],
                         'ai_feedback_min_coverage_pct':ai_agg['min_coverage_pct'],
                         'matched_directed_min_coverage_pct':directed_agg['min_coverage_pct'],
                         'ai_feedback':ai_agg,'matched_directed':directed_agg,
                         'closure_target_met':True})
        # Recheck hashes before claiming result.
        for name,digest in hashes.items():
            expect(sha(RTL/name)==digest,f'Frozen RTL modified: {name}')
        write_json(out/'experiment_status.json',evidence)
        report = '\n'.join([
            '# Phase 4D-7 — Targeted Hermes feedback closure', '',
            '## Input evidence','',
            f'- Trial 5: 10 scenarios and 90% (9/10 bins) at CPBs 8,16,32,64.',
            '- Only missing bin: **edge_81**.',
            f'- Evidence source: `{trial_root}`.', '',
            '## Controlled follow-up','',
            '- One fresh live Hermes request; one strictly validated extra scenario.',
            '- Existing ten scenarios preserved, one additional loopback(129) appended.',
            '- Comparator: identical deterministic directed loopback(129), also one added scenario.',
            '- Both 11-scenario sets independently simulated at four CPBs.', '',
            '## Verified results','',
            f'- Replayed Trial 5 coverage: **{baseline["min_coverage_pct"]}%**.',
            f'- Hermes plus targeted feedback: **{ai_agg["min_coverage_pct"]}%**.',
            f'- Matched directed addition: **{directed_agg["min_coverage_pct"]}%**.',
            f'- AI additional generation latency: **{evidence["hermes_seconds"]} seconds**.',
            f'- Incremental model calls: **{evidence["hermes_calls"]}**.',
            f'- Incremental test scenarios: **{evidence["additional_ai_scenarios"]}**.', '',
            '## Research limitation', '',
            'The prompt explicitly explains the missing bin and its exact deterministic remedy, '
            'so this experiment validates live integration of a feedback loop, not model discovery '
            'or superiority over directed test selection. Scenario budgets differ from original '
            'ten-scenario comparisons; the 11-scenario directed extension is the matched comparator.',
            'Coverage is over ten enumerated bins, not exhaustive RTL proof or extra fault detection.', ''
        ])
        (out/'PHASE4D7_RESEARCH_REPORT.md').write_text(report,encoding='utf-8')
        print('\n========== PHASE 4D-7 COVERAGE CLOSURE SUMMARY ==========',flush=True)
        print('Live Hermes response: PASS',flush=True)
        print(f'Trial5 replay: {baseline["min_coverage_pct"]}% (10 scenarios)',flush=True)
        print(f'Hermes feedback: {ai_agg["min_coverage_pct"]}% (11 scenarios)',flush=True)
        print(f'Matched directed: {directed_agg["min_coverage_pct"]}% (11 scenarios)',flush=True)
        print(f'Additional AI calls: {evidence["hermes_calls"]}',flush=True)
        print('RTL hashes: unchanged',flush=True)
        print('Report:',out/'PHASE4D7_RESEARCH_REPORT.md',flush=True)
        print('PHASE 4D-7: PASS',flush=True)
    except Exception as error:
        evidence.update({'status':'FAIL','failure':f'{type(error).__name__}: {str(error)[:600]}'})
        write_json(out/'experiment_status.json',evidence)
        print('[FAIL] Phase 4D-7:',error,file=sys.stderr)
        print('Partial evidence retained at:',out,file=sys.stderr)
        raise SystemExit(1)


if __name__=='__main__':
    try:
        main()
    except (RuntimeError,ValueError,KeyError,TypeError,FileNotFoundError) as exc:
        print('[FAIL] Phase 4D-7 preflight:',exc,file=sys.stderr)
        raise SystemExit(1)
