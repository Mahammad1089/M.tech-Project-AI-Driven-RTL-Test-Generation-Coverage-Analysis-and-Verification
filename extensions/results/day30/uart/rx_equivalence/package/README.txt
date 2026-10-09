Day 30 UART Step 4C — receiver optimization candidate.

uart_rx_opt.v                  Shift-register RX candidate; baseline untouched.
tb_day30_uart_rx_equivalence.v Cycle-by-cycle external output comparison
                                  and independent 256-byte functional checks.

IMPORTANT:
- This package has not been verified by Icarus Verilog in the user's WSL.
- A simulation PASS is not a PPA improvement.
- Use CPB 8,16,32,64, and keep independent run logs.
- Stop on failures, report exact error messages.
