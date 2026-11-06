# DT driver split, one inverter per flop D input: the same two 125 C 2.97 V corners still do not divide, trial reverted (2026-11-06, base `6716d35`, issue #97)

**Result (simulated, not measured): NEGATIVE for the issue (no corner improved). Owed item 1 of `20261106-issue97-dt-nand-nor-trial.md` was tried in one form: the `DT` driver loading halved. Netlist-only trial, reverted, NOT in the tree (patch kept beside this record). The divide-at-all-18 AC, the nominal row-11 power re-report, the `cmo` load / VCO re-check and `scripts/run-divider-elab.sh` remain NOT met.**

## Trial
`20261106-issue97-dt-split-driver-trial.patch` (`design/netlist/divider.spice` only; `.sch`, adopted cells and VCO untouched). `XT4` (`DTN` -> `DT`) kept and driving only `XFT` (`TC`); a second `inv_hv` `XT4B` (`DTN` -> `DT2`) drives only `XFT2` (`TC2`). Function unchanged; the `DT` fan-out falls from two flop D inputs to one, and `DTN` gains one inverter input. The `XT3` NAND2 driving `DTN` is unchanged and now sees three loads (`XFTN`, `XT4`, `XT4B`) instead of two.

## Method
The four single-corner `request-diag125-97-<proc>-<vdd>.json` (unchanged: ramped start-up, 300 ns, FB/TC rising edges from 40 ns), one `klt sim --batch-set ... --backend batch` call, nothing run locally. Jobs: FAST 2.97 V `klt-sim-553385468c5a`, SLOW 2.97 V `klt-sim-eaabaac43bd7`, SLOW 3.63 V `klt-sim-e69c8c1460c5`, TYP 2.97 V `klt-sim-085a922abd1b`. Fleet ngspice 46 against the pin of 47 (`sim/pins.json`): the pin is not met. One run per corner, repeatability not shown.

## Result
| corner (125 C) | `fbr1..4` / `tcr1..2` from 40 ns | in tree before the trial |
|---|---|---|
| FAST 2.97 V | FB rising at 47.3, 67.3, 87.3, 107.3 ns (20.0 ns period) | divides |
| SLOW 3.63 V | FB rising at 48.6, 68.6, 88.6, 108.6 ns (20.0 ns period) | divides |
| SLOW 2.97 V | none (all measurements not reached) | converged, no divide |
| TYP 2.97 V | none (all measurements not reached) | converged, no divide |

All four converged (`status` pass). No corner changed class, so this splits no hypothesis: it neither supports nor refutes the `DT` timing-margin reading of `20261105-issue97-fast-typ-125c-setup-phase.md`. The `DT` edge time was not probed, so the trial does not show whether `DT` arrives earlier; it shows only that halving its fan-out is not sufficient at SLOW and TYP 125 C 2.97 V.

## Not done / owed (the issue stays open)
1. A stronger `DT` / `DTN` source at those two corners (e.g. a larger `XT3`/`XT4` in the pinned cell, or lighter `q` loads), with a `DT` edge-time probe so the effect is read rather than inferred; or the decision file if the path cannot close at 625 MHz at 125 C 2.97 V in these cells (AC 3).
2. Measured flop setup time at 125 C 2.97 V; 18-corner re-run after any fix; nominal row-11 power against #84; `scripts/run-divider-elab.sh`; `cmo` load / VCO swing and start-up re-check.
