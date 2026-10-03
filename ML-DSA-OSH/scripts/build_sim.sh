#!/bin/bash
# Compile and elaborate the ML-DSA-OSH testbenches with xsim (originals untouched; a patched COPY of combined_top.v is used).
# Usage: ML-DSA-OSH/scripts/build_sim.sh [keygen|sign|verify ...]   -> runs the chosen testbenches (default: all), writes build/sim/run_<op>.log and prints the cycle averages.
set -e
cd "$(dirname "$0")/.."
O=$(pwd); mkdir -p ../build/sim; cd ../build/sim        # work in build/ (git-ignored)
source ${XILINX_ROOT:-/tools/Xilinx}/Vivado/${XILINX_VER:-2024.2}/settings64.sh
S=$O/ref_combined/src; TB=$O/ref_combined/src_tb
cp $O/KAT/*.txt $O/common/zetas.txt .             # KAT files and twiddle ROM content are read from the working directory
rm -rf xsim.dir src_sim; mkdir -p src_sim
# xsim needs declarations before use; Vivado synthesis does not. Move such declarations to the top of the module (copy only).
S=$S python3 - <<'PY'
import re, os, subprocess
import os; S=os.environ["S"]; p="src_sim/combined_top.v"
t=open(f"{S}/combined_top.v").read(); open(p,"w").write(t)
others=[f"{S}/{f}" for f in sorted(os.listdir(S)) if f.endswith(".v") and f!="combined_top.v"]
for it in range(40):
    r=subprocess.run(["xvlog"]+others+[p],capture_output=True,text=True).stdout
    ids=sorted(set(re.findall(r"identifier '(\w+)' is used before its declaration",r)))
    if not ids: break
    t=open(p).read()
    for i in ids:
        m=re.search(r"^[ \t]*((?:reg|wire)(?:\s+signed)?(?:\s*\[[^\]]+\])?\s+%s(?:\s*=[^;]*)?;)[ \t]*\n"%i,t,re.M)
        if not m: raise SystemExit("cannot move declaration of "+i)
        t=t[:m.start()]+t[m.end():]
        j=t.index("output reg [W-1:0] data_o = 0"); j=t.index(");",j)+2
        t=t[:j]+"\n    "+m.group(1)+" // moved for xsim"+t[j:]
    open(p,"w").write(t)
PY
# VHDL: explicit dependency order (packages, leaves, FSMs, then the units that instantiate them)
V="keccak_pkg sha3_pkg regn countern sr_reg piso sipo keccak_cons keccak_round keccak_bytepad keccak_fsm1 keccak_fsm2 sha3_fsm3 keccak_datapath keccak_control keccak_top"
xvhdl $(for f in $V; do echo $S/$f.vhd; done) > xvhdl.log 2>&1
xvlog $(ls $S/*.v | grep -v combined_top.v) src_sim/combined_top.v $TB/tb_keygen_top.v $TB/tb_sign_top.v $TB/tb_verify_top.v > xvlog.log 2>&1
for t in ${@:-keygen sign verify}; do
  xelab -debug off -timescale 1ns/1ps tb_${t}_top -s s_$t > xelab_$t.log 2>&1
  xsim s_$t -runall > run_$t.log 2>&1
  echo "== $t: WRONG=$(grep -c WRONG run_$t.log)"; grep -E "avg\." run_$t.log | sed 's/  */ /g'
done
