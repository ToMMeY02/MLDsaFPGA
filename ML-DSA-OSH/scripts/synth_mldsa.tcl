# ML-DSA-OSH synthesis + implementation (single run: security level and operation are selected at runtime by
# the inputs sec_lvl / mode of combined_top, so ONE run covers ML-DSA-44/65/87 and KeyGen/Sign/Verify).
# env: PART (default xczu5ev-sfvc784-2-e; use xczu7ev-2ffvc1156-2-e for the ZCU104 if your Vivado has that device)
#      CLK_NS (default 4.35)  RPT_DIR  RUN_DIR  STAGE (synth|impl)
proc env_or {n d} { if {[info exists ::env($n)]} {return $::env($n)} else {return $d} }
set PART [env_or PART xczu5ev-sfvc784-2-e]
set CLK  [env_or CLK_NS 4.35]
set W    [file normalize [file dirname [info script]]]      ;# ML-DSA-OSH/scripts
set SRC  [file normalize $W/..]                              ;# ML-DSA-OSH
set RPT  [env_or RPT_DIR [file normalize $W/../../reports/raw]]
set RUN  [env_or RUN_DIR [file normalize $W/../../build/vivado_run]]   ;# git-ignored
set STAGE [env_or STAGE impl]                                ;# synth | impl
file mkdir $RPT
if {[llength [get_parts $PART]] == 0} { puts "ERROR: part $PART not installed"; exit 1 }
file delete -force $RUN
create_project mldsa $RUN -part $PART
foreach f [glob $SRC/ref_combined/src/*.v]   { add_files -norecurse $f }
foreach f [glob $SRC/ref_combined/src/*.vhd] { add_files -norecurse $f }
add_files -norecurse $SRC/common/zetas.txt            ;# twiddle ROM content, read by $readmemh("zetas.txt")
set_property file_type {Memory Initialization Files} [get_files zetas.txt]
set_property top combined_top [current_fileset]
update_compile_order -fileset sources_1
puts "TOP: [get_property top [current_fileset]]"
set xdc $RUN/clk.xdc
set fh [open $xdc w]; puts $fh "create_clock -period $CLK -name clk \[get_ports clk\]"; close $fh
add_files -fileset constrs_1 -norecurse $xdc
set_property -name {STEPS.SYNTH_DESIGN.ARGS.MORE OPTIONS} -value {-mode out_of_context} -objects [get_runs synth_1]
launch_runs synth_1 -jobs 4
wait_on_run synth_1
if {[get_property PROGRESS [get_runs synth_1]] != "100%"} { puts "ERROR: synthesis failed"; exit 1 }
open_run synth_1 -name synth_1
report_utilization -file $RPT/util_synth.rpt
report_utilization -hierarchical -hierarchical_depth 2 -file $RPT/util_synth_hier.rpt
report_timing_summary -file $RPT/timing_synth.rpt
if {$STAGE eq "synth"} { puts "MLDSA-DONE (synthesis only)"; exit 0 }
launch_runs impl_1 -jobs 4
wait_on_run impl_1
if {[get_property PROGRESS [get_runs impl_1]] != "100%"} { puts "WARNING: implementation failed, synthesis results only"; exit 0 }
open_run impl_1
report_utilization -file $RPT/util_impl.rpt
report_utilization -hierarchical -hierarchical_depth 2 -file $RPT/util_impl_hier.rpt
report_timing_summary -max_paths 10 -file $RPT/timing_impl.rpt
report_power -file $RPT/power_impl.rpt
puts "MLDSA-DONE"
