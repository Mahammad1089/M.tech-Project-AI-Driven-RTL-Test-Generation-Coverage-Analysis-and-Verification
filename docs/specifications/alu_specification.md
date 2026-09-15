# 4-Bit ALU Functional Specification

Module:
alu

Inputs:
a[3:0]
b[3:0]
sel[2:0]

Output:
y[3:0]

Operation Mapping:

000 : ADD
001 : SUB
010 : AND
011 : OR
100 : XOR
101 : NOT A
110 : SHIFT LEFT A
111 : SHIFT RIGHT A

Design Type:
Combinational

Clock:
None

Reset:
None

Output Width:
4 bits
