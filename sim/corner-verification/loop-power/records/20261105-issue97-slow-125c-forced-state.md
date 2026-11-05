# SLOW 125 C 2.97 V with the counter held in a valid state for 8-20 ns then released: it still does not divide (2026-11-05, base `8b33951`, issue #97)

**Result (simulated, not measured): PARTIAL, `fail` for the issue. No design change in this increment. This runs owed item 1 of `20261105-issue97-slow-125c-first-clock-trace.md`. The bad state reached from the 3 ns ramp is NOT shown to be the cause: with `q0..q3`, `b1..b3`, `tc`, `tcn` bench-forced to a state a dividing corner is in, SLOW 125 C 2.97 V still produces no FB edge after release. The divide-at-all-18 AC (17 of 18), the fix AC, the nominal row-11 power re-report, the `cmo` load / VCO re-check and `scripts/run-divider-elab.sh` remain NOT met.**

## Method
1. State snapshot (`make_state_snap_97.py`, `request-statesnap-97-FAST-125-2.97.json`, job `klt-sim-ffab567960cd`): FAST 125 C 2.97 V (divides on the in-tree netlist) at 50 ns: `q0..q3` = 1,1,0,1; `b1..b3` = 0,0,0; `tc` = 0; `tcn` = 1 (all rails to within 3 mV).
2. Forced trial (`make_forced_state_97.py`, body `loop_power_body_forced97.spice`, `request-forced-97-SLOW-125-2.97.json`, job `klt-sim-4271629163d3`): the body of the stage-2 request plus one B current source per node, 200 ohm to the target level, active 8-20 ns (after the 3 ns ramp), zero otherwise. Bench only; no design file touched. Unchanged ramped start-up, `tran 4p 120n`, in-tree netlist. Fleet batch backend; ngspice 46 against the pin of 47 (`sim/pins.json`): the pin is not met; nothing was run locally. One run each, repeatability not shown. Converged (179 s). Raw: `20261105-issue97-slow-125c-forced-state-measurements.json`.

## Result
| quantity | value |
|---|---|
| `tfb` (3 FB periods after 40 ns) | not reached |
| `tfb_late` (2 FB periods after 60 ns) | not reached |
| `fbmax`, 30-120 ns | 1.3 mV (FB never rises) |
| `q3` rise after 25 ns | none |
| `tc` rise after 25 ns | none |

## Reading
- After release at 20 ns, the counter still never raises `tc` and `q3` never rises again by 120 ns, as in the unforced run. A counter started in a state that is valid at another corner does not reach terminal count at this corner either. So an unreachable terminal-count cycle entered from the ramp is not supported as the cause; a corner-specific timing failure in the counter logic at SLOW 125 C 2.97 V is the remaining reading (inferred from outcome, not probed).
- Limit: the forcing was not probed during 8-20 ns, so that the nodes actually reached the target levels through 200 ohm against the flop drive is not shown. The `.meas` for `q3`/`tc` only cover after 25 ns. A weaker test than a probed one; it can not rule the start-up out on its own.

## Not done / owed (the issue stays open)
1. A probed repeat (bit trace across the hold and release, `b1..b3` included) to show the state was imposed, then which node first deviates from the FAST-corner sequence after release.
2. Which path is too slow at SLOW 125 C 2.97 V: per-stage delays in the load/borrow decode (`XL*`, `XP*`, `XA*/XB*`) against the 1.6-2.0 ns clock period.
3. TYP 125 C 2.97 V `DT` pulse width; any decode must keep `TC` a direct flop output (two inverter variants were rejected).
4. 18-corner re-run after any fix, nominal row-11 power re-report against #84, `scripts/run-divider-elab.sh` at nominal, `cmo` load / VCO swing and start-up re-check.
