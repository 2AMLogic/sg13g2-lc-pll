# DT decode fed from lightly loaded replica flops of q0 and q1: the same two 125 C 2.97 V corners still do not divide, trial reverted (2026-11-06, base `610fe46`, issue #97)

**Result (simulated, not measured): NEGATIVE for the issue (no corner changed class). Owed item 1 of `20261106-issue97-dt-gate-probe.md` tried in one form: take the heavily loaded `q0` flop's clock-to-Q out of the `DT` path. Netlist-only trial, reverted, NOT in the tree (patch kept beside this record). The divide-at-all-18 AC, the nominal row-11 power re-report, the `cmo` load / VCO re-check and `scripts/run-divider-elab.sh` remain NOT met.**

## Trial
`20261106-issue97-dt-decode-replica-flops-trial.patch` (`design/netlist/divider.spice` only; `.sch`, adopted cells and VCO untouched). Two extra flops on the same `CK` and the same D nets as `q0`/`q1`: `XQ0R` (`dff_tg_hv`, D = `D0`) and `XQ1R` (`dff_tg_hv_qn`, D = `D1`), whose only load is the `XT2` NOR2 (`q0r`, `q1rn`). `XT2` now reads the replicas instead of `q0` / `q1n`. Function unchanged; cost is two flops on `CKL` and on `D0`/`D1`, which raises divider power (stated against #84; not quantified here, the 4-corner `idavg` below is for the diagnosis window only).

## Method
The four single-corner `request-diag125-97-<proc>-<vdd>.json` (unchanged: ramped start-up, 300 ns, FB/TC rising edges from 40 ns), one `klt sim --batch-set ... --backend batch` call, nothing run locally. Jobs: FAST 2.97 V `klt-sim-f552ed0e1b41`, SLOW 2.97 V `klt-sim-b9aa9813a652`, SLOW 3.63 V `klt-sim-7848c8ee837a`, TYP 2.97 V `klt-sim-dc9b1efd32af`. Fleet ngspice 46 against the pin of 47 (`sim/pins.json`): the pin is not met. One run per corner, repeatability not shown.

## Result
| corner (125 C) | FB rising edges from 40 ns | in tree before the trial |
|---|---|---|
| FAST 2.97 V | 47.32, 67.32, 87.32, 107.32, 127.32 ns (20.0 ns period) | divides |
| SLOW 3.63 V | 48.62, 68.62, 88.62, 108.62, 128.62 ns (20.0 ns period) | divides |
| SLOW 2.97 V | none | converged, no divide |
| TYP 2.97 V | none | converged, no divide |

All four converged (`status` pass). Replica flops neither fix nor break any corner. Three `DT` timing changes are now on record with no effect on the two failing corners: lower fan-out, higher last-stage drive, lighter `q0`/`q1` load. The replica flops' own clock-to-Q was not probed, so this does not show that the decode inputs arrive earlier, only that if they do it is not enough. That weakens the reading that the flop-to-`DT` path alone sets the failure; a measured flop setup time at 125 C 2.97 V and a probe of `q0r`/`g10`/`dt` remain the way to tell.

## Not done / owed (the issue stays open)
1. Probe `q0r`, `q1rn`, `g10`, `dt` at SLOW 125 C 2.97 V with the replicas in, and measure the flop setup time at 125 C 2.97 V; a registered-from-previous-count `DT` in `design/*.sch` plus regenerated netlist. If the counter cannot close at 625 MHz at SLOW/TYP 125 C 2.97 V in the adopted cells, file the decision with the evidence (AC 3). Per the issue, `spec/` is not edited by agents.
2. 18-corner re-run after any fix, nominal row-11 power against #84, `scripts/run-divider-elab.sh` at nominal, and the `cmo` load / VCO swing and start-up re-check.
