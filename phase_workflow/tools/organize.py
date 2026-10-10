#!/usr/bin/env python3
"""Build a non-destructive, phase-labelled REVIEW view of the established project.

The source evidence/RTL remains byte-for-byte unchanged. Existing recorded paths
continue to work. Copies are created only for review; they are not used to
replace existing source paths or historical mapped PPA reports.
"""
import argparse
import csv
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

WF = Path(__file__).resolve().parents[1]
ROOT = WF.parent
PROVENANCE = WF / 'tools' / '.legacy_file_map.json'
RTL_FILES = {
    'rtl/alu.v': 'phase_01_rtl/benchmarks/alu.v',
    'rtl/fifo.v': 'phase_01_rtl/benchmarks/fifo.v',
    'rtl/fsm_1011.v': 'phase_01_rtl/benchmarks/sequence_detector.v',
    'extensions/rtl/optimized/alu_opt.v': 'phase_01_rtl/benchmarks/alu_optimized.v',
    'extensions/rtl/optimized/fifo_opt.v': 'phase_01_rtl/benchmarks/fifo_optimized.v',
    'extensions/rtl/fsm_variants/fsm_mealy_ext.v': 'phase_01_rtl/benchmarks/sequence_mealy.v',
    'extensions/rtl/fsm_variants/fsm_moore_ext.v': 'phase_01_rtl/benchmarks/sequence_moore.v',
    'extensions/rtl/uart/uart_tx.v': 'phase_01_rtl/uart/uart_tx.v',
    'extensions/rtl/uart/uart_rx.v': 'phase_01_rtl/uart/uart_rx.v',
    'extensions/rtl/uart/optimized/uart_tx_opt.v': 'phase_01_rtl/uart/uart_tx_opt.v',
    'extensions/rtl/uart/optimized/uart_rx_opt.v': 'phase_01_rtl/uart/uart_rx_opt.v',
    'hermes/hermes_interface.py': 'phase_03_ai_verification/hermes_bridge.py',
}
EVIDENCE_FILES = {
    'extensions/results/day30/master_audit_reconciled_v3/day30_master_requirements_reconciled_v3.csv': 'evaluation/reference/master_requirements.csv',
    'extensions/results/day30/alu_5ff_sensitivity/day30_alu_5ff_comparison.csv': 'evaluation/reference/alu_ppa_comparison.csv',
    'extensions/results/day30/fifo_final_report/day30_fifo_final_comparison.csv': 'evaluation/reference/fifo_ppa_comparison.csv',
    'extensions/results/day30/fsm_20_matrix/day30_fsm_20_matrix_results.csv': 'evaluation/reference/fsm_functional_matrix.csv',
    'extensions/results/day30/fsm_independent_coverage/day30_fsm_independent_coverage.csv': 'evaluation/reference/fsm_independent_coverage.csv',
    'extensions/results/day30/fsm_ppa_extension/day30_fsm_20_ppa_summary.csv': 'evaluation/reference/fsm_ppa.csv',
    'extensions/results/day30/fsm_comparison_extended/day30_fsm_10_mealy_moore_comparison.csv': 'evaluation/reference/fsm_architecture_comparison.csv',
    'extensions/results/day30/fsm_comparison_extended/day30_fsm_20_pareto_analysis.csv': 'evaluation/reference/fsm_pareto_analysis.csv',
    'extensions/results/day30/uart/final_report/day30_uart_architecture_comparison.csv': 'phase_04_uart_novelty/reference/uart_architecture_comparison.csv',
    'extensions/results/day30/uart/final_report/day30_uart_final_report.json': 'phase_04_uart_novelty/reference/uart_report.json',
}
GRAPH_DIR = 'extensions/results/day30/fsm_comparison_extended/graphs'

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1<<20),b''):h.update(chunk)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--check-only',action='store_true')
    args=ap.parse_args()
    if not (ROOT/'rtl/alu.v').exists():
        raise RuntimeError(f'Run inside complete M.Tech Git repository, not standalone ZIP: {ROOT}')
    pairs=dict(RTL_FILES);pairs.update(EVIDENCE_FILES)
    gdir=ROOT/GRAPH_DIR
    if not gdir.is_dir():raise RuntimeError('Missing verified FSM graph directory')
    for i,src in enumerate(sorted(gdir.glob('*.png'))):
        name=src.name
        parts=name.split('_',2)
        clean=parts[2] if len(parts)>2 else f'fsm_figure_{i+1}.png'
        pairs[src.relative_to(ROOT).as_posix()]='evaluation/figures/'+clean
    if args.check_only and not PROVENANCE.exists(): raise RuntimeError('Phase workspace not built')
    copied=[];failed=[]
    for source,target in sorted(pairs.items()):
        src=ROOT/source; dst=WF/target
        if not src.is_file():
            failed.append('MISSING SOURCE '+source);continue
        if dst.is_file():
            if digest(src)!=digest(dst):failed.append('REVIEW COPY CHANGED '+target)
        elif args.check_only:
            failed.append('MISSING COPY '+target)
        else:
            dst.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(src,dst)
        copied.append({'source':source,'review_path':target,'sha256':digest(src)})
    if failed: raise RuntimeError('\n'.join(failed))
    master=WF/'evaluation/reference/master_requirements.csv'
    with master.open(newline='',encoding='utf-8') as f: rows=list(csv.DictReader(f))
    if len(rows)!=18 or len({r.get('id') for r in rows})!=18 or any(r.get('reconciled_status')!='PASS' for r in rows):
        raise RuntimeError('Recorded 18/18 master audit unavailable or invalid')
    audit_path=WF/'evaluation/workflow_status.json'
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
    pub=WF/'evaluation/verification_summary.json'
    content={'project':'AI-assisted RTL verification and UART architecture evaluation',
             'status':'PHASE_WORKFLOW_VERIFIED' if phase_verified else 'HISTORICALLY_VERIFIED',
             'master_audit':{'passed':18,'total':18},
             'uart_ai_integration':'VERIFIED_12_OF_12' if phase_verified else 'PENDING_FRESH_VERIFICATION',
             'audit_note':'Archived 18/18 evidence preserved; new four-phase audit and live Hermes UART results validated.' if phase_verified else 'Historical 18/18 evidence preserved; new UART AI evidence is incomplete or absent.',
             'modules':['ALU','FIFO','FSM','UART']}
    if not args.check_only:
        pub.write_text(json.dumps(content,indent=2)+'\n',encoding='utf-8')
        PROVENANCE.write_text(json.dumps({'generated_utc':datetime.now(timezone.utc).isoformat(),
            'copied_count':len(copied),'mapping':copied},indent=2)+'\n',encoding='utf-8')
    print('[PASS] Preserved existing sources and copied',len(copied),'files into phase-based view')
    print('[PASS] Historical requirements 18/18 from immutable source evidence')
    print('[PASS] New AI UART integration verified (12/12)' if phase_verified else '[PENDING] New AI UART integration requires valid local evidence')
    print('REVIEW ROOT:',WF)

if __name__=='__main__':
    try:main()
    except (ValueError,OSError,RuntimeError) as ex:
        print('[FAIL] Phase organizer:',ex,file=sys.stderr);sys.exit(1)
