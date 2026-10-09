# Day 30 UART Verification and PPA Report

## Functional verification

All audited UART TX equivalence, RX equivalence, and hybrid loopback logs passed.

Total checked assertions/comparisons: **1,845,552**

The hybrid loopback passed at CPB = 8, 16, 32 and 64.

## Technology-mapped PPA

| Architecture | Area (um²) | Estimated power (uW) |
|---|---:|---:|
| baseline | 450.604 | 370.282 |
| fully_optimized | 440.230 | 392.761 |
| hybrid | 425.600 | 366.547 |

## Hybrid versus baseline

- Mapped area reduction: **5.55%**
- Estimated power reduction: **1.01%**
- Individually analyzed TX and RX blocks met setup timing.

## Selected architecture

**Baseline UART TX + optimized UART RX** is the provisional area/power-preferred architecture.

## Limitations

- Power assumes input switching activity and is not waveform-derived.
- Combined PPA is calculated from separately analyzed blocks.
- Integrated STA and post-layout analysis are not performed.
- Functional tests do not constitute formal equivalence proof.

## Project status

UART functional and pre-layout PPA comparison: completed.

Optimized FIFO, full FSM configuration evidence, and the integrated project audit: pending.
