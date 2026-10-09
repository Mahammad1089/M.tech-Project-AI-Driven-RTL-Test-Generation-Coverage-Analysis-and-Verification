# Day 30 — Complete FSM architecture and PPA comparison

## Verification summary

- Extended FSM implementations: **20/20**
- Matched Mealy/Moore comparisons: **10/10**
- Pareto comparison records: **20/20**
- Original `fsm_original_1011`: preserved as separate historical reference

## Matched Mealy/Moore pairs

| Pattern | Overlap | Mealy area | Moore area | Moore area change | Mealy power | Moore power | Moore power change |
|---|---:|---:|---:|---:|---:|---:|---:|
| `1011` | 0 | 32.452 | 24.738 | -23.77% | 5.300 | 4.000 | -24.53% |
| `1011` | 1 | 30.324 | 23.940 | -21.05% | 5.170 | 3.950 | -23.60% |
| `1101` | 0 | 29.526 | 28.196 | -4.50% | 5.020 | 4.390 | -12.55% |
| `1101` | 1 | 31.920 | 26.600 | -16.67% | 5.260 | 4.260 | -19.01% |
| `1001` | 0 | 28.728 | 24.738 | -13.89% | 4.920 | 4.140 | -15.85% |
| `1001` | 1 | 27.930 | 23.674 | -15.24% | 4.870 | 3.930 | -19.30% |
| `10101` | 0 | 38.304 | 25.536 | -33.33% | 6.550 | 4.260 | -34.96% |
| `10101` | 1 | 41.762 | 31.388 | -24.84% | 6.930 | 4.710 | -32.03% |
| `1110` | 0 | 29.526 | 21.812 | -26.13% | 4.990 | 3.720 | -25.45% |
| `1110` | 1 | 30.058 | 21.812 | -27.43% | 5.020 | 3.720 | -25.90% |

Values: cell area in µm² and estimated power in µW.

## Pareto analysis

Criteria: lower mapped area, lower estimated total power, lower reported data arrival.
Exploratory global Pareto members: **2** / 20.
Controlled matched-pair Pareto members: **14** / 20.
The controlled comparisons (same pattern, same overlap) are the appropriate architecture comparison.
Global Pareto mixes functionally different pattern/mode choices and must not be used to recommend a substitute detector.

## Historical methodology

- Arrival-based ADP = mapped area × reported arrival, µm²·ns.
- Arrival-based PDP = estimated power × reported arrival, fJ.
- Area-power product = mapped area × estimated power, µm²·µW.
- Signed percentage change = 100 × (Moore − Mealy) / Mealy.

## Limitations

- Technology-mapped pre-layout results, no parasitics or die area
- Power estimated from assumed switching activity (not waveform/silicon power)
- Reported data arrival is not necessarily intrinsic combinational delay
- Mealy and Moore output event timing can differ; PPA does not establish cycle equivalence
- Only same-pattern/same-overlap Mealy–Moore comparisons are controlled
- Global Pareto across different patterns and overlap settings is exploratory only
- Reported power/area/arrival optimization not equivalent to functional quality

**DAY 30 FSM 20-CONFIGURATION COMPARISON: PASS**
