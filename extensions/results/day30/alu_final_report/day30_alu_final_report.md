# Day 30 — Final ALU PPA Report

## Functional verification

Original and optimized ALUs passed
**2048/2048 equivalence checks**.

## Technology-mapped PPA

| Metric | Original | Optimized |
|---|---:|---:|
| Cell area (µm²) | 68.096 | 59.052 |
| Cell count | 62 | 51 |
| Setup slack (ns) | 9.290 | 9.340 |
| Minimum-path slack (ns) | 0.410 | 0.410 |
| Estimated power (µW) | 6.950 | 5.860 |

## Optimization results

- Cell area reduction: **13.28%**
- Estimated power reduction: **15.68%**
- Setup slack improvement: **50 ps**
- Mapped cell count reduction: **11**

## Evaluation conditions

- Library: Nangate45 typical
- Analysis: technology-mapped, pre-layout
- Virtual clock: 10 ns
- Input/output delays: 0.2 ns
- SDC load: 0.005
- Library capacitance unit: 1 ff
- Assumed input activity: 0.1 transitions/ns
- Duty cycle: 0.5

## Conclusion

The optimized ALU maintains functional equivalence
while reducing mapped cell area and estimated power.
Both designs meet the evaluated setup constraints.

These are pre-layout estimates, not physical
implementation or measured silicon results.
