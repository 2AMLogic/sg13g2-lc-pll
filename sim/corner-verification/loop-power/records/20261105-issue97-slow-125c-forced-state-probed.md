# SLOW 125 C 2.97 V forced-state trial, probed: forcing reached the target, the DT pulse falls between two clock edges and is never captured, cause not apportioned (2026-11-05, base `901250b`, issue #97)

**Result (simulated, not measured): PARTIAL, `fail` for the issue. No design change in this increment. This closes owed item 1 of `20261105-issue97-slow-125c-forced-state.md` (forcing not probed) and narrows item 2. The forcing reached the target state. After release `q0` toggles on most clocks with a few two-clock gaps, the `q0..q3` state sequence is irregular, and `DT` (43.95-44.84 ns) falls between clock rises (43.7, 45.3 ns), so `TC`/`TCN` never move. The cause is NOT established: a timing-margin shortfall on the terminal-count path and a state-sequence explanation both remain open, and the previous record's "unreachable terminal-count cycle" hypothesis is neither confirmed nor refuted. The divide-at-all-18 AC (17 of 18), the fix AC, the nominal row-11 power re-report, the `cmo` load / VCO re-check and `scripts/run-divider-elab.sh` remain NOT met.**

*Correction (review of PR #132): an earlier draft of this record read the rise-only `q0` row as "changes every 2nd-3rd clock" and concluded the counter flops miss clocks on the ordinary count path. That was a misread: a bit toggling every clock has a rise-to-rise spacing of 2 clocks (3.2 ns). Both edges are counted below.*

## Method
Same bench-only forcing as the previous record (`make_forced_state_97.py`: `q=1011`, `b=000`, `tc=0`, `tcn=1` through 200 ohm, 8-20 ns, then released; ramped start-up; in-tree netlist; `tran 4p`; SLOW 125 C 2.97 V). Two probe requests, one `klt sim --batch-set ... --backend batch` job each, one run each (repeatability not shown), both converged:
1. `make_forced_probe_97.py` -> `request-forcedprobe-97-SLOW-125-2.97.json`, job `klt-sim-a34c8683b795`: level of each forced node at 19 ns, and 1.485 V crossings 1..14 (from 14 ns) of `ckl`, `q0..q3`, `b1..b3`, `tc`, `tcn`, `d0..d3`, `dt`, `dtn`, `db1..db3`, window to 60 ns.
2. `make_forced_probe_97b.py` -> `request-forcedprobe2-97-SLOW-125-2.97.json`, job `klt-sim-4c3f0a7225ce`: crossings 1..16 (from 36 ns) of `ckl`, `q0..q3`, `dt`, `dtn`, `tc`, `tcn`, to 62 ns, to place the DT pulse against real clock edges.
Fleet batch backend, ngspice 46 against the pin of 47 (`sim/pins.json`): the pin is not met; nothing was run locally. The first submit was refused with `batch_no_capacity` (spot quota shared with ci-spot); a bounded `--wait-for-capacity` retry succeeded. Raw: `20261105-issue97-slow-125c-forced-state-probed-measurements.json`.

## Result
Forcing reached the target at 19 ns (V): `q0` 2.85, `q1` 2.97, `q2` 0.00003, `q3` 2.97, `b1` 0.105, `b2` 0.00004, `b3` 0.00003, `tc` 0.0008, `tcn` 2.97. So the counter was in the intended state when released; the earlier record's open limit ("forcing not probed") is closed. (`q0` at 2.85 V and `b1` at 0.105 V are a few percent off the rail, still the intended logic levels.)

Clock `ckl` rises every 1.60 ns from 14 ns (14.73, 16.38, ... 43.7, 45.3, 46.9 ns).

| node | crossings after release (ns), r = rise, f = fall |
|---|---|
| `q0` | 20.15f 22.23r 23.95f 25.54r 27.20f 28.76r 31.96f 33.54r 35.21f 36.77r 38.72f 41.47r 43.17f 44.74r 46.42f 47.99r 51.15f 52.74r 54.42f 55.98r 59.16f 60.74r |
| `q1` | 22.27f 25.37r 28.72f 31.78r 36.73f 39.79r 44.72f 47.79r 51.13f 52.70r 55.93f 58.99r |
| `q2` | 33.41r 41.66f 60.63r |
| `q3` | 33.52f 60.58r |
| `dt` rise / fall | 43.95, 55.18, 59.97 / 44.84, 56.04, 60.82 |
| `tc`, `tcn` | no crossing at all after 14 ns |

## Reading (inferred from the crossings of both edges; no path was probed gate by gate)
- `q0` toggles on most clocks. Successive `q0` changes from 36.77 ns are spaced 1.95, 2.75, 1.70, 1.57, 1.68, 1.57, 3.16, 1.59, 1.68, 1.56, 3.18 and 1.58 ns against a 1.60 ns clock; most are one period, three (2.75, 3.16, 3.18 ns) are about two. So there are occasional missed or held clocks, not a failed ordinary count path.
- State sequence, `q3q2q1q0` read as a number just before each clock rise (probe 1 to 35.7 ns, probe 2 from 37.3 ns; clock-to-Q about 1.0 ns is under the 1.60 ns period so each sample is the settled result of the previous edge): 11, 11, 11, 11 (forced, to 20 ns), 10, 9, 8, 11, 10, 9, 9, 10, 7, 6, 5, 4, 6, 3, 2, 1, 0, 3, 3, 0, 3, 2, 1, 1, 2, then 15 at 61.3 ns. Reads: a mostly descending count with reloads (8 to 11 near 26 ns, 0 to 3 at 48.5 and 53.3 ns), repeated states (9, 9; 3, 3; 1, 1: consistent with a held clock) and steps that a held clock does not explain (9 to 10, 4 to 6, 6 to 3, 1 to 2, 3 to 0). This matches the previous record's irregular sequence. The bit-level sample assumes all four bits have settled; it is derived from threshold crossings, not a logic-level dump.
- Clock to Q is about 1.0 ns here (e.g. clock rise 40.5 ns, `q0` rise 41.47 ns; clock rise 43.7 ns, `q0` rise 44.74 ns), about two thirds of the 1.60 ns period. Inferred from two edges, not a measured path delay.
- `dt` rises at 43.95 ns (0.25 ns after the clock rise at 43.7 ns) and falls at 44.84 ns, before the next rise at 45.3 ns. The pulse lies entirely between two edges, so the `TC`/`TC2`/`TCN` flops never see `dt` high at a capture: `tc` and `tcn` never move, the earlier "never presents terminal count". The same repeats at 55.18-56.04 and 59.97-60.82 ns.
- Cause not apportioned. Two readings both fit and are not separated here: (a) a timing-margin shortfall on the decode feeding `dt` (a pulse about 0.9 ns wide, shorter than the 1.60 ns period, with `dt` rising only 0.25 ns after a clock edge); (b) the counter is in a state sequence that is not the intended one (the irregular steps above), so the `dt` pulse is a symptom of that sequence. The previous record's "unreachable terminal-count cycle from start-up" is neither confirmed nor refuted. The TYP 125 C 2.97 V `DT` capture miss (`...tc-chain-two-125c-corners.md`) has the same shape; not tested here.
- Limits: one run per request; the gate-by-gate delay is not probed; the clock slew at the counter's `ckl` input is not separated from the flop delay; the state sequence is a derived read of crossings.

## Not done / owed (the issue stays open)
1. Discriminate (a) from (b) above: dump `q0..q3` logic levels per clock at SLOW 125 C 2.97 V and compare with the intended count sequence, and apportion the 1.60 ns: per-stage delays of one flop (clock to Q), and of the `XT1-XT4` decode and `XL*`/`XP*` NAND levels, at SLOW 125 C 2.97 V (single-corner request). Compare against FAST 125 C 2.97 V which divides.
2. A design change that buys period margin in the adopted counter cells (shorter decode depth, stronger or lighter-loaded flop outputs, or fewer loads on `q0`); any decode must keep `TC` a direct flop output (two inverter variants were rejected). Each trial must be confined to `design/*.sch` plus the regenerated `design/netlist/divider.spice`.
3. 18-corner re-run after any fix, nominal row-11 power re-report against #84, `scripts/run-divider-elab.sh` at nominal, and the `cmo` load / VCO swing and start-up re-check.
