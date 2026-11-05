# FAST and TYP 125 C 2.97 V: the DT pulse arrives 0.03 / 0.15 ns after the capture edge, SLOW 0.25 ns, only FAST captures it (2026-11-05, base `78eb824`, issue #97)

**Result (simulated, not measured): PARTIAL, `fail` for the issue. No design change. This closes owed item 1 of `20261105-issue97-slow-125c-setup-phase.md` for the FAST and TYP corners (the same probe as SLOW 125 C 2.97 V, one run each, both converged). The comparison supports a timing-margin shortfall on the terminal-count decode (`DT`) path and does not support a margin shortfall on every counter feedback path. The measured flop setup time is still not known. The divide-at-all-18 AC (17 of 18 per the earlier records), the fix AC, the nominal row-11 power re-report, the `cmo` load / VCO re-check and `scripts/run-divider-elab.sh` remain NOT met.**

## Method
`make_forced_probe_97c.py` copies `request-forcedprobe-97-SLOW-125-2.97.json` (same bench-only forcing `q=1011, b=000, tc=0, tcn=1` through 200 ohm for 8-20 ns, ramped start-up, in-tree netlist, `tran 4p 60n`, same 1.485 V crossing probes from 14 ns) and swaps in the FAST and TYP 125 C 2.97 V corner blocks. One `klt sim --batch-set ... --backend batch` call, two jobs: FAST `klt-sim-e13490345a26`, TYP `klt-sim-852bbb879e23`; nothing run locally. Fleet engine ngspice 46 against the pin of 47 (`sim/pins.json`): the pin is not met. One run each, repeatability not shown. `analyze_setup_phase_97b.py` (reads the saved crossings only) places each D-node transition after the last `ckl` rise, as `analyze_setup_phase_97.py` did for SLOW. Raw: `20261105-issue97-fast-typ-125c-setup-phase-measurements.json`; phases: `...-analysis.json`.

Forcing reached the target at 19 ns in both runs (`q0` 2.81 / 2.83 V, `q1` and `q3` at 2.97 V, `q2`, `b2`, `b3`, `tc` near 0, `tcn` 2.97 V, `b1` 0.14 / 0.13 V). Clock period over the window: FAST 1.606 ns, TYP 1.611 ns (SLOW 1.613 ns).

## Result: latest settling transition of each D node after the launching clock rise (ns)
| node | FAST (divides) | TYP (does not) | SLOW (does not) |
|---|---|---|---|
| `d0` | 1.29 | 1.40 | 1.59 |
| `d1` | 1.13 | 1.20 | 1.54 |
| `d2` | 1.29 | 1.29 | 1.37 |
| `d3` | 1.29 | 1.22 | 1.33 |
| `db1` | 1.48 | 1.31 | 1.52 |
| `db2` | 1.49 | 1.59 | 1.39 |
| `db3` | 1.43 | 1.57 | 1.35 |

`DT` pulse against the clock (rise-edge phase is the crossing time after the clock rise it follows):
| corner | `dt` rise (after edge) | `dt` fall | next clock rise | `tc` |
|---|---|---|---|---|
| FAST | 34.74 ns (0.03) | 36.06 ns | 36.31 ns | rises 35.81 ns, 1.10 ns after the 34.71 ns edge |
| TYP | 33.95 ns (0.15) | 34.92 ns | 35.40 ns | no crossing (first `dt` pulse in the window) |
| SLOW (previous record) | 43.95 ns (0.25) | 44.84 ns | 45.30 ns | no crossing |

## Reading (inferred from crossings; no path probed gate by gate, flop setup time not measured)
- The three corners do not rank the same on every D node. `d0`/`d1`/`db1` are worst at SLOW (1.52-1.59 ns), matching the previous record; but `db2`/`db3` settle latest at TYP (1.57-1.59 ns, against 1.35-1.39 at SLOW) and TYP does not divide while FAST (1.43-1.49 ns) does. So "every feedback path has little margin at the failing corners" is not what the three corners show; the previous record's second bullet is narrowed, not confirmed.
- The one quantity that orders the three corners the way divide / no divide does is the `DT` arrival relative to the capture edge: 0.03 ns after at FAST, 0.15 at TYP, 0.25 at SLOW. In FAST `tc` follows that edge by 1.10 ns (about the clock-to-Q seen elsewhere), so the pulse was taken at the edge where it was about to rise; in TYP and SLOW it rises after the edge and falls (0.97 and 0.89 ns wide) 0.48 and 0.46 ns before the next edge, so no edge sees it high. Counting from the launching edge, the `DT` path takes about 1.63 ns at FAST, 1.75 ns at TYP and 1.85 ns at SLOW against a period of 1.61 ns: one clock-to-Q plus the decode exceeds one period at TYP and SLOW. Which edge launched each `DT` transition is assumed (the one preceding the crossing minus one period), not traced.
- Margin at FAST is itself about zero (0.03 ns), consistent with FAST 125 C 2.97 V being the last corner that divides; a measured flop setup time could move that either way.
- Limits: crossings at VDD/2 of each node, not the flop's capture threshold; one run each; the TYP run has one `dt` pulse in its window; the counter state sequence at FAST/TYP was not reconstructed here; the `cmo` load / VCO re-check is not part of this probe.

## Not done / owed (the issue stays open)
1. A design trial that shortens the `DT` path by about 0.3 ns at 125 C 2.97 V (fewer decode levels from `q0..q3` to `dt`, or lighter load on the `q` outputs) in the adopted counter cells; `TC` must stay a direct flop output (two inverter variants were rejected). Confined to `design/*.sch` plus the regenerated `design/netlist/divider.spice`. If the path cannot close at 625 MHz at SLOW 125 C 2.97 V in these cells, file the decision with this evidence (AC 3).
2. A measured flop setup time at 125 C 2.97 V (SLOW/TYP) to turn the 0.03-0.25 ns offsets into a margin.
3. 18-corner re-run after any fix, nominal row-11 power re-report against #84, `scripts/run-divider-elab.sh` at nominal, and the `cmo` load / VCO swing and start-up re-check.
