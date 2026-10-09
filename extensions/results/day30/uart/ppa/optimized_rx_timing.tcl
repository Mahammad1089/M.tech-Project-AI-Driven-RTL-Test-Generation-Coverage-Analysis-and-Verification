read_liberty /home/maham_mtech/Mtech_project/AI_RTL_Verification/extensions/technology/nangate45/NangateOpenCellLibrary_typical.lib
read_verilog /home/maham_mtech/Mtech_project/AI_RTL_Verification/extensions/results/day30/uart/ppa/optimized_rx_mapped.v
link_design uart_rx_opt

create_clock -name uart_clk -period 10.0 [get_ports clk]

set_input_delay 0.2 -clock uart_clk [get_ports {rst}]
set_input_transition 0.05 [get_ports {rst}]
set_input_delay 0.2 -clock uart_clk [get_ports {rx}]
set_input_transition 0.05 [get_ports {rx}]

set_output_delay 0.2 -clock uart_clk [all_outputs]
set_load 5.0 [all_outputs]

puts "UART_MAX_PATHS_BEGIN"
report_checks -path_delay max -group_count 20
puts "UART_MAX_PATHS_END"
puts "UART_TIMING_ANALYSIS_COMPLETE"
