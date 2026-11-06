# mcounter bit 2 Q-bar tap plus second TC flop, implemented in the schematic: 17 of 18 stage-2 corners divide (2026-11-05, base `949ddd1`, issue #97)

**Result (simulated, not measured): PARTIAL, `fail` for the issue. First design change in the tree since the `cml2cmos` self-bias (#111) that moves a 125 C corner. 17 of 18 stage-2 corners divide to 50 MHz; SLOW 125 C 2.97 V and TYP 125 C 2.97 V still do not. The issue stays open: those 2 corners, the nominal row-11 power re-report, the `cmo` load / VCO re-check and `run-divider-elab.sh` are NOT done.**

## Change (in tree)
- `design/dff_tg_hv_qn.sch/.sym` (new): the pinned `dff_tg_hv` topology and devices verbatim, with the slave inverter output (the node that already drives `XBQ`) brought out as `QN`. A tap, no device added. Every other flop is still the pinned `dff_tg_hv`; the pinned cell is untouched.
- `design/mcounter.sch`: `XQ2` is `dff_tg_hv_qn` and drives `q2n` directly (`XIQ2` deleted); a second terminal-count flop `XFT2` (same `DT`, same `CK`) drives `TC2`, used only by the four load NANDs `XL0B..XL3B`. All other loads stay on `TC`/`TCN`.
- `design/netlist/divider.spice`, `design/netlist/pll_top.spice` regenerated with `design/netlist.sh` (`--check` clean). The netlist matches the one the reverted trial of `20261105-issue97-qn-tap-plus-tc2-trial.md` used.
- VCO netlist, `spec/` and the corner set untouched.

## Method
- 18 single-corner stage-2 shards (`request-stage2-97-s-*.json`, ramped start-up, `tran 4p 120n`, "divides" = `tfb` 58.5-61.5 ns) via `klt sim --batch-set ... --max-in-flight 4 --capacity-retries 3 --budget-s 3000 --backend batch`. 17 returned; SLOW 125 C 3.63 V was refused (`batch_no_capacity`, 30 pools), so it is taken from the four-corner 300 ns `request-diag125-97-*.json` run below (same netlist; 8 FB edges, steady 20.0 ns).
- The four 125 C `request-diag125-97-*.json` (300 ns) on the same netlist, to compare with the trial: FAST 2.97 V and SLOW 3.63 V divide (20.0 ns steady), SLOW 2.97 V and TYP 2.97 V have no FB edge in the window. Same result as the trial.
- One run per corner; repeatability not shown. ngspice 46 on the fleet against the pin of 47 (`sim/pins.json`): the pin is not met; nothing was run locally. Raw numbers: `20261105-issue97-mcounter-qn-tc2-in-tree-measurements.json`.

## Per-corner table ("divides" = `tfb` about 60.0 ns)
| process | T (C) | 2.97 V | 3.63 V |
|---|---|---|---|
| FAST | -40 / 27 / 125 | divides / divides / divides | divides / divides / divides |
| TYP | -40 / 27 | divides / divides | divides / divides |
| TYP | 125 | **converged, does not divide** (no `tfb`) | divides |
| SLOW | -40 / 27 | divides / divides | divides / divides |
| SLOW | 125 | **converged, does not divide** (no `tfb`) | divides (300 ns diag run) |

The 14 corners that divided before (`20261104-issue97-stage2-18-corner-after-selfbias.md`) still divide: no regression seen. FAST 125 C 2.97 V and SLOW 125 C 3.63 V newly divide.

Window-mean supply currents (include start-up; NOT a row-11 number): ip 1.76-2.03 mA, id 3.54-5.79 mA across the runs.

## Not done / owed (the issue stays open)
1. TYP and SLOW 125 C 2.97 V: the failing capture is not identified at these two (the bit trace of `20261105-issue97-bit-trace.md` was taken at FAST only). Next: that trace on the in-tree netlist.
2. Nominal row-11 power re-report against #84: no nominal point taken here; the cost of the added flop and the local flop is not isolated.
3. Load check: the change adds nothing to `cmo`; it adds one flop clock load on `CK` (`XFT2`), downstream of the clock buffer. VCO swing and start-up margin were NOT re-run with it, so the claim that the loop works is not made.
4. `scripts/run-divider-elab.sh` / `divider_counts.py` at nominal (needs a host that can load `psp103.osdi`).
