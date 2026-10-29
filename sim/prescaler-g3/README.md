# sim/prescaler-g3

Gate G3 evidence (second-stage device flavour, spec row 4). Nominal corner only, simulated, not measured.

```bash
scripts/run-prescaler-g3.sh   # two local ngspice runs in sequence; writes records/<date>-<sha>.md
```

- **chain** (`g3_chain.spice.tmpl`): the whole prescaler in both modulus states (MC low = /4 stage, total /8;
  MC high = /5 stage, total /10) over a VCO-side frequency sweep, so the /4/5 stage sees half of it.
- **pairs** (`g3_pairs.spice.tmpl`): the HBT latch pair of the /4/5 stage against the same CML topology on
  `sg13_hv_nmos` (`design/mos_latch.sch`, three widths) at the same tail current, load and swing.

The choice is recorded in `spec/decision-records/DR-002-g3-second-stage-flavour.md`. `records/` is dated and
append-only.
