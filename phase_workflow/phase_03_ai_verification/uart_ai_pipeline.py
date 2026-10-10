#!/usr/bin/env python3
"""UART AI test generation, validation, simulation, coverage and feedback.

Actual AI results require an installed, working Hermes invocation or an
explicit, externally obtained AI response. Never reports an AI PASS otherwise.
"""
import argparse
import hashlib
import json
import random
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from testbench_generator import BINS, make_tb, validate_scenarios

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT.parent
BASE = ROOT / 'phase_03_ai_verification'
PARSED = ROOT / 'phase_02_parsing' / 'results' / 'uart_knowledge.json'
RESULTS = BASE / 'results'
RTL = ROOT / 'phase_01_rtl' / 'uart'
SRC = [RTL / f for f in ('uart_tx.v','uart_tx_opt.v','uart_rx.v','uart_rx_opt.v')]
OBJ = {
  'transaction':'Each 8N1 payload must traverse baseline TX to both baseline and optimized RX',
  'oracle':'Compare RX received byte to stimulus; check valid and stop bit; compare optimized and baseline TX/RX every clock',
  'timing':'Exercise 8, 16, 32 and 64 clocks per bit, without modifying RTL',
  'corners':'00, FF, 55, AA, 81, other payload, bad stop, reset mid-frame, ignored start while busy, repeated frames',
  'closure':'Select legal tests for bins not covered by previous validated simulations',
}

def save(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2)+'\n',encoding='utf-8')

def directed():
    vals=(0,255,85,170,129,55,17,0,85,129)
    return [{'id':f'directed_{i:02d}','kind':'loopback','value':v} for i,v in enumerate(vals)]

def randomized(seed):
    rng=random.Random(seed)
    return [{'id':f'random_{i:02d}','kind':'loopback','value':rng.randrange(256)} for i in range(10)]

def prompt(knowledge, uncovered=None, prior=None):
    schema = {
       'scenarios': [
        {'id':'test_01','kind':'loopback','value':85},
        {'id':'test_02','kind':'bad_stop'},
        {'id':'test_03','kind':'reset_mid_tx'},
        {'id':'test_04','kind':'busy_start','value':129},
        {'id':'test_05','kind':'paired_frames','value':17}
       ]}
    bins=uncovered if uncovered is not None else list(BINS)
    return ("You are developing SAFE FUNCTIONAL VERILOG TEST SCENARIOS for a fixed 8N1 UART.\n"
            "Respond with ONLY one JSON object (not Markdown) containing an array key 'scenarios'.\n"
            "Do not write code or commands. The deterministic generator supplies its own testbench.\n"
            "Allowed kind values: loopback, bad_stop, reset_mid_tx, busy_start, paired_frames.\n"
            "For loopback, busy_start and paired_frames provide integer 'value' 0..255.\n"
            "For bad_stop and reset_mid_tx omit 'value'.\n"
            "Each scenario must have a unique short alphanumeric underscore id. "
            + ("Generate exactly 10 scenarios.\n" if uncovered is None else "Generate 1 to 10 new scenarios.\n")
            + "Prioritize missing bins and avoid duplicate operations.\n"
            f"REQUIRED BINS: {json.dumps(bins)}\n"
            f"CONTRACT: {json.dumps(knowledge['protocol'],sort_keys=True)}\n"
            f"OBJECTIVES: {json.dumps(OBJ,sort_keys=True)}\n"
            f"ALREADY TESTED: {json.dumps(prior or [],sort_keys=True)}\n"
            f"EXAMPLE RESPONSE: {json.dumps(schema)}\n")

def parse_hermes_response(value, require_count=None):
    if isinstance(value,dict):
        value=value.get('response_text') or value.get('text') or value.get('output') or value
    if isinstance(value,str):
        s=value.strip()
        if s.startswith('```'):
            s=re.sub(r'^```(?:json)?\s*','',s,flags=re.I)
            s=re.sub(r'\s*```$','',s)
        try: value=json.loads(s)
        except json.JSONDecodeError as exc: raise ValueError('Hermes response is not valid JSON') from exc
    if not isinstance(value,dict): raise ValueError('Expected Hermes JSON object with scenarios array')
    items=validate_scenarios(value,maximum=10)
    if require_count is not None and len(items)!=require_count:
        raise ValueError(f'For equal-budget comparison Hermes must return exactly {require_count} scenarios; got {len(items)}')
    return items

def call_hermes(prompt_path,timeout,require_count=None):
    helper=BASE / 'hermes_bridge.py'
    if not helper.exists(): raise RuntimeError('Hermes bridge not installed')
    import importlib.util
    spec=importlib.util.spec_from_file_location('phase_hermes_bridge',helper)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    result=module.run_hermes(str(prompt_path),timeout_seconds=timeout)
    save(RESULTS/'hermes'/(prompt_path.stem+'_raw.json'),result)
    if result.get('status')!='PASS':
        raise RuntimeError('Hermes call failed: '+str(result.get('error') or result.get('stage')))
    return parse_hermes_response(result,require_count=require_count)

def simulate(name,scenarios,cpb):
    if not shutil.which('iverilog') or not shutil.which('vvp'):
        raise RuntimeError('Icarus Verilog missing; install iverilog in Ubuntu WSL')
    stem=f'{name}_cpb{cpb}'
    dest=RESULTS/'simulation'/stem
    dest.mkdir(parents=True,exist_ok=True)
    tb=dest/'tb_uart_phase.v'
    exe=dest/'uart_sim.out'
    tb.write_text(make_tb(scenarios,cpb),encoding='utf-8')
    save(dest/'scenarios.json',{'scenarios':scenarios,'origin':name})
    cmd=['iverilog','-g2012','-s','tb_uart_phase','-o',str(exe),str(tb),*(str(f) for f in SRC)]
    c=subprocess.run(cmd,capture_output=True,text=True,timeout=120)
    (dest/'compile.log').write_text(c.stdout+'\n'+c.stderr,encoding='utf-8')
    if c.returncode:
        raise RuntimeError(f'{stem}: iverilog compilation failed. See {dest / "compile.log"}')
    start=time.monotonic()
    r=subprocess.run(['vvp',str(exe)],capture_output=True,text=True,timeout=120)
    duration=round(time.monotonic()-start,4)
    (dest/'simulation.log').write_text(r.stdout+'\n'+r.stderr,encoding='utf-8')
    def field(label):
        m=re.search(r'^'+re.escape(label)+r'=(\d+)\s*$',r.stdout,re.M)
        if not m: raise RuntimeError(f'{stem}: missing simulator {label} marker')
        return int(m.group(1))
    checks=field('TOTAL_CHECKS'); failed=field('FAILED_CHECKS'); cycles=field('CYCLES')
    match=re.search(r'^COVERAGE=(.*)$',r.stdout,re.M)
    if not match: raise RuntimeError(f'{stem}: missing COVERAGE marker')
    bins={}
    for piece in match.group(1).strip().split(','):
        name_bin,count=piece.strip().split(':',1)
        bins[name_bin]=int(count)
    if set(bins)!=set(BINS) or not all(v in (0,1) for v in bins.values()):
        raise RuntimeError(f'{stem}: coverage signature incorrect')
    verdict=re.search(r'^VERDICT=(PASS|FAIL)\s*$',r.stdout,re.M)
    status=('PASS' if r.returncode==0 and failed==0 and verdict and verdict.group(1)=='PASS' else 'FAIL')
    report={'status':status,'suite':name,'cpb':cpb,'scenarios':len(scenarios),
            'checks':checks,'failed':failed,'cycles':cycles,'wall_seconds':duration,
            'coverage':bins,'covered_bins':sum(bins.values()),
            'coverage_pct':round(100*sum(bins.values())/len(BINS),2),
            'simulation_log':(dest/'simulation.log').relative_to(ROOT).as_posix()}
    save(dest/'result.json',report)
    print(f'[{status}] {stem}: {checks} checks; {report["covered_bins"]}/{len(BINS)} bins; {duration}s')
    if status!='PASS': raise RuntimeError(f'{stem}: simulation failed. See {dest / "simulation.log"}')
    return report

def evaluate(name,scenarios,cpbs):
    result=[]
    for cpb in cpbs: result.append(simulate(name,scenarios,cpb))
    return result

def aggregate(records):
    return {'tested_cpbs':[r['cpb'] for r in records],
            'checks':sum(r['checks'] for r in records),
            'cycles':sum(r['cycles'] for r in records),
            'failed_checks':sum(r['failed'] for r in records),
            'min_coverage_pct':min(r['coverage_pct'] for r in records),
            'coverage_by_cpb':{str(r['cpb']):r['coverage'] for r in records},
            'seconds':round(sum(r['wall_seconds'] for r in records),4),
            'all_pass':all(r['status']=='PASS' for r in records)}

def create_knowledge():
    cmd=[sys.executable,str(ROOT/'phase_02_parsing'/'extract_uart.py')]
    print('PHASE 2: extracting UART AST knowledge')
    p=subprocess.run(cmd,cwd=PROJECT)
    if p.returncode: raise RuntimeError('Phase 2 parsing failed; no placeholder model generated')
    return json.loads(PARSED.read_text(encoding='utf-8'))

def import_scenarios(path):
    obj=json.loads(path.read_text(encoding='utf-8'))
    return parse_hermes_response(obj,require_count=10)

def save_initial(knowledge):
    save(RESULTS/'objectives.json',OBJ)
    for name,items in [('directed',directed()),('random',randomized(20261010))]:
        save(RESULTS/(name+'_scenarios.json'),{'scenarios':items, 'origin':'deterministic_non_ai'})
    pp=RESULTS/'hermes'/'initial_prompt.txt';pp.parent.mkdir(parents=True,exist_ok=True)
    pp.write_text(prompt(knowledge),encoding='utf-8')
    print('[PASS] Phase 3: objectives, directed/random baselines, AI prompt prepared')

def merge(prev,new,limit=24):
    joined=list(prev); ids={s['id'] for s in joined}
    for n,s in enumerate(new):
        if len(joined)>=limit:break
        clone=dict(s)
        if clone['id'] in ids: clone['id']='feedback_'+str(n)+'_'+str(len(joined))
        if len(clone['id'])>48: clone['id']=clone['id'][:48]
        joined.append(clone);ids.add(clone['id'])
    return joined

def main():
    ap=argparse.ArgumentParser(description='End-to-end UART AI verification workflow')
    ap.add_argument('--mode',choices=('prepare','baseline','ai','all','report'),default='prepare')
    ap.add_argument('--cpb',nargs='+',type=int,default=[8,16,32,64])
    ap.add_argument('--ai-json',type=Path,help='Raw Hermes response JSON captured externally; documented AI provenance required')
    ap.add_argument('--timeout',type=int,default=180)
    ap.add_argument('--feedback-rounds',type=int,default=2)
    args=ap.parse_args()
    if args.cpb != sorted(set(args.cpb)) or any(not 8<=c<=256 for c in args.cpb):
        raise ValueError('CPB list must be unique ascending integers in [8,256]')
    if args.feedback_rounds not in (0,1,2): raise ValueError('Feedback rounds must be 0..2')
    RESULTS.mkdir(parents=True,exist_ok=True)
    if args.mode=='report':
        p=RESULTS/'evaluation_summary.json'
        if not p.exists(): raise RuntimeError('No completed analysis yet')
        print(p.read_text());return
    knowledge=create_knowledge();save_initial(knowledge)
    if args.mode=='prepare':
        print('STATUS=READY_FOR_REAL_HERMES_AND_SIMULATION (not verified complete)');return
    summary={'generated_utc':datetime.now(timezone.utc).isoformat(),
             'status':'IN_PROGRESS','cpb_values':args.cpb,
             'source_fingerprints':{k:v['sha256'] for k,v in knowledge['source_analysis'].items()},
             'ai_generation':'NOT_RUN', 'comparisons':{},'suites':{},
             'note':'Actual measurements only; no estimated or fabricated test results'}
    if args.mode in ('baseline','all'):
        for name,scenarios in [('directed',directed()),('random',randomized(20261010))]:
            results=evaluate(name,scenarios,args.cpb)
            summary['suites'][name]=aggregate(results)
        save(RESULTS/'evaluation_summary.json',summary)
    if args.mode in ('ai','all'):
        path=RESULTS/'hermes'/'initial_prompt.txt'
        if args.ai_json:
            print('NOTICE: Imported test cases have EXTERNAL provenance; confirm produced by Hermes')
            ai=import_scenarios(args.ai_json)
            summary['ai_generation']='IMPORTED_RESPONSE_USER_PROVIDED'
        else:
            ai=call_hermes(path,args.timeout,require_count=10)
            summary['ai_generation']='HERMES_CHAT_ONESHOT'
        save(RESULTS/'hermes'/'validated_ai_scenarios.json',{'scenarios':ai,'origin':summary['ai_generation']})
        result=evaluate('ai_initial',ai,args.cpb)
        summary['suites']['ai_initial']=aggregate(result)
        save(RESULTS/'evaluation_summary.json',summary)
        current=ai
        for round_no in range(1,args.feedback_rounds+1):
            bins=set.intersection(*({b for b,v in r['coverage'].items() if v} for r in result))
            missing=[b for b in BINS if b not in bins]
            print(f'FEEDBACK ROUND {round_no}: missing bins {missing}')
            if not missing:break
            if args.ai_json:
                summary['feedback_status']='PENDING_HERMES_LIVE_FEEDBACK'
                break  # Avoid claiming a replayed AI response constitutes feedback.
            dest=RESULTS/'hermes'/f'feedback_prompt_{round_no}.txt'
            dest.write_text(prompt(knowledge,uncovered=missing,prior=current),encoding='utf-8')
            extra=call_hermes(dest,args.timeout)
            new=merge(current,extra)
            if len(new)==len(current):break
            current=new
            result=evaluate(f'ai_feedback_{round_no}',current,args.cpb)
            summary['suites'][f'ai_feedback_{round_no}']=aggregate(result)
            save(RESULTS/'evaluation_summary.json',summary)
        summary['ai_total_scenarios']=len(current)
        final_agg=aggregate(result)
        summary['final_ai_coverage']=final_agg['min_coverage_pct']
        summary['closure_target_met']=final_agg['min_coverage_pct']==100.0
        if not summary['closure_target_met']:
            summary['feedback_status']=summary.get('feedback_status','COVERAGE_GAPS_REMAIN')
    summary['status']=('PASS' if (summary['ai_generation']=='HERMES_CHAT_ONESHOT' and summary['suites'].get('directed') and summary['suites'].get('random') and summary['suites'].get('ai_initial') and summary.get('closure_target_met')) else ('BASELINES_PASS_AI_PENDING' if args.mode=='baseline' else 'PARTIAL_PENDING_AI_CLOSURE'))
    if 'directed' in summary['suites'] and 'random' in summary['suites'] and 'ai_initial' in summary['suites']:
        summary['comparisons']={n:{'scenario_budget':10 if n!='ai_initial' else len(ai),
                                   'coverage_min_pct':summary['suites'][n]['min_coverage_pct'],
                                   'total_sim_cycles':summary['suites'][n]['cycles'],
                                   'total_checks':summary['suites'][n]['checks'],
                                   'coverage_bins_per_1000_sim_cycles':round(summary['suites'][n]['min_coverage_pct']/10*1000 / max(1,summary['suites'][n]['cycles']),5)} for n in ('directed','random','ai_initial')}
        summary['comparisons']['note']='Coverage at original budgets is the fair comparison; targeted closure is separately reported.'
    save(RESULTS/'evaluation_summary.json',summary)
    print('FINAL STATUS:',summary['status'])
    print('REPORT:',RESULTS/'evaluation_summary.json')
    if summary['status']!='PASS':
        print('INFO: AI or full coverage remains pending; do not claim complete.')

if __name__=='__main__':
    try:main()
    except (ValueError,RuntimeError,OSError,subprocess.TimeoutExpired) as exc:
        print('[FAIL] UART PIPELINE:',exc,file=sys.stderr)
        sys.exit(1)
