# sim/prescaler-g3

Gate G3 evidence (device flavour of the CML latch, spec row 4). Nominal corner only, simulated, not measured.

```bash
scripts/run-prescaler-g3.sh   # one local ngspice run; writes records/<date>-<sha>.md
```

- **pairs** (`g3_pairs.spice.tmpl`): the HBT latch pair (`cml_latch`) against the same CML topology on
  `sg13_hv_nmos` (`design/mos_latch.sch`, three widths) at the same tail current, load and swing. Resistors are the PDK
  `rppd`/`rhigh` instances, so the deck loads `cornerRES.lib` and `r3_cmc.osdi`.

The former **chain** bench (whole prescaler, /8 and /10) is retired by `spec/decision-records/DR-006-retire-g3-chain-bench.md`;
`sim/prescaler-div89/` is its successor. The choice itself is recorded in
`spec/decision-records/DR-002-g3-second-stage-flavour.md` (its /4/5 premise is superseded by DR-005). `records/` is dated
and append-only: records before the PDK-resistor one used ideal `R` (the 20261103 record predates #164).
