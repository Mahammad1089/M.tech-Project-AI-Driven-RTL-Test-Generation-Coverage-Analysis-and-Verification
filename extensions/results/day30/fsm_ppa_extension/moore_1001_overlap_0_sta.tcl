
read_liberty extensions/technology/nangate45/NangateOpenCellLibrary_typical.lib
read_verilog extensions/results/day30/fsm_ppa_extension/moore_1001_overlap_0_mapped.v
link_design fsm_moore_ext
create_clock -name fsm_clk -period 10.0 [get_ports clk]
set_input_delay 0.2 -clock fsm_clk [get_ports din]
set_output_delay 0.2 -clock fsm_clk [get_ports detected]
set_false_path -from [get_ports rst]
puts "MAXIMUM_TIMING_PATHS_BEGIN"
report_checks -path_delay max -group_count 10
puts "MAXIMUM_TIMING_PATHS_END"
puts "MINIMUM_TIMING_PATHS_BEGIN"
report_checks -path_delay min -group_count 10
puts "MINIMUM_TIMING_PATHS_END"
puts "TIMING ANALYSIS COMPLETED"
