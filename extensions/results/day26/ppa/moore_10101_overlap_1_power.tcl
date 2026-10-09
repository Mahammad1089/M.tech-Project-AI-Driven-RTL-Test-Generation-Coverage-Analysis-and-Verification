read_liberty extensions/technology/nangate45/NangateOpenCellLibrary_typical.lib
read_verilog extensions/results/day26/ppa/moore_10101_overlap_1_mapped.v
link_design fsm_moore_ext

create_clock -name fsm_clk -period 10.0 [get_ports clk]

set_input_delay 0.2 -clock fsm_clk [get_ports din]
set_output_delay 0.2 -clock fsm_clk [get_ports detected]

set_false_path -from [get_ports rst]

puts "========== FSM POWER ANALYSIS =========="
puts "Configuration: moore_10101_overlap_1"
puts "Top module: fsm_moore_ext"
puts "Activity: 0.1 transitions/ns"
puts "Duty cycle: 0.5"

set_power_activity -global -activity 0.1 -duty 0.5

report_power

puts "========== POWER ANALYSIS COMPLETED =========="
