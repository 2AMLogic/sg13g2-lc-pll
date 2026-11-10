# prescaler-div89 summary 20261110-182-cml-dff-latch-resize (issue #182)

**Result (simulated, not measured): a `cml_dff`-only latch variant `cml_dff_latch` (load `RL1/RL2` rppd 1u x 8.0u instead of 9.05u) closes the 108-unit chain grid (108 of 108 pass, /8 and /9 at 5.0 and 5.5 GHz, SLOW/TYP/FAST x -40/27/125 C x 2.970/3.300/3.630 V) but NOT the 288-unit async grid (285 of 288 pass; the 3 failures are all SLOW / 125 C / 5.5 GHz, 2.970 V phi=1200 ps and 3.630 V phi=0 and 1400 ps). Overall: FAIL, recorded. No spec row is relaxed and no decision record is filed: the failure is narrow enough that a further resize or a different fix is the next step (follow-up), not a stretch-band ceiling.**

All numbers below are simulated (ngspice 46 on the Spot batch fleet, sim/pins.json pin 47: known mismatch), never measured. Method of each grid is in the generated records (same decks, requests and grading as `20261109-234530-6fbbf0e-pdk-resistors.md`; `klt sim --backend batch --wait-for-capacity 600`).

## What changed
- New `design/cml_dff_latch.sch/.sym`: a copy of `cml_latch` with `RL1/RL2` at l = 8.0u. `design/cml_dff.sch` XM/XS point at it; `cml_latch` (used by `div2_cml_ls`) is untouched, so the two /2 stages are unchanged (the #168 bisection showed them not to be the cause).
- Netlists `design/netlist/prescaler.spice`, `pll_top.spice` regenerated with `design/netlist.sh`.
- rppd value, extracted as in `20261110-168-rl-bisection/rppd_extract.py` (DC op, 0.1 V): 1u x 8.0u = 2125 (typ, 27 C), 2161 (typ, 125 C), 2331 (wcs, 27 C), **2371 (wcs, 125 C)**, 1920 (bcs, 27 C), 1951 (bcs, 125 C) ohm. 8.2u (2428 at wcs / 125 C, the value in the issue's 2400-2450 target) was tried first.

## Result per latch length (same corners and grading)

| `cml_dff` latch RL | wcs/125 C value | chain fails (of 108) | async fails (of 288) | record |
|---|---|---|---|---|
| 9.05u (main, `6fbbf0e`) | 2673 | 6 | 32 | `20261109-234530-6fbbf0e-pdk-resistors.md` |
| 8.2u | 2428 | 2 (SLOW/125 C/5.5 GHz /8 at 2.970 and 3.300 V) | 17 (SLOW/125 C 2.970 V: 16 phases; 3.630 V: 1) | `20261110-182-cml-dff-latch-l8p2.md` |
| **8.0u (chosen)** | 2371 | **0** | **3** (all SLOW/125 C) | `20261110-182-cml-dff-latch-l8p0.md` |

Both new records are complete `div89_record.py` outputs with their `klt` reports. The 2400-2450 ohm target of the issue was not enough at 5.5 GHz / 2.970 V: 2428 still fails /8 (consistent with #168, where an ideal 2500 failed and 2400 passed). 8.0u was not searched further (threshold search is out of scope); TYP and FAST corners pass at both lengths, so lowering RL to 2125 (typ) / 1920 (bcs, 27 C) does not break them on this grid. Supply power over all 108 chain corners moves by 0.001-0.002 mW (max 7.378 mW against 7.377 mW before; within the 10 mW allocation).

## Re-checks asked by the issue
- **#160 (VCO load): NOT fully re-run; input capacitance re-measured.** `sim/vco-prescaler-load` needs `openvaf-r`, which this host lacks, so the VCO swing / startup result itself is not re-checked here and "the loop works" stays withheld. What was re-measured is the quantity it depends on: first-stage differential input capacitance by `cin_probe.spice.tmpl` (nominal TYP / 27 C / 3.3 V, one local `ngspice -b` each, rppd/rhigh loaded through `cornerRES.lib` + r3_cmc OSDI, which the stored probe deck omitted): main netlist 1.8878 fF at 5.0 GHz and 1.9970 fF at 5.5 GHz; with `cml_dff_latch` 1.8854 fF and 1.9948 fF (-0.002 fF). The resize does not change the load to the precision of this probe (nominal corner only). Note the PDK-resistor figure (1.89 / 2.00 fF) is itself above the 1.84 / 1.95 fF the #160 check used (ideal resistors), a pre-existing difference.
- **#165 (Vce): NOT re-checked, bench cannot run.** `sim/prescaler-g1/prescaler_vce.cir` includes the netlist with ideal-resistor assumptions and no rppd model, so after #164 every unit errors in the netlist (36 of 36 units errored in fleet job `klt-sim-65d0ed3220ce`, `unknown subckt` for rppd; the same bench against `main`'s netlist was not run, but main's netlist has the same rppd cards since #164); no Vce number is claimed. #165 stays open. Expected direction, reasoned and not simulated: the `XRL` drop in `cml_dff_latch` falls by about 11 % at a given tail current, which raises the latch devices' Vce (and does not touch the `mc_conv` `xqt` device #165 is about).
- **#58 (layout)**: the layout cells that contain `cml_dff` (`cml_div23` and the cells above it in `layout/`) are invalidated by this change, as the `rppd` geometry in `cml_dff`'s latches differs from `cml_latch`. They were not regenerated here; follow-up issue #187 filed. Other follow-ups: #186 (residual async failures), #188 (Vce bench lacks the rppd models).

## Not established
The stalling waveform node; the exact threshold between 2371 and 2428 ohm; the residual 3 SLOW / 125 C async failures (period 8.28/8.73 and "4 changes" sequences, i.e. retiming marginality not a stuck divider); noise / jitter (none computed).
