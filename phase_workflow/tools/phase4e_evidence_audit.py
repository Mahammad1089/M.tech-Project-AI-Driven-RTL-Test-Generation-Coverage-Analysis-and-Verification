#!/usr/bin/env python3
"""Phase 4E: reproduce literature-report numbers from immutable phase evidence.

Place at phase_workflow/tools/phase4e_evidence_audit.py and execute from repository root.
This script does not call Hermes, synthesize, simulate, delete, rename, or edit RTL.
It validates the actual phase-result JSON and optionally writes a new review-only
trace in phase_workflow/phase_04_uart_novelty/research/.

Use: python3 phase_workflow/tools/phase4e_evidence_audit.py --dry-run
     python3 phase_workflow/tools/phase4e_evidence_audit.py --write
"""
from __future__ import annotations
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

WF = Path(__file__).resolve().parents[1]
EV = WF / 'evaluation'
AI = WF / 'phase_03_ai_verification' / 'results'
RTL = WF / 'phase_01_rtl' / 'uart'
KNOWLEDGE = WF / 'phase_02_parsing' / 'results' / 'uart_knowledge.json'
OUT = WF / 'phase_04_uart_novelty' / 'research'
CPBS = [8, 16, 32, 64]


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def load(path):
    require(path.is_file(), f'Required evidence missing: {path}')
    return json.loads(path.read_text(encoding='utf-8'))


def latest_verified(folder, pattern, file_name, predicate):
    found = sorted(folder.glob(pattern), reverse=True)
    for item in found:
        path = item / file_name
        if path.is_file():
            data = load(path)
            if predicate(data):
                return path, data
    raise RuntimeError(f'No verified {file_name} found in {folder}')


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def near(actual, expected, name):
    require(isinstance(actual, (float, int)) and abs(actual - expected) < 0.015,
            f'{name}: expected {expected}; recorded {actual}')


def run():
    print('========== PHASE 4E: EVIDENCE AND NOVELTY AUDIT ==========')
    audit_path = EV / 'workflow_status.json'
    audit = load(audit_path)
    require((audit.get('status'),audit.get('passed'),audit.get('total')) == ('PASS',12,12),
            'Historical 12/12 workflow audit is no longer PASS')
    print('[PASS] Historical workflow audit: 12/12')

    knowledge = load(KNOWLEDGE)
    hashes = {}
    for name in ('uart_tx', 'uart_tx_opt', 'uart_rx', 'uart_rx_opt'):
        source = RTL / (name + '.v')
        require(source.is_file(),f'Missing phase RTL: {source}')
        digest = sha256(source)
        require(digest == knowledge['source_analysis'][name]['sha256'],
                f'Source hash mismatch: {source}')
        hashes[source.name] = digest
    print('[PASS] Four UART RTL SHA-256 hashes unchanged')

    ai = load(AI / 'evaluation_summary.json')
    require(ai.get('status') == 'PASS' and ai.get('ai_generation') == 'HERMES_CHAT_ONESHOT',
            'Archived Hermes UART evaluation is not PASS')
    for name, cov in (('directed',60.0),('random',20.0),('ai_initial',100.0)):
        suite = ai.get('suites',{}).get(name,{})
        require(suite.get('all_pass') is True and suite.get('failed_checks') == 0
                and suite.get('tested_cpbs') == CPBS, f'Phase 3 suite mismatch: {name}')
        near(suite.get('min_coverage_pct'), cov, f'Phase 3 {name} coverage')
    require(ai.get('ai_total_scenarios') == 10 and ai.get('closure_target_met') is True,
            'Phase 3 model budget/coverage closure unexpected')
    print('[PASS] Phase 3: 10 AI scenarios; 100% of ten bins; 4 CPBs')

    base_path, base = latest_verified(EV / 'repeatability', 'phase4c_*',
             'phase4c_summary.json', lambda x:x.get('status') == 'PASS')
    require(len(base.get('random_seeds', [])) == 10,
            'Phase 4C-1 does not contain ten seeds')
    for name, exp in (('payload_random',13.0),('protocol_random',69.0),('balanced_directed',100.0)):
        near(base.get('statistics',{}).get(name,{}).get('mean'),exp,
             f'Phase 4C-1 {name} mean coverage')
    print('[PASS] Phase 4C-1: 10-seed comparison and strong directed control')

    fresh_path, fresh = latest_verified(EV / 'repeatability' / 'hermes_trials',
           'phase4c2_*','phase4c2_summary.json',
           lambda x:x.get('status') == 'PASS' and x.get('passed_trials') == 5)
    require(fresh.get('planned_trials') == 5 and fresh.get('failed_trials') == 0,
            'Phase 4C-2 attempts/failures unexpected')
    require(fresh.get('distinct_valid_scenario_signatures') == 5,
            'Fewer than five distinct validated AI sequences')
    near(fresh.get('statistics',{}).get('mean'),98.0,'Five-trial AI coverage mean')
    trial5 = next((t for t in fresh.get('trials', []) if t.get('trial') == 5),None)
    require(trial5 is not None and trial5.get('simulation_status') == 'PASS',
            'Trial 5 unavailable or unverified')
    near(trial5.get('min_coverage_pct'),90.0,'Trial 5 coverage')
    for item in trial5.get('per_cpb',[]):
        missing = [name for name,val in item.get('coverage',{}).items() if val == 0]
        require(missing == ['edge_81'], 'Trial 5 gap differs from edge_81')
    require(len(trial5.get('per_cpb',[])) == 4, 'Trial 5 missing CPB records')
    print('[PASS] Phase 4C-2: 5/5 valid AI trials; 98% mean; trial 5 edge_81 gap')

    mutation_path, mutation = latest_verified(EV/'fault_injection',
            'phase4d5_reset_checker_*','corrected_checker_summary.json',
            lambda x:x.get('status') == 'PASS'
                and x.get('checks',{}).get('mutant_simulations') == 1512)
    require(mutation.get('checks',{}).get('clean_controls') == 108 and
            mutation.get('checks',{}).get('invalid') == 0 and
            mutation.get('original_rtl_unchanged') is True,
            'Full corrected mutation evidence incomplete')
    for name, exp in (('balanced_directed',100.0),('hermes_ai',100.0),
                      ('hermes_archived',100.0),('protocol_random',81.43),
                      ('payload_random',50.71)):
        near(mutation.get('method_score_pct',{}).get(name,{}).get('mean'),exp,
             f'Corrected mutation {name}')
    print('[PASS] Phase 4D-6: 1512 mutant simulations; AI/direct all 14 killed')

    feedback_path, feedback = latest_verified(EV/'feedback_closure','phase4d7_*',
         'experiment_status.json',lambda x:x.get('status') == 'PASS'
             and x.get('closure_target_met') is True)
    require(feedback.get('hermes_calls') == 1 and
            feedback.get('additional_ai_scenarios') == 1 and
            feedback.get('final_ai_scenario_count') == 11,
            'Targeted feedback experiment budget differs')
    for key, exp in (('baseline_replay_coverage_pct',90.0),
                     ('ai_feedback_min_coverage_pct',100.0),
                     ('matched_directed_min_coverage_pct',100.0)):
        near(feedback.get(key),exp,key)
    require(feedback.get('feedback_kind') == 'loopback' and
            feedback.get('feedback_value') == 129,
            'Feedback did not use loopback(129)')
    print('[PASS] Phase 4D-7: real one-call feedback 90% to 100%; directed matches')

    evidence = {
      'stage':'PHASE_4E_LITERATURE_AND_NOVELTY_TRACE',
      'validated_utc':datetime.now(timezone.utc).isoformat(),
      'result':'PASS',
      'historical_audit':'PASS_12_OF_12',
      'rtl_sha256':hashes,
      'project_evidence':{
        'phase3_initial_AI_coverage_pct':100.0,
        'phase3_initial_scenarios':10,
        'phase4c1_payload_random_mean_pct':13.0,
        'phase4c1_protocol_random_mean_pct':69.0,
        'phase4c1_balanced_directed_pct':100.0,
        'phase4c2_fresh_ai_trials':5,
        'phase4c2_fresh_ai_mean_coverage_pct':98.0,
        'phase4c2_full_coverage_trials':4,
        'phase4d6_clean_controls':108,
        'phase4d6_mutant_simulations':1512,
        'phase4d6_corrected_mutation_scores':{n:v['mean'] for n,v in mutation['method_score_pct'].items()},
        'phase4d7_initial_coverage_pct':90.0,
        'phase4d7_feedback_coverage_pct':100.0,
        'phase4d7_matched_directed_coverage_pct':100.0,
        'phase4d7_incremental_AI_calls':1,
      },
      'sources':{
        'technical_audit':str(audit_path.relative_to(WF)),
        'phase3':str((AI/'evaluation_summary.json').relative_to(WF)),
        'phase4c1':str(base_path.relative_to(WF)),
        'phase4c2':str(fresh_path.relative_to(WF)),
        'phase4d6':str(mutation_path.relative_to(WF)),
        'phase4d7':str(feedback_path.relative_to(WF)),
      },
      'scientific_boundaries':[
        'This audit validates existing project evidence; it does not prove publication novelty.',
        'A 10-bin functional coverage model is not exhaustive verification.',
        '100% mutation score means all 14 selected mutants were killed, not all faults.',
        'AI and balanced-directed equal 100% on corrected mutation experiment.',
        'Targeted feedback prompt disclosed the exact bin and loopback(129) remedy.',
        'UART architecture PPA is an independent pre-layout synthesis result.',
      ]
    }
    print('PHASE 4E EVIDENCE AUDIT: PASS')
    return evidence


def write_outputs(evidence):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / 'PHASE4E_EVIDENCE_AUDIT.json'
    trace = OUT / 'PHASE4E_EVIDENCE_TRACE.md'
    path.write_text(json.dumps(evidence,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    lines = ['# Phase 4E: Verified evidence trace','','Evidence status: **PASS**.',
             'This document references existing WSL outputs; it does not rerun verification.','',
             '## Source provenance','','| Dataset | Project-relative file |','|---|---|']
    for key,val in evidence['sources'].items():
        lines.append(f'| {key} | `{val}` |')
    lines += ['','## Validated quantitative findings','']
    for key,val in evidence['project_evidence'].items():
        lines.append(f'- **{key}:** {val}')
    lines += ['','## Scientific boundaries','']
    lines += ['- '+item for item in evidence['scientific_boundaries']]
    lines += ['','## Literature positioning','','Literature references and method comparison are in the separately authored ',
              '`Phase_4E_Literature_and_Novelty_Report.docx` / `.md`. The literature is not verified by this offline data audit.','']
    trace.write_text('\n'.join(lines),encoding='utf-8')
    print('[PASS] Evidence JSON:',path)
    print('[PASS] Evidence Markdown:',trace)


if __name__=='__main__':
    import sys
    ap = argparse.ArgumentParser(description=__doc__)
    mode=ap.add_mutually_exclusive_group(required=True)
    mode.add_argument('--dry-run',action='store_true',help='Validate without writing files')
    mode.add_argument('--write',action='store_true',help='Validate and write new review-only evidence trace')
    args=ap.parse_args()
    try:
        result=run()
        if args.write:
            write_outputs(result)
        else:
            print('PHASE 4E PREFLIGHT: PASS (read-only)')
    except (KeyError,TypeError,ValueError,RuntimeError,OSError,json.JSONDecodeError) as error:
        print('[FAIL] PHASE 4E:',error,file=sys.stderr)
        sys.exit(1)
