# Q-bar tap on q2 plus a separate TC copy for the load NANDs: two of the four 125 C corners now divide to 50 MHz (2026-11-05, base `e9f8965`, issue #97)

**Result (simulated, not measured): PARTIAL, `fail` for the issue. First structural change in this issue that moves a 125 C corner to the right ratio: FAST 2.97 V and SLOW 3.63 V (both 125 C) divide at a steady 20.0 ns FB period; SLOW 2.97 V and TYP 2.97 V (125 C) still do not. The trial is a netlist-only edit, reverted and NOT in the tree (patch kept beside this record). The divide-at-all-18 AC, the fix AC and the row-11 power re-report remain NOT met.**

- **Candidate** (from `20261105-issue97-bit-trace.md`): D2 is reached by two co-critical routes, clock -> q2 -> `q2n` -> `a2` -> `D2` and clock -> `TC` -> `l2b` -> `D2`, both 1.56 ns against a 1.60 ns period at FAST 125 C 2.97 V. Each had been shortened alone (`...qn-tap-trial.md`, `...tc-fanout-split.md`, `...edge-trace-and-tc-buffer.md`) with no corner moving. Shorten both together.
- **Trial** (`20261105-issue97-qn-tap-plus-tc2-trial.patch`, `design/netlist/divider.spice` only, `divider.sch`/`mcounter.sch` untouched, adopted `dff_tg_hv` untouched): (1) `XQ2` becomes a local `dff_tg_hv_qn`, the same pinned `inv_hv`/`tgate_hv` with the slave node `SB` brought out as `q2n`, and `XIQ2` is deleted; (2) a second terminal-count flop `XFT2` (same `DT`, same clock) drives a new net `TC2`, used only by the four load NANDs `XL0B..XL3B`; every other load stays on the original `TC`/`TCN`. This differs from the earlier split, which moved 14 loads and stopped the counter; here 4 loads move and the counter runs.
- **Method**: the four single-corner `request-diag125-97-<proc>-<vdd>.json` (unchanged: ramped start-up, 300 ns, FB/TC edges from 40 ns) via `klt sim --batch-set ... --max-in-flight 4 --backend batch` against the trial netlist. One run per corner, repeatability not shown. Jobs: FAST 2.97 V `klt-sim-496a5844a91c`, SLOW 2.97 V `klt-sim-62e797d60bee`, SLOW 3.63 V `klt-sim-222ba68e7e42`, TYP 2.97 V `klt-sim-7ee47d1c32be`. ngspice 46 on the fleet against the pin of 47 (`sim/pins.json`): the pin is not met; nothing was run locally. Raw numbers: `20261105-issue97-qn-tap-plus-tc2-trial-measurements.json`.

| corner (125 C) | FB rising-edge period with trial (ns) | before (ns) | class |
|---|---|---|---|
| FAST 2.97 V | 20.0 steady (7 periods) | 26.4 | **divides** |
| SLOW 3.63 V | 20.0 steady (7 periods) | 26.4 | **divides** |
| TYP 2.97 V | fewer than two FB edges in the window | 28.8 | converged, does not divide |
| SLOW 2.97 V | fewer than two FB edges in the window | none (stuck) | converged, does not divide |

- Window-mean PLL-block currents (include start-up; not a row-11 number): FAST ip 1.94 / id 4.46 mA, SLOW 3.63 V 1.78 / 5.25, SLOW 2.97 V 1.76 / 3.54, TYP 2.97 V 1.87 / 4.02. No nominal power point was taken, so #84 is not touched. The extra flop and local flop are a few cells; their power cost is not isolated here.

## Reading

- Shortening both D2 routes is what moves FAST and SLOW 3.63 V; either alone moved nothing. That supports the co-critical reading of the bit trace as a cause, it does not prove it (one run per corner; the two corners that moved also have the most timing margin of the four).
- TYP 2.97 V and SLOW 2.97 V (the lowest VDD, slowest cells) still fail. The trace that explained FAST was not repeated there, so the failing bit at those two is unknown; another path, or the same path with less margin, may limit them.
- Not checked: that the corners which divided before the trial (14 of 18 at `20261104-issue97-stage2-18-corner-after-selfbias.md`) still divide. The trial adds load on `DT` and a new flop on the clock; a regression at the cool or nominal corners is possible and untested.

## Not done / owed (the issue stays open)

1. Bit trace (as `20261105-issue97-bit-trace.md`) at TYP 125 C 2.97 V and SLOW 125 C 2.97 V with the trial applied, to see which capture is still wrong.
2. If the trial is kept: implement it in `mcounter.sch` (local QN flop symbol, second TC flop) and regenerate netlists via `klt netlist`, then the 18-corner stage-2 re-run including the 14 corners that divided before, the nominal row-11 power re-report against #84, `scripts/run-divider-elab.sh`/`divider_counts.py` at nominal, and the VCO swing/start-up re-check with the `cmo` load.
