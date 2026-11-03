# sim/prescaler-g1

Gate G1 bench for `design/prescaler.sch` (spec row 4, section 1 tank-node load budget). One local
`ngspice -b`, **nominal corner only** (`hbt_typ`, 27 C, 3.3 V), stimulus 0.4 Vpp differential at common mode
3.3 V (the tank returns to VDD), ideal IREF = 50 uA.

```bash
scripts/run-prescaler-g1.sh              # writes records/<date>-<sha>.md
scripts/test-prescaler-g1-negative.sh    # starved stage and oversized input must be flagged
```

Reports at 5.0 GHz: differential input capacitance (fF) and shunt conductance (S) by AC small-signal at the
operating point, cross-checked by the fundamental of the input current in a large-signal transient; and the
max toggle frequency of the /2 (one transient per input frequency, output must be at f/2 and >= 0.2 V pk-pk).
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
