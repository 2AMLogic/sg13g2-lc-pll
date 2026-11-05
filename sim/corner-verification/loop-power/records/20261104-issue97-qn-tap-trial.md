# Direct Q-bar tap on the q2 flop does not move the four 125 C corners (2026-11-04, base `6d1cbe3`, issue #97)

**Result (simulated, not measured): REFUTATION of "removing the `q2n` inverter from the q2 -> `a2` -> `D2` path closes the 125 C corners", `fail` for the issue. A trial exposed the slave node `SB` of the q2 flop as `q2n` (new local `dff_tg_hv_qn` built from the same pinned `inv_hv`/`tgate_hv`, `XIQ2` deleted; `design/mcounter.sch` and the regenerated `divider.spice`/`pll_top.spice` via `design/netlist.sh`). The four 125 C corners behave as before the trial; it was reverted and is not in the tree. The divide-at-all-18 AC, the fix AC and the row-11 power re-report remain NOT met.**

- **Candidate** (from `20261104-issue97-d2-settle.md`): clock -> q2 -> `D2` is 1.56 ns against a 1.60 ns period at FAST 125 C 2.97 V; `SB` is already the inverted bit, so tapping it drops one inverter delay from the `a2` leg.
- **Method**: the four single-corner `request-diag125-97-<proc>-<vdd>.json` (unchanged: ramped start-up, 300 ns) run with `klt sim --batch-set ... --max-in-flight 4 --backend batch` against the trial netlist. One run per corner, repeatability not shown. Jobs: FAST 2.97 V `klt-sim-09156a907ec5`, SLOW 2.97 V `klt-sim-188bbbdad4b7`, SLOW 3.63 V `klt-sim-521fb732a6ec`, TYP 2.97 V `klt-sim-1755fd70534a`. ngspice 46 on the fleet against the pin of 47 (`sim/pins.json`): the pin is not met; nothing was run locally. Raw numbers: `20261104-issue97-qn-tap-trial-measurements.json`.

| corner (125 C) | FB rising-edge period with QN tap (ns) | before (ns) | class |
|---|---|---|---|
| FAST 2.97 V | 26.4 steady (8 edges from 53.7) | 26.4 | converged, does not divide to 20 ns |
| SLOW 3.63 V | 26.4 steady (8 edges from 55.0) | 26.4 | converged, does not divide |
| TYP 2.97 V | 22.4 then 28.8 steady | 28.8 | converged, does not divide |
| SLOW 2.97 V | no FB edge | none (stuck) | converged, stuck |

- Window-mean PLL-block currents (not a row-11 number; include start-up): FAST ip 1.94 / id 4.19 mA, SLOW 2.97 V 1.76 / 3.36, SLOW 3.63 V 1.78 / 4.92, TYP 1.87 / 3.98. No nominal power point was taken, so #84 is not touched.

## Reading

The FB periods are identical to the baseline, so the `q2n` inverter is not what limits the q2 loop, or the miscapture is not the only term; the setup reading of `d2-settle` is not contradicted by this (the saved delay, about one inverter, may be too small, and `SB` carries an extra load). Four structural trials (D delay, TC/TCN buffering, clock buffering, QN tap) have now not closed a corner.

## Not done / owed (the issue stays open)

1. A trace at FAST 125 C 2.97 V of which bit's capture is wrong at the reload (not just q2): the earlier traces covered q2 only.
2. A fix, then the 18-corner re-run (14 of 18 divide as of `20261104-issue97-stage2-18-corner-after-selfbias.md`), the nominal row-11 power re-report against #84, and the VCO swing/start-up re-check with the `cmo` load.
