# sim/prescaler-g1

Gate G1 bench for `design/prescaler.sch` (spec row 4, section 1 tank-node load budget). One local
`ngspice -b`, **nominal corner only** (`hbt_typ`, 27 C, 3.3 V), stimulus 0.4 Vpp differential at common mode
3.3 V (the tank returns to VDD), ideal IREF = 50 uA.

```bash
scripts/run-prescaler-g1.sh              # writes records/<date>-<sha>.md
scripts/test-prescaler-g1-negative.sh    # starved stage and oversized input must be flagged
```

Reports at 5.0 GHz: differential input capacitance (fF) and shunt conductance (S) by AC small-signal at the
operating point, cross-checked by the fundamental of the input current in a large-signal transient; and the
max toggle frequency of the /2 (one transient per input frequency, output must be at f/2 and >= 0.2 V pk-pk).
The capacitance is compared with the 2.1 fF budget in the record; a figure above it stands as a fail.

**Not graded here**: the budget is device plus routing over the C-grid; this is the device-level number at
one corner (routing, other corners, and the VCO re-check, gate G2, are outside). Simulated, not measured.

- `records/` is dated and append-only; a failed run is recorded too.
- Needs the pinned PDK (`sim/pins.json`), `jq`, `ngspice` (`NGSPICE`), `klt` (netlist drift check). ngspice is held to
  2 OpenMP threads on the shared host.
- `negative-control-*.txt`: output of `scripts/test-prescaler-g1-negative.sh`.
