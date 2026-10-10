#!/usr/bin/env python3
"""One authoritative gate for review readiness: no placeholder passes."""
from pathlib import Path
import csv, hashlib, json, sys
from datetime import datetime, timezone

WF=Path(__file__).resolve().parents[1]
ROOT=WF.parent
STATUS=WF/'evaluation'/'workflow_status.json'

def check(label,passed,detail):
    return {'step':label,'status':'PASS' if passed else 'PENDING','detail':detail}

def main():
    checks=[]
    rtl=WF/'phase_01_rtl/uart'
    files=['uart_tx.v','uart_rx.v','uart_tx_opt.v','uart_rx_opt.v']
    checks.append(check('P1_UART_RTL',all((rtl/f).is_file() for f in files),'Four UART RTL source snapshots'))
    legacy=WF/'evaluation/reference/master_requirements.csv'
    try:
        with legacy.open(newline='') as f:r=list(csv.DictReader(f))
        hist=len(r)==18 and len({x['id'] for x in r})==18 and all(x.get('reconciled_status')=='PASS' for x in r)
    except (OSError,KeyError):hist=False
    checks.append(check('BASELINE_TECHNICAL_AUDIT',hist,'Original 18-requirement audit is retained as historical evidence'))
    k=WF/'phase_02_parsing/results/uart_knowledge.json'
    know=None
    try:
        know=json.loads(k.read_text())
        parsed=know['source_analysis']
        ok=set(parsed)=={'uart_tx','uart_rx','uart_tx_opt','uart_rx_opt'} and all(
            hashlib.sha256((WF/parsed[m]['file']).read_bytes()).hexdigest()==parsed[m]['sha256']
            for m in parsed)
    except (KeyError,OSError,ValueError,TypeError):ok=False
    checks.append(check('P2_UART_PYVERILOG',ok,'Live PyVerilog AST output with four hashes; not a heuristic placeholder'))
    obj=WF/'phase_03_ai_verification/results/objectives.json'
    prompt=WF/'phase_03_ai_verification/results/hermes/initial_prompt.txt'
    checks.append(check('P3_OBJECTIVES_PROMPT',obj.is_file() and prompt.is_file(),'UART objectives and prompt generated'))
    summ=WF/'phase_03_ai_verification/results/evaluation_summary.json'
    try: data=json.loads(summ.read_text())
    except (ValueError,OSError):data={}
    suites=data.get('suites',{})
    baseline_ok=all(suites.get(n,{}).get('all_pass') and
                    set(suites[n].get('tested_cpbs',[]))=={8,16,32,64}
                    for n in ('directed','random'))
    checks.append(check('P3_DIRECTED_RANDOM',baseline_ok,'Icarus simulation for two baselines across four clock settings'))
    ai_ok=data.get('ai_generation')=='HERMES_CHAT_ONESHOT' and suites.get('ai_initial',{}).get('all_pass') and \
          set(suites.get('ai_initial',{}).get('tested_cpbs',[]))=={8,16,32,64}
    checks.append(check('P3_HERMES_UART',ai_ok,'Hermes-generated UART scenarios validated and simulated across four settings'))
    closure_ok=bool(ai_ok and data.get('closure_target_met') and data.get('final_ai_coverage')==100.0)
    checks.append(check('P3_COVERAGE_CLOSURE',closure_ok,'All ten functional bins hit by validated AI/feedback tests'))
    fair=bool(ai_ok and baseline_ok and all(data.get('comparisons',{}).get(n,{}).get('scenario_budget')==10 for n in ('directed','random','ai_initial')))
    checks.append(check('P3_FAIR_COMPARISON',fair,'Same initial test budget; feedback reported separately'))
    uart=WF/'phase_04_uart_novelty/reference/uart_report.json'
    try: u=json.loads(uart.read_text());uo=u.get('status')=='PASS'
    except (OSError,ValueError):uo=False
    checks.append(check('P4_UART_ARCHITECTURE_PPA',uo,'Archived UART technology mapping and verified hybrid comparison'))
    checks.append(check('P4_UART_AI_INTEGRATION',bool(closure_ok and fair and uo),
                        'Only complete when new AI evidence and original PPA are both present'))
    integrated=WF/'phase_04_uart_novelty/UART_INTEGRATED_RESEARCH_REPORT.json'
    try: ir=json.loads(integrated.read_text());integrated_ok=ir.get('status')=='PASS'
    except (OSError,ValueError):integrated_ok=False
    checks.append(check('P4_INTEGRATED_RESULTS_REPORT',integrated_ok and bool(closure_ok),
                        'Combined AI verification and archived mapped UART architecture report'))
    checks.append(check('EVALUATION_REVIEW_STRUCTURE',
                        (WF/'README.md').exists() and (WF/'docs/PHASE_EXECUTION_GUIDE.md').exists(),
                        'All four reviewer-facing phases and execution guide'))
    all_pass=all(c['status']=='PASS' for c in checks)
    STATUS.parent.mkdir(parents=True,exist_ok=True)
    doc={'generated_utc':datetime.now(timezone.utc).isoformat(),
         'status':'PASS' if all_pass else 'WORK_REMAINING',
         'passed':sum(x['status']=='PASS' for x in checks),
         'total':len(checks),'checks':checks,
         'no_fabrication':'Existing audit and new UART AI validation are separate evidence'}
    STATUS.write_text(json.dumps(doc,indent=2)+'\n')
    print('========== PHASE WORKFLOW REQUIREMENTS AUDIT ==========')
    for item in checks:print(f"{item['step']:30} {item['status']:8} {item['detail']}")
    print('SUMMARY:',doc['passed'],'/',doc['total'])
    print('OVERALL:',doc['status'])
    print('REPORT:',STATUS)
    return 0 if all_pass else 2

if __name__=='__main__':
    sys.exit(main())
