# Two 125 C 2.97 V corners that still do not divide fail by two different mechanisms; TYP is a terminal-count (DT -> TC) capture miss (2026-11-05, base `1d3349d`, issue #97)

**Result (simulated, not measured): PARTIAL, `fail` for the issue. No design change in this increment. On the in-tree netlist (q2 Q-bar tap + second TC flop, `20261105-issue97-mcounter-qn-tc2-in-tree.md`) the owed bit trace was taken at TYP 125 C 2.97 V and SLOW 125 C 2.97 V. The two corners do not share a cause. TYP: the counter counts down correctly 11 -> 0, but `TC` and `TC2` never rise although `TCN` does; the `DT` pulse that feeds the TC flops is narrower and ends about 0.45 ns earlier than the `DTN` pulse that feeds the TCN flop, which does capture. SLOW: `q3` and `q2` never toggle in 262-302 ns, `DT` never rises, `DTN` and `TCN` stay high, so the counter sits in a state that never reaches terminal count. The divide-at-all-18 AC (17 of 18 divide), the fix AC, the nominal row-11 power re-report, the `cmo` load / VCO re-check and `run-divider-elab.sh` remain NOT met.**

## Method
- `make_bit_trace_97b.py` -> `request-bittrace2-97-{TYP,SLOW}-125-2.97.json`: 1.485 V crossings 1..16 of `ckl`, `tc`, `tc2`, `q2n`, `q0..q3`, `d0..d3`; window 40-80 ns (TYP) and 262-302 ns (SLOW), ramped start-up, `tran 4p`. Fleet jobs `klt-sim-3a8120969868`, `klt-sim-35e750fe323c`.
- `make_tc_levels_97.py` -> `request-tclevels-97-*.json`: max/min and 0.5 V / 2.5 V crossings of `dt`, `dtn`, `tc`, `tcn`, `tc2` over the same windows (same fleet, `--backend batch`).
- One run per corner per request, repeatability not shown. ngspice 46 on the fleet against the pin of 47 (`sim/pins.json`): the pin is not met; nothing was run locally. Logic levels in the tables below are reconstructed from 1.485 V crossings, taken 50 ps before each `ckl` rise. Raw: `20261105-issue97-tc-chain-two-125c-corners-measurements.json`.

## TYP 125 C 2.97 V
State `q3q2q1q0` before each `ckl` rise (40.2 ns on): 1011, 1010, 1001, 1000, 0111, 0110, 0101, 0100, 0011, 0010, 0001 (clock 11, 56.2 ns), **0000, 0001, 0000, 1111**, 1110, 1101. The count from the load value is correct down to 0001. At 0001 the next state should be the reload; `D` instead reads 0000 (clock 11), 0001 (clock 12), 0000 (clock 13), then 1111: the counter free-runs down past zero.

| node | max / min (V) | crossings (ns) |
|---|---|---|
| `dt` | 3.01 / -0.11 | pulse above 2.5 V 54.89-55.63; above 0.5 V 54.61-56.05 |
| `dtn` | 3.05 / 0.001 | below 2.5 V 54.29-56.08; below 0.5 V 54.69-55.77 |
| `tc` | **0.029 / -0.048** | none (never rises) |
| `tc2` | **0.003 / -0.003** | none (never rises) |
| `tcn` | 3.16 / -0.010 | falls to the rail, 56.02-56.99 (0.5 V), 55.49-57.58 (2.5 V) |

- `DT` and `DTN` are decodes of the same state (0010 before clock 10 at 54.598 ns). The `DT` high pulse is 0.74 ns wide at 2.5 V and ends at 55.63; the `DTN` low pulse is 1.79 ns wide at 2.5 V and ends at 56.08, so `DT` leaves about 0.45 ns earlier. The next `ckl` rise is 56.199.
- `TCN` (flop `XFTN`, D = `DTN`) captures; `TC` (`XFT`) and `TC2` (`XFT2`), both D = `DT`, do not. Same flop cell, same clock, so the difference is the data pulse, not the flop.
- Reading: the terminal-count capture margin is set by the `DT` pulse, whose width is about a third of the clock period at this corner. Candidate (not tested): the `DT` decode glitches through a reconvergent path, ending before the capture instant. A fix is not tried here.

## SLOW 125 C 2.97 V
| node | max / min (V) | crossings |
|---|---|---|
| `dt` | 0.064 / -0.109 | none |
| `dtn`, `tcn` | 3.05 / 2.83, 3.10 / 2.91 | none (stay high) |
| `tc`, `tc2` | 0.028 / -0.047, 0.001 / -0.001 | none |

- `q2`, `q3`, `d2`, `d3`: no crossing in 262-302 ns. `q0`/`q1` toggle with a 7-clock repeat (as in `20261104-issue97-125c-diagnosis.md`). The terminal-count state is never presented, so `DT` never fires. The wrong capture of `TC` seen at TYP is not the cause here.
- Whether the stuck state is reached from the start-up ramp (an invalid state the counter cannot leave) or is entered during running is not separated; the window starts at 262 ns. Not tested: nominal-start-up variant, and a window from the first clock.

## Not done / owed (the issue stays open)
1. A fix for the TYP `DT` pulse (e.g. decode through a path that does not glitch, or capture on the pulse's settled level), then the four 125 C corners singly. Not attempted.
2. SLOW 125 C 2.97 V: why `q3`/`q2` are stuck; a window from the first clock, and the `b1..b3` borrow flops.
3. The 18-corner re-run after any fix, the nominal row-11 power re-report against #84, `scripts/run-divider-elab.sh` at nominal, and the VCO swing / start-up re-check with the `cmo` coupling-cap load and the extra `CK` flop load.
