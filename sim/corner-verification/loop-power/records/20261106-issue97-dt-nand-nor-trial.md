# DT decode rebuilt as NAND2 -> NOR2 (inverter removed): no 125 C corner produces an FB edge, FAST and SLOW 3.63 V regress, trial reverted (2026-11-06, base `12617bf`, issue #97)

**Result (simulated, not measured): NEGATIVE, `fail` for the issue. Owed item 1 of `20261105-issue97-fast-typ-125c-setup-phase.md` was tried in one form and made it worse. Netlist-only trial, reverted, NOT in the tree (patch kept beside this record). The divide-at-all-18 AC, the fix AC, the nominal row-11 power re-report, the `cmo` load / VCO re-check and `scripts/run-divider-elab.sh` remain NOT met.**

## Trial
`20261106-issue97-dt-nand-nor-trial.patch` (`design/netlist/divider.spice` only; `.sch`, adopted cells and VCO untouched). The old `DT` path `nor2(q3,q2)`, `nor2(q0,q1n)` -> `nand2` (`DTN`) -> `inv_hv` (`XT4`) -> `DT` is three gate levels after the q outputs, four from `q1` (via `XIQ1`). `XT4` is replaced by `DT = nor2(nand2(q3n,q2n), nand2(q0n,q1))`, the same function (`q3=q2=0, q1=1, q0=0`) with two levels from `q1` and `q2` (`q2n` is the QN tap) and three from `q0`/`q3`. `DTN`, `TCN` and the old NOR/NAND stay as they were (they still drive `XFTN`). Logic checked by hand against the old expression; not simulated at gate level in isolation.

## Method
The four single-corner `request-diag125-97-<proc>-<vdd>.json` (unchanged: ramped start-up, 300 ns, FB/TC edges from 40 ns), one `klt sim --batch-set ... --backend batch` call, nothing run locally. Jobs: FAST 2.97 V `klt-sim-8ebc37d31d5e`, SLOW 2.97 V `klt-sim-12c5dcf1805a`, SLOW 3.63 V `klt-sim-2d5b384a7dad`, TYP 2.97 V `klt-sim-b157430abaee`. Fleet ngspice 46 against the pin of 47 (`sim/pins.json`): the pin is not met. One run per corner, repeatability not shown. The netlist hash in the FAST report (`abe0ece6...`) matches the trial file.

## Result
| corner (125 C) | FB / TC rising edges `fbr1..8`, `tcr1..8` from 40 ns | before the trial (in tree) |
|---|---|---|
| FAST 2.97 V | none (all 16 `measurement_not_reached`) | divides, 20.0 ns |
| SLOW 3.63 V | none | divides, 20.0 ns |
| SLOW 2.97 V | none | converged, no divide |
| TYP 2.97 V | none | converged, no divide |

All four converged (`status` pass, no timestep failure), so these are converged-no-divide. In the FAST 2.97 V log the counter ends at `q3` high, `q0..q2` low, `tc` ~0: it never presents terminal count. No waveform tracing was done on why.

## Reading
- Removing the `XT4` inverter and shortening `q1`/`q2` to two levels does not shorten the effective `DT` path: the single `nor2_hv` now drives two flop D inputs (`XFT`, `XFT2`) through series PMOS, and `q0n`, `q3n`, `q2n`, `q1` each gain a NAND input. That is a candidate, not measured: no `DT` edge time was probed here. What is measured is only that no corner produces an FB edge.
- It does not refute the timing-margin reading of the previous record; it shows this decode restructure is not the way to close it.

## Not done / owed (the issue stays open)
1. A `DT` that is restored from the inverter, with the extra margin taken elsewhere (e.g. an up-sized `DT` driver in the pinned cell, lighter `q` loads), or the decision file if the `DT` path cannot close at 625 MHz at SLOW 125 C 2.97 V in these cells (AC 3).
2. Measured flop setup time at 125 C 2.97 V; 18-corner re-run after any fix; nominal row-11 power against #84; `scripts/run-divider-elab.sh`; `cmo` load / VCO swing and start-up re-check.
