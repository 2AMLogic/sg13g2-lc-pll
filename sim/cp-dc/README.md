# sim/cp-dc

Static current bench for `design/cp.sch`. One `.dc` sweep of V_out (1.0 V to 3.3 V, 0.05 V steps),
typical corner, nominal 3.3 V supply, 27 C, I_cp nominal 200 uA (IREF = 20 uA). UP and DN are each
forced on in their own copy of the CP inside the same deck. Reports I_up, I_dn, mismatch
(|I_up - I_dn| / 200 uA) per point, and the contiguous window around 1.65 V where mismatch <= 2 %.

```bash
scripts/run-cp-dc.sh               # one local ngspice -b; writes records/<date>-<sha>.md
scripts/test-cp-dc-negative.sh     # skewed up leg must make the bench flag mismatch > 2 %
```

**Spec row 7 is not graded here.** Its upper bound V_hi,req needs the VCO's graded f(Vctrl) curve
(gate G4). The record lists the measured window only. Simulated, not measured; typical corner only.

- `records/` is dated and append-only; a failed run is recorded too.
- Needs the pinned PDK (`sim/pins.json`, model libraries and `psp103.osdi` hash-checked), `jq`, `ngspice`
  (`NGSPICE`), `klt` (netlist drift check). ngspice is held to 2 OpenMP threads on the shared host.
- `negative-control-*.txt`: output of `scripts/test-cp-dc-negative.sh`.

## I_cp over the supply sub-corners (`klt sim`)

`cp_icp.cir` + `cp_icp_corners.request.json`: the same two-copy arrangement at the single point V_out = 1.65 V, over the
18 supply sub-corners (SLOW/TYP/FAST = `mos_ss`/`mos_tt`/`mos_ff` of `cornerMOShv.lib`), as a batch `klt sim` request;
`icp_record.py --report ... --out-dir records --id ...` writes `records/<id>-icp-corners.md` and the klt report (gzip).
`sim/loop-model/envelope.py` reads that report as the I_cp input of the row 5 envelope.
