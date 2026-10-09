
read_liberty /home/maham_mtech/Mtech_project/AI_RTL_Verification/extensions/technology/nangate45/NangateOpenCellLibrary_typical.lib
read_verilog /home/maham_mtech/Mtech_project/AI_RTL_Verification/extensions/results/day30/uart/ppa/baseline_rx_mapped.v
link_design uart_rx

create_clock -name uart_clk -period 10.0 [get_ports clk]

set_load 5.0 [all_outputs]

# One assumed transition per 10 ns clock cycle.
# This is 0.1 transitions/ns for the input signals.
set_power_activity -input -activity 1.0 -duty 0.5

# Treat synchronous reset as inactive in steady-state operation.
set_power_activity -input_ports [get_ports rst] -activity 0.0 -duty 0.0

puts "UART_POWER_REPORT_BEGIN"
report_power -digits 6
puts "UART_POWER_REPORT_END"
puts "UART_POWER_ANALYSIS_COMPLETE"
