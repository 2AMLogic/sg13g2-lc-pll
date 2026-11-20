# divider hot-corner stall trace 20261110-3f59e40 (issue #197)

**Result (simulated, not measured): the 7 hot no-toggle units are a setup-timing failure of the M-counter terminal-count path, not a bench artefact and not a loss of swing.** The terminal-count decode `DT` pulses once, after the sampling edge of the `TC` flop and gone before the next edge, so `TC` is never set, `FB` never rises again, and the counter never reloads.

- **Scope**: two single units of the real divider chain (`cml2cmos` + `mcounter` + `acounter`, `design/netlist/divider.spice`), M = 12, A = 4, 3.3 V, ideal 0.4 Vpp differential input at 3.18 V common mode: **SLOW/125C at 625 MHz** (hbt_wcs, mos_ss, cap_wcs, res_wcs) and **TYP/125C at 687.5 MHz** (hbt_typ, mos_tt, cap_typ, res_typ). The other five failing units of `20261110-ramped-start-f27b2f0-corners.md` are not traced; they share the symptom (one FB rise near 1.7 ns), not shown to share the cause.
- **Method**: one local `klt sim --backend local` run per unit (ngspice-46, one process each, no grid), `tran 20p 30n`, `save all`, `options.waveforms`. Bench: the ramped start of PR #198 / issue #166 (`divider_corner.cir` at `f27b2f0`: VDD, IREF and the input common mode ramp from 0 over 3 ns, sine from 3 ns), which this branch does not carry. Requests: `gen_hot_trace_requests.py`; node reader: `trace_raw.py` (1.65 V crossings, interpolated linearly between 20 ps samples). Window 8 to 30 ns, i.e. after start-up. Raw files (160 MB each) are not kept.
- **Commit**: `3f59e40` of this repository plus the #198 bench files.

## Which stage stops toggling

| node | SLOW/125C 625 MHz, 8 to 30 ns | TYP/125C 687.5 MHz, 8 to 30 ns |
|---|---|---|
| `xcv.cmo` (CML output) | 1.14 to 3.15 V, 13 rises | 1.08 to 3.13 V, 15 rises |
| `ck` (cml2cmos out) | -0.05 to 3.38 V, 14 rises | -0.05 to 3.37 V, 15 rises |
| `ckl` (buffered counter clock) | 0.09 to 3.32 V, 14 rises | 0.10 to 3.31 V, 15 rises |
| M counter `q0` | changes every ckl period (13 crossings) | changes every ckl period |
| `dt` (terminal-count decode) | **one pulse: rise 26.571 ns, fall 27.531 ns** | **one pulse: rise 21.518 ns, fall 22.398 ns** |
| `tc` (XFT output) | **never above 0.03 V** | **never above 0.03 V** |
| `fb`, `mc` | `fb` 0 rises; `mc` 1 fall (19.2 ns) | `fb` 0 rises; `mc` 1 fall |

- Everything up to and including `ckl` and the counter flops toggles rail to rail. The first node that stops toggling is **`tc`**, the output of `XM.XFT` (`dff_tg_hv`, D = `dt`). Its D input is the decode `DT` = inverted `DTN`, built from `q3 q2` (`f32`), `q0 q1n` (`g10`).
- **Mechanism**: `DT` pulses high once, rising **0.154 ns after** the `ckl` rising (sampling) edge at 26.417 ns and falling **0.489 ns before** the next edge at 28.020 ns (SLOW; period 1.603 ns). TYP: rises 0.139 ns after the edge at 21.379 ns, falls 0.438 ns before the edge at 22.836 ns (period 1.457 ns). The edge samples 0, the next edge samples 0. `TC` and `FB` (`XFB`, D = `TC`) therefore never rise and the counter, which reloads on `TC`, never terminates. Counter flop clock-to-Q measures about 0.9 ns (`ckl` rise to `q0` change, SLOW, 3 edges at 0.90 to 0.96 ns) in a 1.6 ns period, before the 2 to 3 gates of decode and the setup of the next flop.
- Cause: **missing timing margin (setup) at 125 C, not swing and not a latch stuck by start-up**: `cml2cmos` and `ckl` keep full swing, the counter state advances, and the same SLOW/125C chain divides at 100 MHz (count request of the ramped-start record) and TYP/125C at 625 MHz. The two traced units agree on the mechanism; they differ in `DT` pulse timing by under 20 ps relative to the edge, so one cause is supported for both, not shown for the other five.

## Disposition

**(a): the divider as sized has a speed failure at 125 C; it is not a bench artefact (the ramped start removed every convergence failure and left these 7) and no speed-target change is proposed.** Candidate fixes (retiming the terminal-count decode, splitting the M counter, sizing the decode gates) are a design change and are filed as a follow-up with its own acceptance criteria, not made here. No design file changed, so the 54-unit grid is not re-run in this issue; the next grid record belongs to the follow-up. The 625 / 687.5 MHz targets in `spec/target-spec.md` row 4 are unchanged.
