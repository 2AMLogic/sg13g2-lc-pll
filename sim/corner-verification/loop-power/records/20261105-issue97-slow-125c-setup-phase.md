# SLOW 125 C 2.97 V: counter D inputs settle 0.0-0.2 ns before the next clock edge (2026-11-05, base `28ea62f`, issue #97)

**Result (simulated, not measured): PARTIAL, `fail` for the issue. No design change and no new simulation in this increment: it re-reads the crossings already recorded in `20261105-issue97-slow-125c-forced-state-probed-measurements.json` (probe 1, job `klt-sim-a34c8683b795`, ngspice 46 against the pin of 47, `sim/pins.json`). It narrows owed item 1 of `20261105-issue97-slow-125c-forced-state-probed.md`: reading (a), a timing-margin shortfall on the counter feedback paths, is supported; reading (b), an unintended state sequence, is not excluded, because a miscapture itself produces an irregular sequence. The divide-at-all-18 AC (17 of 18), the fix AC, the nominal row-11 power re-report, the `cmo` load / VCO re-check and `scripts/run-divider-elab.sh` remain NOT met.**

## Method
`analyze_setup_phase_97.py` (new, reads the JSON only; output `20261105-issue97-slow-125c-setup-phase-analysis.json`). For each D node, each 1.485 V crossing between 20.5 ns (after the 8-20 ns forcing is released) and 35.7 ns (end of the recorded `ckl` window) is placed after the last `ckl` rise. Clock period over that window: 1.613 ns (14 rises). One run, repeatability not shown. Crossings are at VDD/2 of the node, not the flop's capture threshold; the flop's setup time was not measured.

## Result: time of each D transition after the launching clock rise (ns; period 1.613 ns)
| node | transitions |
|---|---|
| `d0` | 0.90 1.41 1.50 1.51 1.53 1.54 1.55 1.58 1.59 |
| `d1` | 1.19 1.23 1.37 1.37 1.39 1.54 |
| `d2` | 1.03 1.19 1.37 |
| `d3` | 1.33 |
| `db1` | 1.36 1.43 1.44 1.45 1.47 1.47 1.51 1.52 |
| `db2` | 0.14 0.16 1.34 1.39 |
| `db3` | 0.12 0.15 1.34 1.35 |
| `dt`, `dtn` | no transition in the window |

## Reading (inferred; no path probed gate by gate)
- Seven of nine `d0` transitions and the `db1` transitions complete 1.43-1.59 ns after the launching edge, that is 0.02-0.18 ns before the next rise. With a clock to Q of about 1.0 ns (previous record), the `q0` to `D0` / `DB1` logic (an inverter and two NAND levels) is left roughly 0.5-0.6 ns. These nodes are within a tenth of a nanosecond of the capture edge at this corner.
- The `db2`/`db3` transitions at 0.12-0.16 ns are the same edge's glitch, and the 1.34-1.39 ns ones are the settled values; `d1`..`d3` settle 1.2-1.5 ns after the edge. So every counter feedback path has little or no margin here, not one path only.
- What this does not show: the flop's setup time (a D settling 0.02 ns early may or may not be captured), the same measure at FAST 125 C 2.97 V (which divides), or that the miscaptures are the cause rather than a consequence of the irregular states. A margin of this size is consistent with the occasional two-clock `q0` gaps in the previous record, nothing more.

## Not done / owed (the issue stays open)
1. The same placement at FAST 125 C 2.97 V and TYP 125 C 2.97 V (single-corner probe requests, same window) to show whether the margin there is clearly larger, and a measured flop setup time at SLOW 125 C 2.97 V.
2. A design trial that buys period margin on the `q0` -> `D0` / `DB1` paths in the adopted counter cells (fewer logic levels, or a lighter load on `q0`); any decode must keep `TC` a direct flop output. Confined to `design/*.sch` plus the regenerated `design/netlist/divider.spice`; if timing at SLOW 125 C 2.97 V cannot close at 625 MHz in these cells, file the decision with this evidence (AC 3).
3. 18-corner re-run after any fix, nominal row-11 power re-report against #84, `scripts/run-divider-elab.sh` at nominal, and the `cmo` load / VCO swing and start-up re-check.
