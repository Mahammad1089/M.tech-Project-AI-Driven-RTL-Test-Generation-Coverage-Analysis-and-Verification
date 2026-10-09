
read_liberty extensions/technology/nangate45/NangateOpenCellLibrary_typical.lib
read_verilog extensions/results/day30/fsm_ppa_extension/mealy_1110_overlap_0_mapped.v
link_design fsm_mealy_ext
create_clock -name fsm_clk -period 10.0 [get_ports clk]
set_input_delay 0.2 -clock fsm_clk [get_ports din]
set_output_delay 0.2 -clock fsm_clk [get_ports detected]
set_false_path -from [get_ports rst]
puts "FSM POWER ANALYSIS"
puts "Activity setting: set_power_activity -global -activity 0.1 -duty 0.5"
set_power_activity -global -activity 0.1 -duty 0.5
puts "POWER_REPORT_BEGIN"
report_power
puts "POWER_REPORT_END"
puts "POWER ANALYSIS COMPLETED"
