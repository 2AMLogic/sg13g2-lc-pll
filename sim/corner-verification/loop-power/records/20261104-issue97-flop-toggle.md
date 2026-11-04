# An isolated dff_tg_hv toggles at 625 MHz at SLOW 125 C 2.97 V (2026-11-04, base `2754dab`, issue #97)

**Result (simulated, not measured): REFUTATION of one candidate, `fail` for the issue. A single adopted `dff_tg_hv` wired as a divide-by-2 (D = Q-bar) and clocked at the divider clock rate (1.6 ns period, 0.1 ns edges) toggles correctly at SLOW 125 C 2.97 V, the corner where the full M counter never reaches terminal count. The flop cell alone is therefore not what limits the counter at that corner. No design change; the divide-at-all-18 AC, the fix AC and the row-11 power re-report remain NOT met.**

- **Method**: `flop_toggle_body.spice` (one `dff_tg_hv` plus one `inv_hv`, same ramped supply as `loop_power_body.spice`, ideal pulse clock 0 to vddv), `request-flop-toggle-97.json`, `tran 4p 60n`, one corner, one run, `klt sim --backend batch` (job `klt-sim-200c98e07529`; the host cannot load `psp103.osdi`). ngspice 46 on the fleet against the pin of 47 (`sim/pins.json`): the pin is not met. Repeatability not shown.
- **Measured**: Q rising edges (1.485 V) at 12.72 ns (first, from 10 ns) and 44.72 ns (the 11th): 10 Q periods in 32.0 ns, 3.2 ns each, i.e. exactly two clocks. Q swings -0.062 V to 3.060 V over 40-60 ns.
- **What this does not show**: the flop is driven by an ideal source and loaded by one inverter. It says nothing about the flop with the counter's gate loading, the real `CKL` edge, or the TC -> NAND -> D reload path. Together with the clock-buffer record (stronger `CKL` drive changes nothing) and the TC-fanout record, the candidates left are the counter's logic timing (setup on the reload path under real fanout) and the reload/state logic itself.

## Not done / owed (the issue stays open)

1. A gate-level trace of the reload path in the full counter (a clock-aligned sampling grid or waveform output), at SLOW 125 C 2.97 V against a dividing reference.
2. A fix, then the 18-corner re-run, the nominal row-11 power re-report against #84 and the VCO swing/start-up re-check with the `cmo` load.
