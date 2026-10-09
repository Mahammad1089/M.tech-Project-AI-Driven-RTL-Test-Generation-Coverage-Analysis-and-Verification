read_liberty extensions/technology/nangate45/NangateOpenCellLibrary_typical.lib
read_verilog extensions/results/day26/ppa/mealy_1011_overlap_0_mapped.v
link_design fsm_mealy_ext

create_clock -name fsm_clk -period 10.0 [get_ports clk]

set_input_delay 0.2 -clock fsm_clk [get_ports din]
set_output_delay 0.2 -clock fsm_clk [get_ports detected]

# Reset is excluded from ordinary synchronous data-path analysis.
set_false_path -from [get_ports rst]

puts "========== CASE: mealy_1011_overlap_0 =========="
puts "========== MAXIMUM TIMING PATHS =========="
report_checks -path_delay max -group_count 10

puts "========== MINIMUM TIMING PATHS =========="
report_checks -path_delay min -group_count 10

puts "========== TIMING ANALYSIS COMPLETED =========="
