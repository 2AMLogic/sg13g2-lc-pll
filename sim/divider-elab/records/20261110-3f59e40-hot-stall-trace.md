# Divider hot-corner stall trace 20261110-3f59e40 (issue #197)

**Simulation result.** Seven of 54 ramped-start corner runs showed just one startup feedback edge. Two of those seven were traced internally. In each trace the M-counter terminal-count decode (`DT`) pulsed high entirely between successive rising edges of the buffered clock (`CKL`). The first stage to miss the pulse was `XM.XFT`. Its output (`TC`) stayed at or below 0.03 V and the feedback output (`FB`) had no rising edge in the 8–30 ns window. The cause of the other five stalls is open.

Both traces used the `cml2cmos`, `mcounter` and `acounter` chain at M = 12, A = 4, 3.3 V and 125 °C. The SLOW run used 625 MHz (hbt_wcs, mos_ss, cap_wcs, res_wcs) and the TYP run used 687.5 MHz (hbt_typ, mos_tt, cap_typ, res_typ).

**Drive amplitude.** The [ramped-start corner record](20261110-ramped-start-f27b2f0-corners.md) calls the ideal sine “0.4 Vpp” without specifying the voltage pair. In the [deck](../divider_corner.cir), after the 3 ns ramp, BP and BN drive opposite 0.2 V peak sinusoids around 3.18 V common mode. Each pin sees 0.4 Vpp. Subtracting INN from INP gives ±0.4 V, or **0.8 Vpp differential**. The traces characterize that drive only.

**Method.** The original runs used the circuit at `3f59e40` and the ramped-start bench at `f27b2f0` (PR #198). Each unit ran once with local `klt sim`, ngspice-46, `tran 20p 30n`, `save all` and `options.waveforms`. [gen_hot_trace_requests.py](../gen_hot_trace_requests.py) generates the requests. [trace_raw.py](../trace_raw.py) interpolates 1.65 V crossings between adjacent samples. The original raw waveforms were discarded.

## Which stage misses the pulse

| node | SLOW/125C 625 MHz, 8 to 30 ns | TYP/125C 687.5 MHz, 8 to 30 ns |
|---|---|---|
| `xcv.cmo` (CML output) | 1.14 to 3.15 V, 13 rises | 1.08 to 3.13 V, 15 rises |
| `ck` (cml2cmos out) | -0.05 to 3.38 V, 14 rises | -0.05 to 3.37 V, 15 rises |
| `ckl` (buffered counter clock) | 0.09 to 3.32 V, 14 rises | 0.10 to 3.31 V, 15 rises |
| M counter `q0` | changes every ckl period (13 crossings) | changes every ckl period |
| `dt` (terminal-count decode) | **one pulse: rise 26.571 ns, fall 27.531 ns** | **one pulse: rise 21.518 ns, fall 22.398 ns** |
| `tc` (XFT output) | **never above 0.03 V** | **never above 0.03 V** |
| `fb`, `mc` | `fb` 0 rises; `mc` 1 fall (19.2 ns) | `fb` 0 rises; `mc` 1 fall |

The converter output (`ck`), buffered clock (`ckl`) and observed counter bit (`q0`) kept toggling. The following times use the 1.65 V crossing on each signal.

| Corner | CKL rise (ns) | DT rise (ns) | DT fall (ns) | Next CKL rise (ns) | DT rises after first edge (ps) | DT falls before next edge (ps) |
|---|---:|---:|---:|---:|---:|---:|
| SLOW | 26.417 | 26.571 | 27.531 | 28.020 | 154 | 489 |
| TYP | 21.379 | 21.518 | 22.398 | 22.836 | 139 | 438 |

The rising offsets differ by 15 ps and the falling offsets by 51 ps. In both cases `DT` was low at both edges. In the [divider netlist](../../../design/netlist/divider.spice), XFT samples `DT` on `CKL` and drives `TC`, which XFB samples to produce `FB`. The M-counter load mux uses `TC2` from the separate XFT2 flop. The record gives no `TC2` crossing times.

XT1–XT4 decode count 2. A late count-2 decode is one hypothesis. A transient decode as several counter bits change could also produce a pulse between edges. Three SLOW `q0` transitions followed a `CKL` rising edge by 0.90–0.96 ns, but the recorded data do not identify a `Q[3:0]` transition into count 2, its launch and intended capture edges, or the setup requirement of XFT. A setup violation remains unverified.

## Disposition

Disposition (a) keeps the stage-2 counter speed gate open. The corner grid had 47 expected divides and seven hot stalls. One stall was at SLOW/125 °C, 625 MHz, A = 4 (N = 100), the post-prescaler rate for the required 5.0 GHz channel. Six were at 687.5 MHz, A = 4, 0, 7 at both SLOW and TYP. The SLOW/125 °C count check passed at 100 MHz and TYP/125 °C passed at 625 MHz. [Issue #199](https://github.com/2AMLogic/sg13g2-lc-pll/issues/199) tracks the design work and the post-fix 54-unit grid against the existing 625 and 687.5 MHz targets.
