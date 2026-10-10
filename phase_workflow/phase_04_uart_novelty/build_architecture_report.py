#!/usr/bin/env python3
"""Convert historic verified UART area/power evidence into a phase-named review report."""
import csv
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'phase_04_uart_novelty'
PPA=BASE/'reference/uart_architecture_comparison.csv'
UART=BASE/'reference/uart_report.json'
OUT=BASE/'UART_ARCHITECTURE_RESULTS.md'

def main():
    with PPA.open(newline='',encoding='utf-8') as f:rows=list(csv.DictReader(f))
    if {r['configuration'] for r in rows}!={'baseline','fully_optimized','hybrid'}:
        raise ValueError('Expected 3 verified UART architecture configurations')
    d=json.loads(UART.read_text())
    if d.get('status')!='PASS':raise ValueError('Original UART architecture result not PASS')
    baseline=next(r for r in rows if r['configuration']=='baseline')
    hybrid=next(r for r in rows if r['configuration']=='hybrid')
    ar=100*(1-float(hybrid['combined_area_um2'])/float(baseline['combined_area_um2']))
    pw=100*(1-float(hybrid['combined_estimated_power_uw'])/float(baseline['combined_estimated_power_uw']))
    lines=['# Phase 4 — UART Architecture and Novelty Evaluation','','## Verified technology-mapped UART comparison','',
        'Historical baseline/optimized TX and RX combinations are compared at **CPB = 16**.',
        'Power is estimated with assumed activity; area is mapped standard-cell area; timing is not a full-chip routed result.','',
        '| Configuration | Combined area (µm²) | Estimated power (µW) | Smallest component slack (ns) |',
        '|---|---:|---:|---:|']
    for r in rows:
        lines.append(f"| {r['configuration'].replace('_',' ').title()} | {float(r['combined_area_um2']):.3f} | {float(r['combined_estimated_power_uw']):.3f} | {float(r['minimum_individual_setup_slack_ns']):.3f} |")
    lines.extend(['',f'* Hybrid area reduction relative to baseline: **{ar:.2f}%**.',
                      f'* Hybrid assumed-activity power reduction relative to baseline: **{pw:.2f}%**.',
                      '* This comparison is existing physical-design estimate evidence, not proof of new LLM test-generation novelty.','',
                      '## Proposed AI-UART research evaluation','',
                      'Compare the new validated Hermes-generated scenario coverage at the same initial test budget with directed and deterministic-random baselines. Report additional closure rounds separately. Only then decide whether the project demonstrates a measurable AI contribution.','',
                      '## Scope limitations','',
                      'No FPGA or fabricated hardware, no post-route timing or measured silicon power, no claim of formally exhaustive UART protocol correctness.'])
    OUT.write_text('\n'.join(lines)+'\n')
    print('[PASS] Phase 4 review report:',OUT)

if __name__=='__main__':main()
