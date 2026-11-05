# SLOW 125 C 2.97 V from the first clock: the M counter is not frozen, it free-runs with an irregular sequence and never presents terminal count (2026-11-05, base `4718b20`, issue #97)

**Result (simulated, not measured): PARTIAL, `fail` for the issue. No design change in this increment. This closes owed item 2 of `20261105-issue97-tc-chain-two-125c-corners.md` (a window from the first clock and the `b1..b3` borrow flops). The earlier reading "q3/q2 are stuck" (window 262-302 ns) is refined: from the first clock the counter does move, but its bits change at irregular, far-too-long intervals, and `TC`/`TCN` are never presented after start-up. The divide-at-all-18 AC (17 of 18 divide), the fix AC, the nominal row-11 power re-report, the `cmo` load / VCO re-check and `scripts/run-divider-elab.sh` remain NOT met.**

## Method
`make_bit_trace_97c.py` -> `request-bittrace3-97-SLOW-125-2.97.json`: 1.485 V rise/fall crossings 1..12 of `ckl`, `q0..q3`, `b1..b3`, `tc`, `tcn`, window 0-90 ns, ramped start-up (unchanged body), in-tree netlist (q2 Q-bar tap + second TC flop), `tran 4p 90n`. One `klt sim --batch-set ... --backend batch` job `klt-sim-ee5bca5bd01b`, one run (repeatability not shown). ngspice 46 on the fleet against the pin of 47 (`sim/pins.json`): the pin is not met; nothing was run locally. Raw: `20261105-issue97-slow-125c-first-clock-trace-measurements.json`. Converged.

## Result (ns, 1.485 V crossings)
| node | rises | falls |
|---|---|---|
| `ckl` | 2.13 7.11 9.16 11.18 13.20 14.73 16.38 18.02 ... (period 1.6-2.0 ns from 14 ns) | 6.26 8.20 10.18 ... |
| `q0` | 2.04 10.13 14.17 17.54 22.30 25.53 28.78 33.54 36.77 ... | 8.16 12.23 15.96 20.69 23.96 ... |
| `q1` | 2.01 10.04 17.29 22.23 28.58 33.49 39.79 47.79 55.79 ... | 8.12 14.20 20.65 25.50 ... |
| `q2` | 2.14 41.41 68.63 | 10.23 49.60 76.79 |
| `q3` | 2.02 68.58 | 41.52 |
| `b2` | 1.94 39.73 47.73 66.93 74.92 | 10.10 41.47 49.45 68.67 76.64 |
| `b3` | 1.94 39.73 66.93 | 8.06 41.45 68.66 |
| `tc` | 2.07 | 8.22 |
| `tcn` | 2.05 | none (never falls) |

## Reading
- `ckl` runs at about 1.6 ns from 14 ns, so ~55 clock edges happen before 90 ns. In that time `q2` changes five times and `q3` twice. A mod-N counter at this clock would change `q2` every few clocks. So the counter is advancing, but through a sequence whose bits `q2`/`q3` move 30-40 ns apart, not through the intended 11 -> 0 reload cycle.
- `tc` rises once at 2.07 ns and falls at 8.22 ns (start-up, before the ramp finishes); it never rises again in 90 ns. `tcn` never falls. So terminal count is never captured after start-up: the load/reload is never triggered, which matches `DT` never rising in the 262-302 ns window of the earlier trace. The counter is in a state cycle that does not contain the terminal-count state.
- The first 10 ns (ramp) already put `b1..b3`/`q0..q3` into a state that does not converge to the intended cycle: `q0`/`q1`/`b1` fall at 8-10 ns on a clock whose edges are 2 ns apart. This points to a start-up/initial-state problem (an invalid state with no path to the terminal-count state) rather than the TYP-style capture miss. Not shown: that the same netlist started from a valid state at this corner counts correctly (a `.ic` / nodeset variant), which would separate the two. That is the next trial.
- Whether the invalid-state cycle also exists at the other corners (they divide, so it is either not reached or is escaped) is not shown.

## Not done / owed (the issue stays open)
1. SLOW 125 C 2.97 V with the counter state forced to a valid state at t = 0 (`.ic` on `q0..q3`, `b1..b3`) to separate an unreachable terminal-count cycle from a corner-specific timing failure; then a reset/self-correcting decode if it is the former.
2. TYP 125 C 2.97 V `DT` pulse width (see `20261105-issue97-tc-chain-two-125c-corners.md`); two TC-via-inverter trials were rejected, so it needs a decode that keeps `TC` a direct flop output.
3. The 18-corner re-run after any fix, the nominal row-11 power re-report against #84, `scripts/run-divider-elab.sh` at nominal, and the `cmo` load / VCO swing and start-up re-check.
