# ============================================================
# AI-DRIVEN RTL VERIFICATION
# DAY 25 - ALU STATIC TIMING ANALYSIS
# OpenSTA-compatible Tcl script
# ============================================================

# Get configuration from environment variables.
# This avoids unsupported OpenSTA positional arguments.

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

set lib     $::env(ALU_STA_LIB)
set netlist $::env(ALU_STA_NETLIST)
set top     $::env(ALU_STA_TOP)
set sdc     $::env(ALU_STA_SDC)

# Verify required files.

foreach file [list $lib $netlist $sdc] {
    if {![file exists $file]} {
        puts stderr "ERROR: Missing input file: $file"
        exit 1
    }
}

puts "============================================"
puts "ALU STATIC TIMING ANALYSIS"
puts "============================================"

puts "Top module: $top"
puts "Liberty: $lib"
puts "Netlist: $netlist"
puts "SDC: $sdc"

# ------------------------------------------------------------
# Load technology library
# ------------------------------------------------------------

puts "Loading Liberty library..."

if {[catch {read_liberty $lib} result]} {
    puts stderr "ERROR: Liberty loading failed: $result"
    exit 1
}

# ------------------------------------------------------------
# Load synthesized mapped netlist
# ------------------------------------------------------------

puts "Loading mapped netlist..."

if {[catch {read_verilog $netlist} result]} {
    puts stderr "ERROR: Netlist loading failed: $result"
    exit 1
}

# ------------------------------------------------------------
# Link design
# ------------------------------------------------------------

puts "Linking design..."

if {[catch {link_design $top} result]} {
    puts stderr "ERROR: Design linking failed: $result"
    exit 1
}

# ------------------------------------------------------------
# Read timing constraints
# ------------------------------------------------------------

puts "Loading timing constraints..."

if {[catch {read_sdc $sdc} result]} {
    puts stderr "ERROR: Timing constraints failed: $result"
    exit 1
}

# ------------------------------------------------------------
# Maximum delay analysis
# ------------------------------------------------------------

puts ""
puts "========== MAXIMUM DELAY PATHS =========="

if {[catch {
    report_checks -path_delay max
} result]} {
    puts stderr "ERROR: Maximum delay analysis failed: $result"
    exit 1
}

# ------------------------------------------------------------
# Minimum delay analysis
# ------------------------------------------------------------

puts ""
puts "========== MINIMUM DELAY PATHS =========="

if {[catch {
    report_checks -path_delay min
} result]} {
    puts stderr "ERROR: Minimum delay analysis failed: $result"
    exit 1
}

# ------------------------------------------------------------
# Completion
# ------------------------------------------------------------

puts ""
puts "========== TIMING CHECK COMPLETE =========="
puts "Top module: $top"
puts "Status: OpenSTA commands executed successfully"
puts "==========================================="
