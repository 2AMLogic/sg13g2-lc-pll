# sim/jitter

Spec row 8, method L (spec section 4): the linear phase-domain model of `sim/loop-model` at the design point,
written as a dated record with every section 4 method field. The method T cross-check (window >= 100 us,
>= 8 windows) is not run and the record says why (gate G6; no oscillating VCO). Not graded.

Five terms. Two are computed here: the VCO's target 1/f^2 line and R1 thermal noise. The three in-band terms
(reference x N^2, PFD/CP x N^2, divider/prescaler) are **inputs**, given as single-sideband phase-noise tables
referred to the PFD input, each with its source, in an optional `NOISE_INPUTS` file. **A term with no input is
reported as missing** - `null` in `sigma_phi_sq_rad2_by_term`, named in `missing_terms`, and named in the
record's result line - **never as 0.0**, so a partial result cannot be summed as if it were complete. No input
file is committed: the reference requirement is #252 and the method-N bench that measures the PFD/CP and
divider terms is #253, so today every run is partial and says so.

```bash
python3 -m venv .venv && .venv/bin/pip install numpy pytest     # once
PYTHON=.venv/bin/python scripts/run-jitter.sh                    # writes records/<date>-<sha>.md
PYTHON=.venv/bin/python scripts/test-jitter-negative.sh          # C2 = C1 must fail the gate; inputs must be stated

# with in-band inputs (none committed; what the record carries is described below):
NOISE_INPUTS=path/to/in-band.json PYTHON=.venv/bin/python scripts/run-jitter.sh
```

With `NOISE_INPUTS` set the record states the inputs rather than only naming the file. It gives the file's
path and sha256, lists each supplied term with the model's own one-line summary of its table and the term's
`source` string (read back from the model's method block, not re-parsed from the file), and copies the file
next to the record as `<id>-noise-inputs.json`, linked from the record - so the full tables travel with the
record even when the file came from outside this repository. A term with no entry in the file is still named
as missing in the result line. With `NOISE_INPUTS` unset no copy is written and the record is unchanged.

`NOISE_INPUTS` file format - every term optional, `source` mandatory, `f_hz` strictly increasing; the table is
interpolated linearly in dB over log f and held flat beyond its end points (one point is a flat floor):

```json
{
  "pfd_cp_x_N2": {
    "ssb_dbc_per_hz": [[1e3, -140.0], [1e7, -150.0]],
    "source": "where this number comes from - a bench record, a datasheet, a stated requirement"
  }
}
```

An unknown term name, or a term without a non-empty `source`, is rejected with a non-zero exit.
