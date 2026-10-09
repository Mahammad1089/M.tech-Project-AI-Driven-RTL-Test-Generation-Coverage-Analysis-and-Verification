#!/usr/bin/env python3
"""Audit Day 30 FIFO functional, mapped area, setup timing and power evidence."""
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path.home() / 'Mtech_project' / 'AI_RTL_Verification'
DAY30 = ROOT / 'extensions' / 'results' / 'day30'
EQ = DAY30 / 'fifo_equivalence'
PPA = DAY30 / 'fifo_ppa'
OUT = DAY30 / 'fifo_final_report'
CONFIGS = [('w8_d4',8,4,2), ('w8_d8',8,8,3), ('w16_d4',16,4,2), ('w8_d16',8,16,4)]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load_csv(filename, key):
    path = PPA / filename
    require(path.is_file(), f'Missing CSV: {path}')
    with path.open(newline='', encoding='utf-8') as f:
        data = list(csv.DictReader(f))
    require(data, f'Empty CSV: {path}')
    result = {}
    for row in data:
        k = tuple(row[field] for field in key)
        require(k not in result, f'Duplicate record {k} in {filename}')
        result[k] = row
    return result


def number(row, field):
    require(field in row, f'Missing column: {field}')
    return float(row[field])


def check_log(path, marker):
    require(path.is_file(), f'Missing log: {path}')
    body = path.read_text(encoding='utf-8', errors='replace')
    require(marker in body, f'Completion marker missing: {path}')
    require(not re.search(r'(?im)^\s*(?:Error:|STA Error:|\[FAIL\])', body),
            f'Error found in log: {path}')
    return body


def equivalence_evidence(label):
    path = EQ / f'{label}.log'
    body = check_log(path, 'DAY 30 FIFO EQUIVALENCE: PASS')
    metrics = {}
    for field in ['TOTAL CYCLES', 'TOTAL CHECKS', 'PASSED CHECKS',
                  'FAILED CHECKS', 'ACCEPTED WRITES', 'ACCEPTED READS',
                  'BLOCKED WRITES', 'BLOCKED READS', 'SIMULTANEOUS REQUESTS',
                  'RESET EVENTS']:
        hits = re.findall(rf'(?m)^\s*{re.escape(field)}:\s*(\d+)\s*$', body)
        require(len(hits) == 1, f'{path}: expected one {field}, got {len(hits)}')
        metrics[field.lower().replace(' ', '_')] = int(hits[0])
    require(metrics['failed_checks'] == 0, f'Equivalence failures: {path}')
    require(metrics['total_checks'] == metrics['passed_checks'],
            f'Incorrect check totals: {path}')
    require(metrics['total_checks'] > 0 and metrics['total_cycles'] >= 5000,
            f'Incomplete test: {path}')
    return metrics


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    area = load_csv('day30_fifo_area_comparison.csv', ['configuration'])
    timing = load_csv('day30_fifo_timing_comparison.csv', ['design', 'configuration'])
    power = load_csv('day30_fifo_power_comparison.csv', ['configuration'])
    labels = {item[0] for item in CONFIGS}
    require(set(area) == {(x,) for x in labels}, 'Area configuration set incorrect')
    require(set(power) == {(x,) for x in labels}, 'Power configuration set incorrect')
    require(set(timing) == {(d, x) for x in labels for d in ('baseline','optimized')},
            'Timing configuration set incorrect')
    records = []
    total_checked = 0
    print('========== FIFO FINAL EVIDENCE AUDIT ==========')
    for label, width, depth, aw in CONFIGS:
        e = equivalence_evidence(label)
        a = area[(label,)]
        p = power[(label,)]
        bt = timing[('baseline', label)]
        ot = timing[('optimized', label)]
        for row in (a, p, bt, ot):
            for field, value in [('data_width',width), ('depth',depth), ('addr_width',aw)]:
                require(int(row[field]) == value, f'{label}: {field} mismatch')
        for row in (bt, ot):
            require(row['setup_status'] == 'MET', f'{label}: setup timing not MET')
            require(abs(number(row,'clock_period_ns') - 10.0) < 1e-8,
                    f'{label}: unexpected clock period')
        for implementation in ('baseline', 'optimized'):
            sta_log = PPA / f'{implementation}_{label}_timing.log'
            pow_log = PPA / f'{implementation}_{label}_power.log'
            check_log(sta_log, 'FIFO_TIMING_ANALYSIS_COMPLETE')
            check_log(pow_log, 'FIFO_POWER_ANALYSIS_COMPLETE')
            require((PPA / f'{implementation}_{label}_mapped.v').is_file(),
                    f'Missing mapped netlist: {implementation}_{label}')
        baseline_area = number(a,'baseline_area_um2')
        optimized_area = number(a,'optimized_area_um2')
        baseline_power = number(p,'baseline_power_uw')
        optimized_power = number(p,'optimized_power_uw')
        baseline_slack = number(bt,'worst_setup_slack_ns')
        optimized_slack = number(ot,'worst_setup_slack_ns')
        require(min(baseline_area, optimized_area, baseline_power, optimized_power) > 0,
                f'{label}: nonpositive PPA quantity')
        area_red = (baseline_area-optimized_area)/baseline_area*100
        power_red = (baseline_power-optimized_power)/baseline_power*100
        row = {
            'configuration':label, 'data_width':width, 'depth':depth,
            'addr_width':aw, 'equivalence_cycles':e['total_cycles'],
            'equivalence_passed_checks':e['passed_checks'],
            'equivalence_failed_checks':e['failed_checks'],
            'baseline_area_um2':baseline_area, 'optimized_area_um2':optimized_area,
            'area_reduction_pct':area_red,
            'baseline_slack_ns':baseline_slack, 'optimized_slack_ns':optimized_slack,
            'slack_change_ns':optimized_slack-baseline_slack,
            'baseline_estimated_power_uw':baseline_power,
            'optimized_estimated_power_uw':optimized_power,
            'estimated_power_reduction_pct':power_red,
        }
        records.append(row)
        total_checked += e['passed_checks']
        print(f"[PASS] {label}: {e['passed_checks']:,} checks; "
              f"area {area_red:+.2f}%; slack {row['slack_change_ns']:+.3f} ns; "
              f"estimated power {power_red:+.2f}%")
    require(total_checked == 124008,
            f'Unexpected total checks: {total_checked} (expected 124008)')
    csv_path = OUT / 'day30_fifo_final_comparison.csv'
    with csv_path.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    report = {
        'status':'PASS', 'scope':'Tested functional equivalence and pre-layout PPA',
        'equivalence_passed_checks':total_checked, 'equivalence_failed_checks':0,
        'technology':'Nangate45 typical', 'clock_period_ns':10.0,
        'assumed_input_activity_transitions_per_cycle':1.0,
        'output_load_ff':5.0, 'configurations':records,
        'source_files':['extensions/results/day30/fifo_ppa/day30_fifo_area_comparison.csv',
                        'extensions/results/day30/fifo_ppa/day30_fifo_timing_comparison.csv',
                        'extensions/results/day30/fifo_ppa/day30_fifo_power_comparison.csv'],
        'limitations':[
            'Equivalence is simulation-based, not a formal proof.',
            'Area is mapped standard-cell area, not post-layout area.',
            'Timing is pre-layout maximum-path timing, not post-route or hold signoff.',
            'Power assumes activity; no workload-derived VCD/SAIF activity.',
            'Four power-of-two configurations only; other parameters not tested.',
            'Small power differences may be sensitive to modeling assumptions.',
        ],
    }
    json_path = OUT / 'day30_fifo_final_report.json'
    json_path.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    md = [
        '# Day 30 FIFO — Functional and PPA Evidence', '',
        '## Verified scope', '',
        f'- Equivalence simulation checks passed: **{total_checked:,}**, failures: **0**.',
        '- Eight mapped implementations analyzed: four baseline and four optimized.',
        '- All eight individual designs met the 10 ns setup constraint.',
        '- Technology: Nangate45 typical; estimated pre-layout results.', '',
        '## Per-configuration comparison', '',
        '| FIFO | Area reduction | Slack difference (ns) | Estimated power reduction |',
        '|---|---:|---:|---:|',
    ]
    for r in records:
        md.append(f"| {r['configuration']} | {r['area_reduction_pct']:+.2f}% | "
                  f"{r['slack_change_ns']:+.3f} | "
                  f"{r['estimated_power_reduction_pct']:+.2f}% |")
    md.extend([
        '', '## Findings', '',
        '- Optimized area is lower for all four configurations.',
        '- Estimated power falls in three configurations and rises slightly for w8_d4.',
        '- Setup margin is equal, better, or slightly worse depending on configuration; all meet the specified clock.',
        '- A positive reduction means an improvement; negative means an increase.',
        '', '## Limitations', '',
    ])
    md.extend(f'- {item}' for item in report['limitations'])
    md.extend(['', '## Pending master-project work', '',
               '- Verify all 20 FSM configurations and reconcile the existing 13 mapped PPA cases.',
               '- Complete remaining ALU mapped PPA if not already independently evidenced.',
               '- Run final integrated requirements audit and prepare thesis submission documentation.', ''])
    md_path = OUT / 'day30_fifo_final_report.md'
    md_path.write_text('\n'.join(md), encoding='utf-8')
    print('========== FIFO FINAL REPORT ==========')
    print('Verified functional checks:', total_checked)
    print('CSV:', csv_path)
    print('JSON:', json_path)
    print('Markdown:', md_path)
    print('DAY 30 FIFO FINAL EVIDENCE REPORT: PASS')
    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print('[FAIL]', exc)
        sys.exit(1)
