create_clock -name virtual_clk -period 10

set_input_delay 0.2 -clock virtual_clk [all_inputs]
set_output_delay 0.2 -clock virtual_clk [all_outputs]

set_load 0.005 [all_outputs]
