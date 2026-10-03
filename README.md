# ML-DSA FPGA — Post-Quantum Cryptography Hardware Implementation

## Overview

**ML-DSA** is the lattice-based digital signature scheme standardized by NIST in **FIPS 204** (August 2024). It is the standardized form of **CRYSTALS-Dilithium** and comes in three parameter sets: ML-DSA-44 (NIST security level II), ML-DSA-65 (level III) and ML-DSA-87 (level V).

This repository benchmarks the **ML-DSA-OSH** hardware implementation from KU Leuven COSIC (Verilog/VHDL) with Vivado 2024.2: FPGA resource usage, achievable clock frequency, and cycle counts for key generation, signing and verification, with the outputs checked against NIST test vectors.

> **Read this first.** The intended target was the ZCU104, but its device (XCZU7EV) is **not installed** in the Vivado used for this work, so everything below was **measured on an XCZU5EV** (same Zynq UltraScale+ family and speed grade, smaller device). Numbers for the XCZU7EV would differ. See *Hardware Target*.

## Hardware Target

- **Intended board:** ZCU104 Evaluation Kit, device **XCZU7EV-2FFVC1156** (Zynq UltraScale+ MPSoC). PL resources: 230K LUTs, 461K FFs, 312 BRAMs, 1,728 DSPs.
- **Device actually used for all measurements:** **xczu5ev-sfvc784-2-e** (117,120 LUTs, 234,240 FFs, 144 BRAM36, 1,248 DSPs), because the XCZU7EV is missing from this Vivado installation (`get_parts *zu7ev*` returns nothing). The synthesis script takes the device from the `PART` variable, so you can set `PART=xczu7ev-2ffvc1156-2-e` if your Vivado has it.
- **Tool:** Vivado 2024.2 (and xsim for simulation). Nothing was run on a physical board.

## Source Repository

- **Original:** <https://github.com/KULeuven-COSIC/ML-DSA-OSH> (commit `7510091`), MIT license. The design is largely based on the Dilithium hardware of Beckwith et al. (GMU CERG, Apache-2.0).
- **Reference paper:** ML-DSA-OSH, DATE 2026 (KU Leuven COSIC), as cited in the task description. The exact title and the paper's figures were **not verified** (the upstream `CITATION` file is empty).
- **Modifications:** none to the original files; see [`ML-DSA-OSH/CHANGES.md`](ML-DSA-OSH/CHANGES.md).

## Resource Utilization Results

**One hardware instance serves every level and operation.** The design selects the security level (`sec_lvl`) and the operation (`mode`) at runtime on the same `combined_top` module, so resources and frequency are **identical** for ML-DSA-44/65/87 and for KeyGen/Sign/Verify; only the latency differs. The resource columns below therefore repeat the same measured values.

Measured once, after place and route, on xczu5ev, out-of-context, 4.35 ns clock constraint:

| LUT | FF | BRAM36 | DSP | WNS | Timing met | Est. Fmax | Est. power |
|---:|---:|---:|---:|---:|---|---:|---:|
| 56,475 (48.2 %) | 29,292 (12.5 %) | 29 (20.1 %) | 16 (1.3 %) | +0.019 ns | yes | 231 MHz | 3.19 W |

Frequency is `1000 / (4.35 ns - WNS)` for this single run (an estimate, not a searched maximum). Power is a Vivado estimate with default switching activity, not a measurement. Latencies are cycle counts from RTL simulation with the upstream testbenches (which include data transfer on a 64-bit bus), converted at 230 MHz.

### ML-DSA-44 (NIST Level II)
| Operation | LUT | FF | BRAM36 | DSP | Freq (MHz) | Latency (cycles, mean over KATs) | Latency (µs @ 230 MHz) |
|---|---:|---:|---:|---:|---:|---:|---:|
| KeyGen | 56,475 | 29,292 | 29 | 16 | 231 | 4,872 | 21.2 |
| Sign | 56,475 | 29,292 | 29 | 16 | 231 | 25,081 (min 10,970, max 53,034) | 109.0 |
| Verify | 56,475 | 29,292 | 29 | 16 | 231 | 6,634 | 28.8 |

### ML-DSA-65 (NIST Level III)
| Operation | LUT | FF | BRAM36 | DSP | Freq (MHz) | Latency (cycles, mean over KATs) | Latency (µs @ 230 MHz) |
|---|---:|---:|---:|---:|---:|---:|---:|
| KeyGen | 56,475 | 29,292 | 29 | 16 | 231 | 8,292 | 36.1 |
| Sign | 56,475 | 29,292 | 29 | 16 | 231 | 34,262 (min 16,179, max 97,833) | 149.0 |
| Verify | 56,475 | 29,292 | 29 | 16 | 231 | 9,730 | 42.3 |

### ML-DSA-87 (NIST Level V)
| Operation | LUT | FF | BRAM36 | DSP | Freq (MHz) | Latency (cycles, mean over KATs) | Latency (µs @ 230 MHz) |
|---|---:|---:|---:|---:|---:|---:|---:|
| KeyGen | 56,475 | 29,292 | 29 | 16 | 231 | 14,033 | 61.0 |
| Sign | 56,475 | 29,292 | 29 | 16 | 231 | 54,222 (min 25,672, max 108,916) | 235.7 |
| Verify | 56,475 | 29,292 | 29 | 16 | 231 | 14,643 | 63.7 |

**Functional check:** the testbenches compare the outputs with NIST ACVP test vectors: 75 KeyGen, 45 Sign and 45 Verify vectors, **0 mismatches**.

**Sign latency varies a lot** between vectors (rejection sampling), and the mean is over only 15 vectors per level, so treat it as a rough estimate. For reference, the task description quotes paper values of 54,942 LUT / 29,309 FF / 29 BRAM / 16 DSP and Sign latencies of 106 / 143 / 160 µs at 230 MHz (unverified by me): the resources agree closely, Sign-44 and Sign-65 agree within about 4 %, but Sign-87 is clearly slower here (mean 236 µs).

The full report (in French, with the per-block breakdown) is in [`reports/ml_dsa_benchmark.md`](reports/ml_dsa_benchmark.md); the raw Vivado reports and simulation logs are in `reports/raw/`.

## Known Issues

- **Device is not the ZCU104's.** All figures are for the XCZU5EV (see above).
- **No per-operation or per-level resource figures** exist, because the hardware is shared (see above).
- **Sign-87 latency** is clearly above the figure quoted for the paper; the cause is unknown (small sample, rejection loop, unknown measurement method).
- **xsim portability.** xsim rejects `combined_top.v` (three signals used before their declaration) while Vivado synthesis accepts it, and the Keccak VHDL needs an explicit compile order. `ML-DSA-OSH/scripts/build_sim.sh` works around both with a patched *copy*; the committed sources are untouched.
- **Out-of-context only.** Only `combined_top` was implemented; there is no surrounding design (processor, memory, I/O), no bitstream and nothing was tested on hardware.
- Power numbers are default-activity estimates.

## Installation & Usage

### Prerequisites

- Vivado 2024.2 installed at `/tools/Xilinx/Vivado/2024.2/` (set `XILINX_ROOT` for another location, for the simulation script).
- A device in your Vivado installation: the default is `xczu5ev-sfvc784-2-e`; the ZCU104's `xczu7ev-2ffvc1156-2-e` can be selected with `PART` if your installation includes it.

### Clone

```
git clone https://github.com/sadaouiyanis21/MLDsaFPGA.git
cd MLDsaFPGA
```

### Run Synthesis

```
source /tools/Xilinx/Vivado/2024.2/settings64.sh
cd ML-DSA-OSH/scripts/
vivado -mode batch -source synth_mldsa.tcl
```

Optional: `PART=...`, `CLK_NS=...` (default 4.35), `STAGE=synth` (synthesis only). Reports are written to `reports/raw/`; the Vivado run directory goes to `build/` (git-ignored).

### Run the simulation (cycle counts and KAT check)

```
cd ML-DSA-OSH/scripts/
./build_sim.sh            # or: ./build_sim.sh verify
```

This compiles the upstream testbenches with xsim, checks the outputs against the NIST vectors and prints the average cycle counts per level. Logs go to `build/sim/`.

### View Reports

Reports are in `reports/raw/` — open `reports/ml_dsa_benchmark.md` for the summary. `scripts/gen_report.py` regenerates the summary from `reports/raw/` (copy the simulation logs `build/sim/run_*.log` to `reports/raw/sim/` first).

## License

- ML-DSA-OSH original code: MIT License (KU Leuven COSIC); some files also carry the Apache License 2.0 of GMU CERG (see `ML-DSA-OSH/LICENSE` and `ML-DSA-OSH/NOTICE`).
- Scripts, reports and documentation added in this repository: MIT License.
