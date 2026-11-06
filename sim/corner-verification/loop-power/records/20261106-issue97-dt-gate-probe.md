# SLOW 125 C 2.97 V: the `DT` path is 1.07 ns clock-to-Q plus 0.78 ns of NOR / NAND / inverter, 1.85 ns against a 1.606 ns period (2026-11-06, base `d95658e`, issue #97)

**Result (simulated, not measured): PARTIAL, `fail` for the issue. No design change. This closes owed item 1 of `20261106-issue97-dt-parallel-driver-trial.md` (locate where the 1.85 ns goes): one forced-state probe at SLOW 125 C 2.97 V, gate by gate. The divide-at-all-18 AC, the fix AC, the nominal row-11 power re-report, the `cmo` load / VCO re-check and `scripts/run-divider-elab.sh` remain NOT met.**

## Method
`make_dt_gate_probe_97.py` copies `request-forcedprobe-97-SLOW-125-2.97.json` (same bench-only forcing `q=1011, b=000, tc=0, tcn=1` through 200 ohm for 8-20 ns, ramped start-up, in-tree netlist, `tran 4p 60n`, 1.485 V crossings from 14 ns) and replaces the probes with `ckl`, `q0..q3`, `q1n`, `f32`, `g10`, `dtn`, `dt`, `tc`. `analyze_dt_gate_97.py` (reads the saved crossings only) places each transition after the last `ckl` rise.
- Run 1 (`request-dtgate-97-SLOW-125-2.97.json`, 14 crossings per edge, job `klt-sim-413a3c7e712b`): the 14-rise `ckl` window ends at 35.7 ns, before the first `DT` pulse (43.95 ns), so `f32`, `dtn`, `dt` show no transition in the analysed window. It is a window miss, kept as evidence (`...-dt-gate-probe-measurements.json`); it carries no `DT` result.
- Run 2 (`request-dtgate-97-SLOW-125-2.97-n34.json`, 34 crossings per edge, job `klt-sim-0062a2574052`): 29 `ckl` rises to 59.5 ns. Used for the result (`...-dt-gate-probe-n34-measurements.json`).
- Both through `klt sim --batch-set ... --backend batch`, nothing run locally. The first submit was refused (`batch_no_capacity`: the Spot quota is shared with ci-spot); the retry with `--wait-for-capacity` was accepted. This host has no PDK, so a local fall-back was not possible and not used. Fleet ngspice 46 against the pin of 47 (`sim/pins.json`): the pin is not met. One run, repeatability not shown. Crossings are at VDD/2, not the flop's capture threshold.

## Result: the first `DT` pulse, 42.1 ns launching edge (clock period 1.606 ns)
| step | node transition | time (ns) | after previous step |
|---|---|---|---|
| launching `ckl` rise | | 42.10 (inferred: `q0` fall minus its 1.07 phase) | |
| flop clock-to-Q | `q0` falls | 43.17 (phase 1.07) | 1.07 |
| NOR2 `XT2` | `g10` rises | 43.42 | 0.25 |
| NAND2 `XT3` | `dtn` falls | 43.72 | 0.30 |
| inverter `XT4` | `dt` rises | 43.95 | 0.23 |
| next capture edge | `ckl` rises | 43.71 | `dt` is 0.25 ns after it |

`dt` falls 44.84 ns, 0.89 ns wide. `dtn` / `dt` have a second pulse at 54.98 / 55.18 ns, spaced 11.23 ns (6.99 clock periods) from the first; `tc` never crosses. Same chain at the second pulse: `dtn` falls with phase 0.08, `dt` rises with phase 0.28. The other leg (`q2` falls 41.66, `f32` rises 41.86, 0.20 ns) is complete 1.8 ns before `g10` and is not the late input.

## Reading
- The last-arriving input is `q0` through `g10` (`XT2`): of the 1.85 ns, the flop clock-to-Q is 1.07 ns (58 %) and the three decode levels 0.78 ns (0.25 + 0.30 + 0.23). Measured on this one pulse; the launching edge is inferred, not traced.
- To be captured at the 43.71 ns edge, `DT` has to move earlier by at least 0.25 ns plus the flop's setup time, which is still not measured. Removing the whole inverter (0.23 ns) is not enough on its own, and `20261106-issue97-dt-nand-nor-trial.md` shows that removing it by restructuring the decode produced no FB edges at all.
- The decode is therefore at most 42 % of the path; trimming it alone cannot buy the margin. A path that does not start at `q0`'s clock-to-Q (a decode computed one count earlier and registered, or a `q0` replica flop) is the structural option this points at. That is a reading of one pulse, not a tested fix.

## Not done / owed (the issue stays open)
1. A design trial that takes `q0`'s clock-to-Q out of the `DT` path (for example `DT` registered from the previous count), in the adopted flop cells, `design/*.sch` plus the regenerated `design/netlist/divider.spice`; or, if the path cannot close at 625 MHz at SLOW 125 C 2.97 V in these cells, the decision file with this and the earlier evidence (AC 3). A measured flop setup time at 125 C 2.97 V.
2. 18-corner re-run after any fix, nominal row-11 power against #84, `scripts/run-divider-elab.sh` at nominal, and the `cmo` load / VCO swing and start-up re-check.
