# sim/loop-power

Spec row 11 for the circuits that exist: the CML prescaler and the M/A divider at N = 100, driven at 5.0 GHz
by an ideal source, supply current averaged over a window, plus PFD + CP + bias taken from the newest
`sim/loop-tran` record. Nominal corner, simulated, **row 11 not graded**.

```bash
scripts/run-loop-power.sh        # writes records/<date>-<sha>.md   (about 3 minutes)
```

The record states whether the FB output actually divides to 50 MHz in the window; if it does not, the currents
are labelled as not a row 11 number. The lock detector, reference and clock buffering have no schematic and are
listed as owed, not counted as zero.
