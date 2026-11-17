# sim/prescaler-g3

Gate G3 evidence (second-stage device flavour, spec row 4; whole-prescaler divide check for the ratified P = 8/9). Nominal corner only, simulated, not measured.

```bash
scripts/run-prescaler-g3.sh   # two local ngspice runs in sequence; writes records/<date>-<sha>.md
```

- **chain** (`g3_chain.spice.tmpl`): the whole prescaler in both modulus states (MC low: total /8;
  MC high, driven at 3.3 V: total /9) over a VCO-side frequency sweep. The first stage (`cml_div23`, /2 or /3)
  sees the full input, followed by a fixed /4.
- **pairs** (`g3_pairs.spice.tmpl`): the HBT latch pair of a CML /2 stage (2.5-2.75 GHz clock) against the same CML topology on
  `sg13_hv_nmos` (`design/mos_latch.sch`, three widths) at the same tail current, load and swing.

The choice is recorded in `spec/decision-records/DR-002-g3-second-stage-flavour.md`. `records/` is dated and
append-only.
