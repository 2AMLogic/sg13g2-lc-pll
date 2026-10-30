# sim/pfd

The 50 MHz re-grade that spec section 7 (gate G5) makes the adoption of the `sg13g2-pll` PFD
conditional on. Dead zone and charge-vs-phase only; typical corner, nominal supply; simulated.

```bash
scripts/run-pfd-sweep.sh                      # the pinned PFD, unmodified; writes records/<date>-<sha>.md
PFD_VARIANT=reset-fix scripts/run-pfd-sweep.sh   # DIAGNOSTIC ONLY: shows what the failure is
scripts/test-fetch-pll.sh                     # negative controls for the PFD pin's fetch/verify path
```

One transient, phase stepped inside the deck: REF fixed at 50 MHz, FB a PWL source delayed by phi_k,
phi from -10 ns to +10 ns (T_ref/2) in 10 ps (|phi| <= 1 ns), 50 ps (to 3 ns) and 250 ps steps; the
PFD drives `design/cp.sch` held at 2.0 V and the current is integrated per cycle. The estimators (charge
window, dead-zone threshold, monotonicity tolerance) are written in every record next to the number.

**Finding (see the records)**: two gradings, in order.
1. Pin `sg13g2-pll@83e59fe` (records `20261023-172209-a47e23f`, `20261023-172447-a47e23f`): **fails**. Over
   phi = -10 ns to +10 ns the per-cycle charge stays between -136 fC and -99 fC (fitted slope 0.1 uA
   against a nominal I_cp of 200 uA), so there is no curve to read a dead zone from. The `reset` net was
   `NAND(UP, DN)` through two inverters, i.e. idle-high, into the active-high `R` input of both
   `srlatch` cells, which holds the latches in reset. The diagnostic variant (one inverter removed;
   not the adopted PFD, not a grade) gave slope 192 uA, which supported that reading.
2. Pin `sg13g2-pll@e71ff61` (merge of `sg13g2-pll#284`, closing `#283`; third reset-chain inverter added
   to the top-level `pfd`): re-graded unmodified, see the newest record in `records/`. Function check
   passes, slope 191.9 uA vs I_cp 200 uA, dead zone 0 ps at the 10 ps step, monotonic.
   Typical corner and nominal supply only; simulated, not measured; spec row 7 not graded.

**Path (settled 2026-10-23, done 2026-10-30)**: upstream fix and re-pin, no local PFD. The defect was
reported as `2AMLogic/sg13g2-pll#283` (sibling of its #56) and fixed by `sg13g2-pll#284`. The pin was
bumped to the fix's merge commit (full SHA, per-file sha256), `scripts/test-fetch-pll.sh` still refuses
the tampered file (`negative-control-fetch-pll-20261030.txt`), and `scripts/run-pfd-sweep.sh` was run
unmodified (`PFD_VARIANT=adopted`). `PFD_VARIANT=reset-fix` remains a diagnostic against the *old* netlist
shape and is not meaningful against the fixed pin.

- `records/` is dated and append-only. `negative-control-*.txt`: output of `scripts/test-fetch-pll.sh`.
- ngspice is held to 2 OpenMP threads (shared host); the sweep takes several minutes.
