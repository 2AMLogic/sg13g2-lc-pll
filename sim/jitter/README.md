# sim/jitter

Spec row 8, method L (spec section 4): the linear phase-domain model of `sim/loop-model` at the design point,
written as a dated record with every section 4 method field. **Partial**: only the VCO's target 1/f^2 line and
R1 thermal noise; the reference, PFD/CP and divider terms are zero placeholders. The method T cross-check
(window >= 100 us, >= 8 windows) is not run and the record says why (gate G6; no oscillating VCO). Not graded.

```bash
python3 -m venv .venv && .venv/bin/pip install numpy pytest     # once
PYTHON=.venv/bin/python scripts/run-jitter.sh                    # writes records/<date>-<sha>.md
PYTHON=.venv/bin/python scripts/test-jitter-negative.sh          # C2 = C1 filter must read MODEL GATE FAILED
```
