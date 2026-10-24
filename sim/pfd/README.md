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

**Finding (see the records)**: the pinned PFD does not act as a tri-state phase detector in this bench:
over phi = -10 ns to +10 ns the per-cycle charge stays between -136 fC and -99 fC (fitted slope 0.1 uA
against a nominal I_cp of 200 uA), so there is no charge-vs-phase curve to read a dead zone from. The
netlist's `reset` net is `NAND(UP, DN)` passed through two inverters (`XI1`, `XI2`), i.e. idle-high,
into the active-high `R` input of both `srlatch` cells; read from the netlist, that holds the latches in
reset. The diagnostic variant (`PFD_VARIANT=reset-fix`, one inverter removed; not a design and not the
adopted PFD) gives a linear curve with slope 192 uA, a zero crossing at phi = 861 ps, a 0 ps dead zone
at the 10 ps step, and a monotonic curve, which supports that reading. Per spec section 7 the failure
needs a decision, not a silent substitution.

**Path (settled 2026-10-23)**: upstream fix and re-pin, no local PFD. The defect is reported as
`2AMLogic/sg13g2-pll#283` (sibling of its #56, which fixed the same parity defect in the
`design/sg13cmos5l/` copy only). Until that fix is merged, the adopted PFD stays ungraded here: the
records above are the failed re-grade, the diagnostic variant is not a grade, and no edited PFD is
committed. Once merged: bump the `sg13g2-pll` pin in `reuse.lock.json`, run `scripts/test-fetch-pll.sh`,
then `scripts/run-pfd-sweep.sh` unmodified and append a new record. A locally designed PFD would need a
superseding decision record first; that is only on the table if upstream declines.

- `records/` is dated and append-only. `negative-control-*.txt`: output of `scripts/test-fetch-pll.sh`.
- ngspice is held to 2 OpenMP threads (shared host); the sweep takes several minutes.
