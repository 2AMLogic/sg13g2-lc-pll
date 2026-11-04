# Two-inverter delay on every counter flop D input: changes the 125 C behaviour, divides nowhere (2026-11-04, base `69ad30a`, issue #97)

**Result (simulated, not measured): REFUTATION of "a master/slave hold race on the q -> logic -> D paths is the whole cause", `fail` for the issue. A trial netlist change put two `inv_hv` in series (about one extra gate-pair delay) ahead of the D pin of all 9 `mcounter` and 3 `acounter` `dff_tg_hv` flops. At the four 125 C corners that previously did not divide, no corner divides to 50 MHz (FB period 20 ns); the trial was reverted and is not in the tree. The divide-at-all-18 AC, the fix AC and the row-11 power re-report remain NOT met.**

- **Candidate tested**: the adopted flop closes its master (`CLKB` falling / `CKBB` rising, skewed by 120-144 ps at SLOW 125 C, see `20261104-issue97-125c-diagnosis.md`) while its slave opens. A q change that reaches a D pin through 2-3 gates faster than that skew would be captured by the wrong flop state (hold violation), giving a wrong modulus. Adding delay on D should cure a hold-limited counter.
- **Method**: the four single-corner requests of the 125 C diagnosis (`request-diag125-97-<proc>-<vdd>.json`, unchanged: ramped start-up, 300 ns) run with `klt sim --batch-set ... --max-in-flight 4 --backend batch` against the trial `design/netlist/divider.spice` (netlist-only edit; `divider.sch` untouched). Each corner ran once; repeatability not shown. Jobs: FAST 2.97 V `klt-sim-697a98da64f3`, SLOW 3.63 V `klt-sim-a2006dd19357`, TYP 2.97 V `klt-sim-afd50d62e6fd`, SLOW 2.97 V `klt-sim-be2759e7b4d2`. Raw numbers: `20261104-issue97-d-delay-hold-trial-measurements.json`. ngspice 46 on the fleet against the pin of 47 (`sim/pins.json`): the pin is not met; nothing was run locally.

| corner (125 C) | FB period before (ns) | with D delay: FB rising edges (ns) | class |
|---|---|---|---|
| FAST 2.97 V | 26.4 | 50.1, 72.9, 95.7, ... steady 22.8 | converged, divides by ~114, not 100 |
| SLOW 3.63 V | 26.4 | 51.0, 73.8, 96.2, ... steady 22.8 | converged, divides by ~114, not 100 |
| SLOW 2.97 V | none (stuck) | 60.6, 95.0, 129.4, 150.9, 172.5, ... (34.4, 34.4, 21.5, 21.6) | converged, reaches TC, period erratic, not 20 ns |
| TYP 2.97 V | 28.8 | no edge; FB within +-1.4 mV, TC max 24 mV | converged, stuck (worse than before) |

## What this does and does not show

- The delay moves the modulus toward 12.5 clocks at FAST and SLOW 3.63 V (16.5 -> 14.25 clocks) and un-sticks SLOW 2.97 V, so a timing mechanism between flop outputs and D inputs is real. It does not close any corner, and TYP 2.97 V gets worse, so hold is not the only term; setup slack shrinks with the same delay (1.6 ns period).
- The behaviour is still not traced to a gate. A clock-aligned waveform trace of the reload path at one corner (owed in the previous record) remains the discriminating measurement; a blind structural trial is now the third that did not close.
- No power number was taken, so #84 is not touched (the trial adds 24 `inv_hv`).

## Not done / owed (the issue stays open)

1. Gate-level reload-path trace (waveform output) at FAST 125 C 2.97 V against TYP 27 C 2.97 V.
2. A fix, then the 18-corner re-run, the nominal row-11 power re-report against #84, and the VCO swing/start-up re-check with the `cmo` load.
