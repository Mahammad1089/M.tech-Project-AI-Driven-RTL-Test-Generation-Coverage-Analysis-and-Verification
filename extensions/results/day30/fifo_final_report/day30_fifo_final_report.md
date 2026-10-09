# Day 30 FIFO — Functional and PPA Evidence

## Verified scope

- Equivalence simulation checks passed: **124,008**, failures: **0**.
- Eight mapped implementations analyzed: four baseline and four optimized.
- All eight individual designs met the 10 ns setup constraint.
- Technology: Nangate45 typical; estimated pre-layout results.

## Per-configuration comparison

| FIFO | Area reduction | Slack difference (ns) | Estimated power reduction |
|---|---:|---:|---:|
| w8_d4 | +1.33% | +0.000 | -0.09% |
| w8_d8 | +1.17% | +0.020 | +7.64% |
| w16_d4 | +0.82% | -0.010 | +0.04% |
| w8_d16 | +0.30% | +0.030 | +4.08% |

## Findings

- Optimized area is lower for all four configurations.
- Estimated power falls in three configurations and rises slightly for w8_d4.
- Setup margin is equal, better, or slightly worse depending on configuration; all meet the specified clock.
- A positive reduction means an improvement; negative means an increase.

## Limitations

- Equivalence is simulation-based, not a formal proof.
- Area is mapped standard-cell area, not post-layout area.
- Timing is pre-layout maximum-path timing, not post-route or hold signoff.
- Power assumes activity; no workload-derived VCD/SAIF activity.
- Four power-of-two configurations only; other parameters not tested.
- Small power differences may be sensitive to modeling assumptions.

## Pending master-project work

- Verify all 20 FSM configurations and reconcile the existing 13 mapped PPA cases.
- Complete remaining ALU mapped PPA if not already independently evidenced.
- Run final integrated requirements audit and prepare thesis submission documentation.
