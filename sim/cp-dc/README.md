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
