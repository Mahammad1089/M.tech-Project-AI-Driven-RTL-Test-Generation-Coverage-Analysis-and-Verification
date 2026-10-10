#!/usr/bin/env python3
"""Integrated AI-verification/architecture summary, never assumes AI success."""
import csv
import json
from pathlib import Path

WF=Path(__file__).resolve().parents[1]
PPA=WF/'phase_04_uart_novelty/reference/uart_architecture_comparison.csv'
UART=WF/'phase_04_uart_novelty/reference/uart_report.json'
AI=WF/'phase_03_ai_verification/results/evaluation_summary.json'
OUT=WF/'phase_04_uart_novelty/UART_INTEGRATED_RESEARCH_REPORT.md'
META=WF/'phase_04_uart_novelty/UART_INTEGRATED_RESEARCH_REPORT.json'

def main():
    with PPA.open(newline='',encoding='utf-8') as f: rows=list(csv.DictReader(f))
    old=json.loads(UART.read_text())
    if old.get('status')!='PASS':raise ValueError('Historical UART report does not verify PASS')
    if AI.is_file():
        new=json.loads(AI.read_text())
    else:new={}
    suites=new.get('suites',{})
    required=('directed','random','ai_initial')
    ai_pass=bool(new.get('status')=='PASS' and new.get('ai_generation')=='HERMES_CHAT_ONESHOT'
                 and new.get('closure_target_met') and all(s in suites for s in required))
    lines=['# Phase 4 — Combined UART Research Evaluation','',
           '## Experimental separation', '',
           'The UART architecture comparison is **previously verified, pre-layout mapped evidence**. '
           'The UART Hermes functional coverage evaluation is a separate **new experiment**. '
           'Do not infer AI hardware area or power improvements from the two reports.','',
           '## A. Historic baseline / optimized / hybrid UART architectures','',
           '| Option | Combined area (µm²) | Estimated power (µW) | Minimum individual slack (ns) |',
           '|---|---:|---:|---:|']
    for r in rows:
        lines.append(f"| {r['configuration'].replace('_',' ').title()} | {float(r['combined_area_um2']):.3f} | {float(r['combined_estimated_power_uw']):.3f} | {float(r['minimum_individual_setup_slack_ns']):.3f} |")
    lines.extend(['','## B. UART test-generation strategy comparison','',
                 '| Test strategy | Scenarios at initial budget | Minimum coverage across CPBs | Checks | Simulation cycles | Status |',
                 '|---|---:|---:|---:|---:|---|'])
    for label,key in [('Directed','directed'),('Deterministic random','random'),('Hermes — initial','ai_initial')]:
        r=suites.get(key)
        if r:
            budget=new.get('comparisons',{}).get(key,{}).get('scenario_budget','not recorded')
            lines.append(f"| {label} | {budget} | {r.get('min_coverage_pct','?')}% | {r.get('checks','?')} | {r.get('cycles','?')} | {'PASS' if r.get('all_pass') else 'REVIEW'} |")
        else:lines.append(f'| {label} | — | — | — | — | PENDING |')
    lines.extend(['','## C. AI-driven feedback closure','',
                  f"- Hermes source status: `{new.get('ai_generation','NOT_RUN')}`.",
                  f"- AI scenarios after feedback: `{new.get('ai_total_scenarios','NOT_AVAILABLE')}`.",
                  f"- Minimum measured AI coverage: `{new.get('final_ai_coverage','NOT_AVAILABLE')}`.",
                  f"- Coverage target met: `{new.get('closure_target_met',False)}`.",
                  f"- Full integrated experimental status: **{'PASS' if ai_pass else 'PENDING'}**.",
                  '', '## D. Research-claim guardrails','',
                  '- AI efficiency improvements may be claimed only when same-budget recorded metrics substantiate them.',
                  '- A 100% result refers to the ten defined functional test bins, not complete UART protocol state-space proof.',
                  '- The RX/TX RTL remains unchanged, and all experiments are simulation only.',
                  '- The PPA library is external; power is assumed-activity estimated, and timing is pre-layout.',
                  '- Publication-level novelty requires verified peer-reviewed prior-art comparison.',
                  '', '## Evidence locations','',
                  '- Phase 2 UART knowledge: `phase_02_parsing/results/uart_knowledge.json`',
                  '- Hermes prompts, scenario validation and simulations: `phase_03_ai_verification/results/`',
                  '- Original UART architecture comparison: `phase_04_uart_novelty/reference/`',
                  '- Automated final acceptance: `evaluation/workflow_status.json`',''])
    OUT.write_text('\n'.join(lines),encoding='utf-8')
    META.write_text(json.dumps({'status':'PASS' if ai_pass else 'PENDING',
                                'original_uart_ppa_status':old['status'],
                                'new_ai_source':new.get('ai_generation','NOT_RUN'),
                                'ai_coverage_complete':bool(new.get('closure_target_met',False)),
                                'comparison_suites_present':list(suites),
                                'estimated_hardware_metric_not_attributed_to_ai':True},indent=2)+'\n')
    print('RESEARCH EVALUATION:', 'PASS' if ai_pass else 'PENDING_NEW_UART_AI_RESULTS')
    print('REPORT:',OUT)
    return 0
if __name__=='__main__':raise SystemExit(main())
