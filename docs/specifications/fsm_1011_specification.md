# 1011 Sequence Detector Specification

## DUT

fsm_1011

## Design Type

Sequential finite state machine.

## Sequence

1011

## Detection Type

Overlapping sequence detection.

## Inputs

clk   - clock
rst   - active-high synchronous reset
din   - serial input bit

## Output

detected - asserted for one clock cycle when 1011 is detected

## States

IDLE
S1
S10
S101

## State Meaning

IDLE:
No useful prefix currently matched.

S1:
Prefix 1 has been matched.

S10:
Prefix 10 has been matched.

S101:
Prefix 101 has been matched.

## State Transitions

IDLE + 0 -> IDLE
IDLE + 1 -> S1

S1 + 0 -> S10
S1 + 1 -> S1

S10 + 0 -> IDLE
S10 + 1 -> S101

S101 + 0 -> S10
S101 + 1 -> S1 and detected = 1

## Reset

rst = 1 forces the FSM to IDLE.

## Implementation

Verilog RTL only.

## Verification

Simulation only.

## Hardware Requirement

None.

## Day-16 Goal

Implement and establish deterministic baseline
verification of the FSM.

State and transition coverage are handled on Day 17.
