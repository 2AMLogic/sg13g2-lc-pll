# sim/jitter

Spec row 8, method L (spec section 4): the linear phase-domain model of `sim/loop-model` at the design point,
written as a dated record with every section 4 method field. **Partial**: only the VCO's target 1/f^2 line and
R1 thermal noise; the reference, PFD/CP and divider terms are zero placeholders. The method T cross-check
(window >= 100 us, >= 8 windows) is not run as a jitter bench: its cost is measured below (gate G6). Not graded.

```bash
python3 -m venv .venv && .venv/bin/pip install numpy pytest     # once
PYTHON=.venv/bin/python scripts/run-jitter.sh                    # writes records/<date>-<sha>.md
PYTHON=.venv/bin/python scripts/test-jitter-negative.sh          # C2 = C1 filter must read MODEL GATE FAILED
```

## Method T cost ladder (gate G6)

```bash
scripts/run-jitter-t-cost.sh --smoke     # ONE short local ngspice (2 us, about 20 s): a probe, not the ladder
scripts/run-jitter-t-cost.sh             # ladder as ONE `klt sim` deck-list request to the Spot batch fleet
```

Transient noise (`trnoise` white frequency noise on the behavioural phase accumulator) on the `sim/loop-tran`
closed loop, divided-down FB output, nominal corner, stop times 20 / 50 / 100 / 200 us, one unit per fleet job.
Record: `records/20261103-140556-4050b52-tcost.md` (+ `-report.json`, the klt report). The noise level is the
section 3 *target* line, a cost placeholder; **no jitter number is claimed**. The ladder is never hand-looped
locally; a failed batch submit exits non-zero and does not fall back. Findings and the recommendation for #86 are
in the record's "Findings" section.
