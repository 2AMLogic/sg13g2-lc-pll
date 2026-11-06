# DT inverter doubled in parallel (stronger DT source): the same two 125 C 2.97 V corners still do not divide, trial reverted (2026-11-06, base `92963c3`, issue #97)

**Result (simulated, not measured): NEGATIVE for the issue (no corner changed class). Owed item 1 of `20261106-issue97-dt-split-driver-trial.md` tried in one form: a stronger `DT` source. Netlist-only trial, reverted, NOT in the tree (patch kept beside this record). The divide-at-all-18 AC, the nominal row-11 power re-report, the `cmo` load / VCO re-check and `scripts/run-divider-elab.sh` remain NOT met.**

## Trial
`20261106-issue97-dt-parallel-driver-trial.patch` (`design/netlist/divider.spice` only; `.sch`, adopted cells and VCO untouched). A second `inv_hv` `XT4B` (`DTN` -> `DT`) in parallel with `XT4`, output nodes tied: the `DT` drive roughly doubles into the same two flop D inputs (`XFT`, `XFT2`); `DTN` gains one inverter input. Function unchanged.

## Method
The four single-corner `request-diag125-97-<proc>-<vdd>.json` (unchanged: ramped start-up, 300 ns, FB/TC rising edges from 40 ns), one `klt sim --batch-set ... --backend batch` call, nothing run locally. Jobs: FAST 2.97 V `klt-sim-e43266e97155`, SLOW 2.97 V `klt-sim-62441adbd7b1`, SLOW 3.63 V `klt-sim-efa22d3b4ead`, TYP 2.97 V `klt-sim-a9ca52bff8c1`. Fleet ngspice 46 against the pin of 47 (`sim/pins.json`): the pin is not met. One run per corner, repeatability not shown.

## Result
| corner (125 C) | FB rising edges from 40 ns | in tree before the trial |
|---|---|---|
| FAST 2.97 V | 47.29, 67.29, 87.29, 107.29, 127.29 ns (20.0 ns period) | divides |
| SLOW 3.63 V | 48.60, 68.59, 88.59, 108.59, 128.59 ns (20.0 ns period) | divides |
| SLOW 2.97 V | none (16 measurements not reached) | converged, no divide |
| TYP 2.97 V | none (16 measurements not reached) | converged, no divide |

All four converged (`status` pass). Doubling `DT` drive neither fixes nor breaks any corner. The `DT` edge time was not probed, so this does not show whether `DT` arrives earlier; it shows only that the last-stage drive is not what limits SLOW/TYP 125 C 2.97 V. Together with the halved-fan-out trial (`...dt-split-driver-trial.md`) this is two independent `DT` loading/drive changes in opposite directions with no effect, which weakens (does not refute) the reading that the `DT` last stage is the bottleneck; the clock-to-Q plus the NOR/NAND levels, or something other than `DT` timing, remain candidates.

## Not done / owed (the issue stays open)
1. Probe the `DT`/`DTN`/`f32`/`g10` edge times at SLOW 125 C 2.97 V to locate where the 1.85 ns goes; a measured flop setup time at 125 C 2.97 V. If the path cannot close at 625 MHz at SLOW/TYP 125 C 2.97 V in these cells, file the decision with the evidence (AC 3).
2. 18-corner re-run after any fix; nominal row-11 power against #84; `scripts/run-divider-elab.sh`; `cmo` load / VCO swing and start-up re-check.
