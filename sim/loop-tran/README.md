# sim/loop-tran

Closed-loop transient: lock time (spec row 10) and reference spur (row 9). Nominal corner, one local
ngspice, simulated, **not graded** (C-grid and the real VCO are owed).

```bash
scripts/run-loop-tran.sh                  # writes records/<date>-<sha>.md   (about 2 minutes)
scripts/test-loop-tran-negative.sh        # flipped VCO slope and a disconnected UP switch must read NOT LOCKED
```

**Real**: the pinned `sg13g2-pll` PFD, `design/cp.sch`, `design/loopfilter.sch` (3rd order from
`sim/loop-model`). **Stand-in**: the VCO, prescaler and M/A counters are one behavioural phase accumulator
(`f_out(Vctrl)/N`) with a straight-line f(Vctrl) centred on the window centre and a positive slope, both
assumptions (gate G4: the VCO's graded curve does not exist). So these numbers carry no prescaler or
counter delay, no VCO swing, no noise. Every record states
its estimators next to the numbers: edge detection, the two readings of the row 10 lock criterion, the row 9
spur method (T on v(Vctrl), last 40 periods, small-index FM mapping).

Prerequisites beyond `sim/pins.json`: `r3_cmc.osdi` (loop-filter rppd), pinned there too; python3 (stdlib only).
