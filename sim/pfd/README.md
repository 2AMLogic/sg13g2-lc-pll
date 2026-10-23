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

**Finding (see the records)**: the pinned PFD does not act as a tri-state phase detector. Its `reset`
net is `NAND(UP, DN)` passed through two inverters (`XI1`, `XI2`), i.e. idle-high, into the active-high
`R` input of both `srlatch` cells, so the latches are held in reset and UP/DN are only the ~0.6 ns
edge-detector pulses whatever the phase error. The charge is then not proportional to phase. With one
inverter removed (the diagnostic variant, not a design) UP holds for the full phase error and the CP
sources about 204 uA. Per spec section 7 this needs a decision, not a silent substitution: a
superseding decision record before any locally designed PFD is committed, and a report to `sg13g2-pll`.

- `records/` is dated and append-only. `negative-control-*.txt`: output of `scripts/test-fetch-pll.sh`.
- ngspice is held to 2 OpenMP threads (shared host); the sweep takes several minutes.
