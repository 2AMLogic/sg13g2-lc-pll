# Trial: TC and TC2 as inverters of TCN (replacing the DT-fed flops) makes four 125 C corners worse (2026-11-05, base `0e1af1f`, issue #97)

**Result (simulated, not measured): NEGATIVE. The change was not kept; no design file is changed in this increment.** Following `20261105-issue97-tc-chain-two-125c-corners.md` (TYP 125 C 2.97 V: `TCN` captures, `TC`/`TC2` fed from the narrower `DT` pulse do not), `XFT` and `XFT2` were replaced by two `inv_hv` driven from `TCN`, and `XT4` (DTN -> DT) was removed. The patch is `20261105-issue97-tc-from-tcn-inverter-trial.patch` (`design/mcounter.sch` + regenerated `design/netlist/divider.spice` through `klt netlist`).

## Method
Single-corner stage-2 requests (`request-stage2-97-s-*`, ramped start-up, unchanged) for the four 125 C corners, submitted with `klt sim --batch-set` to the batch fleet (no local ngspice). ngspice 46 on the fleet against the pin of 47 (`sim/pins.json`). One run per corner, repeatability not shown. Raw: `20261105-issue97-tc-from-tcn-inverter-trial-measurements.json`.

## Result
| corner | `tfb` | `fbmax` (V) | reading |
|---|---|---|---|
| TYP 125 C 2.97 V | not reached | 0.004 | FB never rises: does not divide |
| SLOW 125 C 2.97 V | not reached | 0.001 | does not divide (as before) |
| FAST 125 C 2.97 V | not reached | 0.006 | **regression**: divided before this change |
| TYP 125 C 3.63 V | not reached | 3.72 | FB toggles, 3-period window not met: not a 50 MHz divide; **regression** on the 17-of-18 baseline |

Four converged runs, none divides. Two corners that divided on the in-tree netlist stop dividing.

## Reading
- Removing the DT-fed flops is not neutral: `TC`/`TC2` now come one inverter delay after `TCN`'s clock-to-Q instead of from their own flop, and `TCN` carries two more loads. The `TC` consumers (`XP1A`..`XP3A` AND the borrow-load path) and the `TC2` load NANDs see the terminal count later, which the cycle apparently cannot absorb at 125 C. The mechanism is inferred from the outcome, not probed (no per-node trace taken).
- So the DT pulse width is not the only lever, and decoding `TC` from `TCN` is rejected as a fix.

## Still owed (issue stays open)
1. A different fix for the TYP 125 C 2.97 V `DT` capture miss (e.g. widen or retime the `DT` decode in `XT1..XT3`, or a per-node trace of why SLOW `q3`/`q2` are stuck).
2. 18-corner re-run, nominal row-11 power re-report against #84, `scripts/run-divider-elab.sh` at nominal, `cmo` load / VCO swing and start-up re-check.
