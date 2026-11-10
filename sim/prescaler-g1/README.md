# sim/prescaler-g1

Gate G1 bench for `design/prescaler.sch` (spec row 4, section 1 tank-node load budget). One local
`ngspice -b`, **nominal corner only** (`hbt_typ`, 27 C, 3.3 V), stimulus 0.4 Vpp differential at common mode
3.3 V (the tank returns to VDD), ideal IREF = 50 uA, PDK `rppd` resistors (`res_typ`, r3_cmc OSDI).

```bash
scripts/run-prescaler-g1.sh              # writes records/<date>-<sha>.md
scripts/test-prescaler-g1-negative.sh    # starved stage and oversized input must be flagged
```

Reports at 5.0 GHz: differential input capacitance (fF) and shunt conductance (S) by AC small-signal at the
operating point, cross-checked by the fundamental of the input current in a large-signal transient; and the
max toggle frequency of the first stage `cml_div23` (divides by 2 at MC = 0; probe `x1.x89.c1/c1b`; one transient per input frequency, output must be at f/2 and >= 0.2 V pk-pk).
The capacitance is compared with the 2.1 fF budget in the record; a figure above it stands as a fail.

**Not graded here**: the budget is device plus routing over the C-grid; this is the device-level number at
one corner (routing, other corners, and the VCO re-check, gate G2, are outside). Simulated, not measured.

- `records/` is dated and append-only; a failed run is recorded too.
- Needs the pinned PDK (`sim/pins.json`), `jq`, `ngspice` (`NGSPICE`), `klt` (netlist drift check). ngspice is held to
  2 OpenMP threads on the shared host.
- `negative-control-*.txt`: output of `scripts/test-prescaler-g1-negative.sh`.

## HBT Vce against BVCEO over the supply sub-corners (`klt sim`)

`prescaler_vce.cir` + `prescaler_vce.request.json` (generated: `scripts/gen_prescaler_vce_request.py`, `--check` is in
`scripts/ci-harness.sh`) is a `klt sim` corner request: 18 supply sub-corners ({2.970, 3.630} V x {SLOW, TYP, FAST} x
{-40, 27, 125} C), one `vecmax(|Vce|)` measurement per HBT (all 95), graded against BVCEO 2.2 V min. The multi-corner
run goes to the batch fleet (`KLT_SIM_BACKEND=batch`), never a local ngspice loop:

```bash
cd sim/prescaler-g1 && PDK_ROOT=<parent of ihp-sg13g2> klt sim --format json -o <scratch> --report-out <scratch>/vce-report.json prescaler_vce.request.json
python3 vce_record.py --report <scratch>/vce-report.json --out-dir records --id <YYYYMMDD-HHMMSS>-<sha> --commit <sha>
```

`vce_record.py` grades the report and writes `records/<id>-vce.md` plus the klt report (gzip). A corner that did not
converge is never counted as a pass (verdict INCOMPLETE at best); any Vce over the rating is a FAIL. Tests (negative
controls on the grader): `test_vce_record.py`. If the batch submit fails, report the error; do not loop locally.

### Why the Vce record passes (issue #72)

The 20261103-021000 record failed (14 of 18 corners over 2.2 V, 4 not converged). Cause, from a per-device
transient dump: the emitter-follower current sources (`cml_ef`, `div2_ef_hs` QF1/QF2) have their collector on the
follower output, one Vbe below VDD, so Vce is about VDD - Vbe - 0.1 V; the latch / AND tail transistors (QT) and the
MC converter's off-side input transistor (QM1, collector at VDD, emitter one Vbe below VDD/2) carry similar stress.
Changes, all in this block: a diode-connected HBT plus a 4k resistor in series with each follower current source;
a 1.2k / 2.4k collector resistor on every latch/AND tail; the `mc_conv` reference divider moved from VDD/2 to
0.7 VDD (12k/28k). The 2.2 V limit is unchanged. The 125 C aborts were the bench's own `.ic` on the /2 output
nodes (see the comment in `prescaler_vce.cir`), not the circuit.

### Status for the `div89_dm` netlist (PR #161, issue #162)

The Vce records dated 20261103 were taken on the previous prescaler netlist and do not cover `div89_dm`; the
`20261106-224822-cf0dede-dirty` re-run is INCOMPLETE (stale `.ic`) and is superseded. The bench is reworked: power-up
ramp instead of `.ic`, and an `mcv` axis (0 = /8, 1 = /9 at the supply level) zipped with `vddv`, so the request is 36 runs
(18 sub-corners x MC low/high). `records/20261108-225549-330a5a2-vce.md`: 36 of 36 converged, **FAIL, 9 runs over 2.2 V, all at
3.63 V with MC high, device `x1.x89.xmc.xqt`** (worst 2.844 V); at 2.97 V all pass, worst 2.186 V (+0.014 V). See DR-005.

### Vce bench loads the PDK resistor models (issue #188)

Since the netlist carries PDK `rppd` resistors (not ideal ones), `prescaler_vce.skeleton.json` pairs each HBT corner with a
`cornerRES.lib` section (SLOW = `res_wcs`, TYP = `res_typ`, FAST = `res_bcs`) and sets `ngspice_init` (`set ngbehavior=hsa`) and
`osdi_preload` (`r3_cmc.osdi`), as `sim/prescaler-div89/div89_chain.request.json` does. Records dated before 20261110 were taken
with ideal resistors and keep that text. `records/20261110-072244-5ee2b8e-dirty-vce.md` (batch job `klt-sim-9043c6375f6d`, 36 of 36
converged, no `unknown subckt`): **FAIL, 9 runs over 2.2 V, all at 3.63 V with MC high, device `x1.x89.xmc.xqt`** (worst 2.850 V);
at 2.97 V all pass, worst 2.192 V (+0.008 V, FAST/125 C). The `cml_dff_latch` devices (`x89.xc23.xf{1,2}.x{m,s}.xqt`) peak at
2.070 V (3.63 V, FAST/125 C, MC low), inside 2.2 V. Simulated, not measured.

### mc_conv tail Vce (issue #165)

The FAIL above is closed: `mc_conv` now has an `RIN` 10k / `RB` 31k input divider (MC high puts `bm` at 0.756 VDD), and
`records/20261109-234716-6fbbf0e-dirty-vce.md` reads PASS (0 of 36 over) on the ideal-resistor circuit; re-run on the merged tree with PDK `rppd` resistors (`RIN` 38.65 um, `RB` 120.65 um): `records/20261110-012200-268f3ea-vce.md`, PASS, 0 of 36 over. /9 now needs MC at or above ~0.94 VDD
(`sim/prescaler-div89/records/20261109-235500-6fbbf0e-dirty-mc-conv-xqt.md`). Simulated, not measured.
