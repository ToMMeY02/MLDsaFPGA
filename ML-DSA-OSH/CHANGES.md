# Changes relative to the original ML-DSA-OSH

- **Original source:** <https://github.com/KULeuven-COSIC/ML-DSA-OSH>, commit `7510091` ("initial commit sources").
- **Reference paper:** ML-DSA-OSH, DATE 2026 (KU Leuven COSIC), as given in the task description. The full title and the paper's numbers were **not verified**: the `CITATION` file of the upstream repository is empty.

## Modified files

**No changes — used as-is.** Everything under `ref_combined/` (RTL in `src/`, testbenches in `src_tb/`), `common/`, `KAT/`, `LICENSE` and `NOTICE` is byte-identical to the upstream commit above (checked with `diff` against an unmodified clone of that commit). The upstream directory layout is kept on purpose, because the upstream testbenches include `../../common/mldsa_params.v` by relative path.

## Added files (not part of the original)

| File | Purpose |
|---|---|
| `scripts/synth_mldsa.tcl` | Vivado 2024.2 batch synthesis + implementation of `combined_top` (out-of-context, 4.35 ns clock constraint). The upstream repository ships no TCL script. The device is selected with `PART`. |
| `scripts/build_sim.sh` | Compiles and runs the three upstream testbenches with xsim and prints the cycle averages (see workarounds below). |

## Workarounds applied (simulation only; nothing is committed that differs from upstream)

- **Signals used before their declaration.** xsim rejects `combined_top.v` because `a_generated`, `a_generated_during` and `op_done_ntty` are declared after their first use; Vivado synthesis accepts it. `build_sim.sh` builds a **copy** of the file (`build/sim/src_sim/combined_top.v`) in which those declarations are moved to the top of the module. The logic is unchanged; the synthesis flow uses the original file.
- **VHDL compile order.** The Keccak VHDL files must be compiled in dependency order for xsim (packages, leaf units, the three FSMs, then `keccak_control`); alphabetical order fails.
- **Working directory.** The testbenches read the KAT files and `zetas.txt` with `$readmemh` from the current directory, so the script copies them there. For synthesis, `zetas.txt` is added to the Vivado project as a memory initialization file (Vivado reports "$readmem data file 'zetas.txt' is read successfully").

## Bugs found

None in the RTL for the tested vectors: all 75 KeyGen, 45 Sign and 45 Verify KAT vectors of the upstream testbenches pass with 0 mismatch. The two portability points above are tool-strictness issues, not functional bugs.

## Device note

The measurements were made for `xczu5ev-sfvc784-2-e`, **not** for the ZCU104 device (`xczu7ev-2ffvc1156-2-e`), which is not installed in the Vivado that was used. The script takes the device from the `PART` variable.
