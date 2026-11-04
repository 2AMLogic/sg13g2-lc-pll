# Edge-aligned counter trace localises the 125 C failure to one bit's capture; stronger TC/TCN drivers do not fix it (2026-11-04, base `0964b49`, issue #97)

**Result (simulated, not measured): PARTIAL, `fail` for the issue. (1) The edge-aligned trace at FAST 125 C 2.97 V shows the M counter loads 12 correctly, then at the next clock `q2` does not fall (state 1100 -> 1111, not 1011) although `D2` reads 0 at that clock crossing. (2) A trial netlist change that drives `TC`/`TCN` through a two-stage buffer (1 then 4 parallel `inv_hv`) leaves all four 125 C corners wrong; the trial was reverted and is not in the tree. The divide-at-all-18 AC, the fix AC and the row-11 power re-report remain NOT met.**

## 1. Edge-aligned trace (measurement)

- **Method**: `make_edge_trace_97.py` -> `request-edge-97-FAST-125-2.97.json` (fails) and `request-edge-97-TYP-27-2.97.json` (divides, reference). Ramped start-up body unchanged, `tran 4p 310n`. For 30 rising edges of `xdiv.ckl` (1.65 V crossing, from 250 ns), `.meas find ... when v(xdiv.ckl)=1.65 rise=k` records `q0..q3, b1..b3, tc, tcn` and the flop D inputs `d0..d3, dt, db1..db3` at that crossing. One run per corner (repeatability not shown), `klt sim --batch-set` on the batch fleet (jobs `klt-sim-74bd511e3b47`, `klt-sim-070406bd98ab`). ngspice 46 on the fleet against the pin of 47 (`sim/pins.json`): the pin is not met; nothing was run locally. Raw: `20261104-issue97-edge-trace-and-tc-buffer-measurements.json`. Levels thresholded at 1.485 V; bit order `q3 q2 q1 q0`.
- **FAST 125 C 2.97 V**, edges 8-12 (q at the crossing is the value before the clock acts; D is the value the flops are about to capture):

| edge | q | tc | D (d3..d0) | note |
|---|---|---|---|---|
| 8 | 0010 | 0 | 0001 | `dt` = 1 (terminal count arriving) |
| 9 | 0001 | 1 | 1100 | load of M = 12 selected |
| 10 | 1100 | 0 | **1011** | loaded 12 correctly; next value 11 is on D |
| 11 | **1111** | 0 | 1110 | expected 1011; `q2` stayed 1 |
| 12 | 1110 | 0 | 1101 | counts down from the wrong value |

  The pattern repeats every period: 16 clocks (1001 ... 0001, load, 1100, 1111, 1110, ...) against 12 expected, i.e. the stuck `q2` adds 4. `D2` was 0 at the edge-10 crossing, yet the flop captured 1. So the capture is early/late against the **flop's internal clock** (`CLKB`/`CKBB` follow `ckl` by 160-240 ps at this corner, `20261104-issue97-125c-diagnosis.md`), not a wrong logic value. A setup violation on the path `TC`/`TCN` fall/rise -> `l2b`/`c2` -> `D2` (which changes only after the load clock) is the consistent reading; it is **not** shown directly (no D2 settle time against the internal clock edge was measured).
- **TYP 27 C 2.97 V (reference)**: 12-clock period holds; loads 1100, then 1011, 1010, ... correct.

## 2. Trial: strong TC/TCN drivers (refutation of "output drive alone")

- **Candidate**: `TC`/`TCN` each drive about 10-11 gate inputs from the minimum-size output inverter of a `dff_tg_hv`, so `D2` settles late after the load clock. Buffering should speed that path.
- **Trial** (netlist-only, `design/netlist/divider.spice`, reverted): in `mcounter`, `XFT`/`XFTN` drive new nets `TCr`/`TCNr`; `TCr -> inv_hv -> 4 x inv_hv in parallel -> TC` (same for `TCN`). `divider.sch` untouched.
- **Method**: the four single-corner requests `request-diag125-97-<proc>-<vdd>.json` (300 ns, unchanged) via `klt sim --batch-set ... --max-in-flight 4 --backend batch`, one run each (jobs `klt-sim-07cf89c566c8`, `klt-sim-959ecfe97901` and two more).

| corner (125 C) | FB rising edges with TC buffer (ns) | FB period (ns) | before (ns) | class |
|---|---|---|---|---|
| FAST 2.97 V | 53.7, 80.1, 106.5, ... | 26.4 | 26.4 | unchanged, wrong ratio |
| SLOW 3.63 V | 55.0, 81.4, 107.8, ... | 26.4 | 26.4 | unchanged, wrong ratio |
| TYP 2.97 V | 52.0, 76.0, 93.6, 124.0, 154.4, ... | 24.0, 17.6, 30.4, 30.4 | 22.4 then 28.8 | erratic, wrong ratio |
| SLOW 2.97 V | none (FB within +-1.4 mV) | - | none | stuck, unchanged |

Together with the TC-fanout-split, D-delay and clock-buffer records, `TC`/`TCN` drive strength is not the limiter. That FAST and SLOW 3.63 V reproduce the previous edge times exactly (the periods are quantised to half-clocks) is not explained.

## Not done / owed (the issue stays open)

1. Measure D2 settling against the flop's internal `CLKB`/`CKBB` edge at edges 10-11 to confirm or refute the setup reading; try a change that re-times the load path (for example registering the `l2b`/`c2` inputs) rather than another drive trial.
2. A fix, then the 18-corner re-run (14 of 18 divide as of `20261104-issue97-stage2-18-corner-after-selfbias.md`), the nominal row-11 power re-report against #84, and the VCO swing/start-up re-check with the `cmo` coupling-cap load. Not touched here; no power number was taken.
