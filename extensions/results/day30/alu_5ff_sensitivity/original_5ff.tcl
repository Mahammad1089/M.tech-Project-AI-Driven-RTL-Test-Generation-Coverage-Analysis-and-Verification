
read_liberty /home/maham_mtech/Mtech_project/AI_RTL_Verification/extensions/technology/nangate45/NangateOpenCellLibrary_typical.lib
read_verilog /home/maham_mtech/Mtech_project/AI_RTL_Verification/extensions/results/day25/ppa/original_mapped.v
link_design alu

create_clock -name virtual_clk -period 10.0

set_input_delay 0.2 -clock virtual_clk [all_inputs]
set_output_delay 0.2 -clock virtual_clk [all_outputs]

set_load 5.0 [all_outputs]

puts "========== MAXIMUM DELAY PATHS =========="
report_checks -path_delay max

puts "========== MINIMUM DELAY PATHS =========="
report_checks -path_delay min

set_power_activity -input -activity 0.1 -duty 0.5

puts "========== POWER REPORT =========="
report_power

puts "========== 5FF ANALYSIS COMPLETED =========="
