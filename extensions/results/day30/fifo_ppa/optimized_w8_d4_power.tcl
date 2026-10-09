
read_liberty /home/maham_mtech/Mtech_project/AI_RTL_Verification/extensions/technology/nangate45/NangateOpenCellLibrary_typical.lib
read_verilog /home/maham_mtech/Mtech_project/AI_RTL_Verification/extensions/results/day30/fifo_ppa/optimized_w8_d4_mapped.v
link_design fifo_opt

create_clock -name fifo_clk -period 10.0 [get_ports clk]

set_load 5.0 [all_outputs]

# Assumed input activity:
# 1 transition/clock cycle = 0.1 transitions/ns.
set_power_activity -input -activity 1.0 -duty 0.5

# Reset is considered inactive during steady-state operation.
set_power_activity -input_ports [get_ports rst] -activity 0.0 -duty 0.0

puts "FIFO_POWER_REPORT_BEGIN"
report_power -digits 6
puts "FIFO_POWER_REPORT_END"
puts "FIFO_POWER_ANALYSIS_COMPLETE"
