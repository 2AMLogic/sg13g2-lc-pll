# SLOW 125 C 2.97 V forced-state trial, probed: the counter flops capture only every 2nd-3rd clock, and the DT pulse falls between two clock edges (2026-11-05, base `901250b`, issue #97)

**Result (simulated, not measured): PARTIAL, `fail` for the issue. No design change in this increment. This closes owed items 1 and 2 (in part) of `20261105-issue97-slow-125c-forced-state.md`. The forcing is shown to have reached the target state, and the failure after release is read as a clock-period timing failure of the counter at this corner, not an unreachable state cycle. The divide-at-all-18 AC (17 of 18), the fix AC, the nominal row-11 power re-report, the `cmo` load / VCO re-check and `scripts/run-divider-elab.sh` remain NOT met.**

## Method
Same bench-only forcing as the previous record (`make_forced_state_97.py`: `q=1011`, `b=000`, `tc=0`, `tcn=1` through 200 ohm, 8-20 ns, then released; ramped start-up; in-tree netlist; `tran 4p`; SLOW 125 C 2.97 V). Two probe requests, one `klt sim --batch-set ... --backend batch` job each, one run each (repeatability not shown), both converged:
1. `make_forced_probe_97.py` -> `request-forcedprobe-97-SLOW-125-2.97.json`, job `klt-sim-a34c8683b795`: level of each forced node at 19 ns, and 1.485 V crossings 1..14 (from 14 ns) of `ckl`, `q0..q3`, `b1..b3`, `tc`, `tcn`, `d0..d3`, `dt`, `dtn`, `db1..db3`, window to 60 ns.
2. `make_forced_probe_97b.py` -> `request-forcedprobe2-97-SLOW-125-2.97.json`, job `klt-sim-4c3f0a7225ce`: crossings 1..16 (from 36 ns) of `ckl`, `q0..q3`, `dt`, `dtn`, `tc`, `tcn`, to 62 ns, to place the DT pulse against real clock edges.
Fleet batch backend, ngspice 46 against the pin of 47 (`sim/pins.json`): the pin is not met; nothing was run locally. The first submit was refused with `batch_no_capacity` (spot quota shared with ci-spot); a bounded `--wait-for-capacity` retry succeeded. Raw: `20261105-issue97-slow-125c-forced-state-probed-measurements.json`.

## Result
Forcing reached the target at 19 ns (V): `q0` 2.85, `q1` 2.97, `q2` 0.00003, `q3` 2.97, `b1` 0.105, `b2` 0.00004, `b3` 0.00003, `tc` 0.0008, `tcn` 2.97. So the counter was in the intended state when released; the earlier record's open limit ("forcing not probed") is closed. (`q0` at 2.85 V and `b1` at 0.105 V are a few percent off the rail, still the intended logic levels.)

Clock `ckl` rises every 1.60 ns from 14 ns (14.73, 16.38, ... 43.7, 45.3, 46.9 ns).

| node | crossings after release (ns) |
|---|---|
| `q0` rise | 22.23 25.54 28.76 33.54 36.77 41.47 44.74 47.99 52.74 55.98 60.74 |
| `q1` rise | 25.37 31.78 39.79 47.79 52.70 58.99 |
| `q2` rise / fall | 33.41, 60.63 / 41.66 |
| `q3` rise / fall | 60.58 / 33.52 |
| `dt` rise / fall | 43.95, 55.18, 59.97 / 44.84, 56.04, 60.82 |
| `tc`, `tcn` | no crossing at all after 14 ns |

## Reading (inferred from the crossings; no path was probed gate by gate)
- With clock edges 1.60 ns apart, `q0` changes only every 3.2-4.8 ns (every 2nd to 3rd clock), `q1` every 5-8 ns. A flop that captured every edge would change at each one for the low bits of a counter. So the counter flops are missing clocks: not only terminal count but the ordinary count path.
- Clock to Q is about 1.0 ns here (e.g. clock rise 40.5 ns, `q0` rise 41.47 ns; clock rise 43.7 ns, `q0` rise 44.74 ns), i.e. about two thirds of the 1.60 ns period, leaving about 0.5 ns for the load/borrow/decode logic plus setup. That is inferred from two edges, not measured as a path delay.
- `dt` rises at 43.95 ns (0.25 ns after the clock rise at 43.7 ns) and falls at 44.84 ns, before the next rise at 45.3 ns. The pulse lies entirely between two edges, so the `TC`/`TC2`/`TCN` flops never see `dt` high at a capture: `tc` and `tcn` never move, which is the earlier "never presents terminal count". The same repeats at 55.2-56.0 and 60.0-60.8 ns.
- Together with the previous record (a state that other corners are in does not rescue this corner), the reading is a corner-specific clock-period timing failure of the counter flops and their decode at SLOW 125 C 2.97 V. The previous record's "unreachable terminal-count cycle from start-up" is not supported. The TYP 125 C 2.97 V `DT` capture miss (`...tc-chain-two-125c-corners.md`) has the same shape and is plausibly the same margin shortfall at a smaller scale; not tested here.
- Limits: one run per request; the gate-by-gate delay is not probed, so which stage dominates (flop clock-to-Q, the `XL*`/`XP*` NAND levels, or the `XT*` decode) is not apportioned; the clock slew at the counter's `ckl` input (the `cml2cmos` + buffer output) is not separated from the flop delay.

## Not done / owed (the issue stays open)
1. Apportion the 1.60 ns: per-stage delays of one flop (clock to Q), and of the `XT1-XT4` decode and `XL*`/`XP*` NAND levels, at SLOW 125 C 2.97 V (single-corner request). Compare against FAST 125 C 2.97 V which divides.
2. A design change that buys period margin in the adopted counter cells (shorter decode depth, stronger or lighter-loaded flop outputs, or fewer loads on `q0`); any decode must keep `TC` a direct flop output (two inverter variants were rejected). Each trial must be confined to `design/*.sch` plus the regenerated `design/netlist/divider.spice`.
3. 18-corner re-run after any fix, nominal row-11 power re-report against #84, `scripts/run-divider-elab.sh` at nominal, and the `cmo` load / VCO swing and start-up re-check.
