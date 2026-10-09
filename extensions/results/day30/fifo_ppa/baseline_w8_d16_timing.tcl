read_liberty /home/maham_mtech/Mtech_project/AI_RTL_Verification/extensions/technology/nangate45/NangateOpenCellLibrary_typical.lib
read_verilog /home/maham_mtech/Mtech_project/AI_RTL_Verification/extensions/results/day30/fifo_ppa/baseline_w8_d16_mapped.v
link_design fifo

create_clock -name fifo_clk -period 10.0 [get_ports clk]

set_input_delay 0.2 -clock fifo_clk [get_ports {rst}]
set_input_transition 0.05 [get_ports {rst}]
set_input_delay 0.2 -clock fifo_clk [get_ports {wr_en}]
set_input_transition 0.05 [get_ports {wr_en}]
set_input_delay 0.2 -clock fifo_clk [get_ports {rd_en}]
set_input_transition 0.05 [get_ports {rd_en}]
set_input_delay 0.2 -clock fifo_clk [get_ports {data_in*}]
set_input_transition 0.05 [get_ports {data_in*}]

set_output_delay 0.2 -clock fifo_clk [all_outputs]
set_load 5.0 [all_outputs]

puts "FIFO_MAX_PATHS_BEGIN"
report_checks -path_delay max -group_count 20
puts "FIFO_MAX_PATHS_END"
puts "FIFO_TIMING_ANALYSIS_COMPLETE"
