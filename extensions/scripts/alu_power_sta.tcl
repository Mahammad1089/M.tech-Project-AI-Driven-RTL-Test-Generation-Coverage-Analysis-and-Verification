# ALU Power Analysis - OpenSTA 2.0.17

foreach name {
    ALU_STA_LIB
    ALU_STA_NETLIST
    ALU_STA_TOP
    ALU_STA_SDC
} {
    if {![info exists ::env($name)]} {
        puts stderr "ERROR: Missing environment variable $name"
        exit 1
    }
}

set lib $::env(ALU_STA_LIB)
set netlist $::env(ALU_STA_NETLIST)
set top $::env(ALU_STA_TOP)
set sdc $::env(ALU_STA_SDC)

foreach file [list $lib $netlist $sdc] {
    if {![file exists $file]} {
        puts stderr "ERROR: Missing file: $file"
        exit 1
    }
}

puts "========== ALU POWER ANALYSIS =========="
puts "Top module: $top"

if {[catch {
    read_liberty $lib
    read_verilog $netlist
    link_design $top
    read_sdc $sdc
} result]} {
    puts stderr "ERROR: Design setup failed: $result"
    exit 1
}

puts "========== SWITCHING ASSUMPTIONS =========="
puts "Activity: 0.1 transitions/ns"
puts "Duty cycle: 0.5"

if {[catch {
    set_power_activity -input -activity 0.1 -duty 0.5
} result]} {
    puts stderr "ERROR: Switching activity setup failed: $result"
    exit 1
}

puts "========== POWER REPORT =========="

if {[catch {
    report_power
} result]} {
    puts stderr "ERROR: Power reporting failed: $result"
    exit 1
}

puts "========== POWER ANALYSIS COMPLETED =========="
