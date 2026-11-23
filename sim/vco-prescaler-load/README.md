# sim/vco-prescaler-load

Gate G2 records (#87): the pinned `sg13g2-vco` (`reuse.lock.json`, unmodified) with and without the prescaler's
input on the tank nodes, nominal corner. The local bench that made the first record is retired (issue #227,
operator ruling 2026-11-23): the nominal point now has one route, the batch generator's stage 0. `records/` is
dated and append-only. **Simulated, not measured.**

## Producing the nominal point

Stage 0 of the corner-grid generator writes the two requests (fetch and generate, as for the C-grid):

```bash
scripts/fetch-vco.sh && python3 -I sim/corner-verification/vco-prescaler-load/make_requests.py
```

- `sim/corner-verification/vco-prescaler-load/request-loaded-nominal.json`
- `sim/corner-verification/vco-prescaler-load/request-unloaded-nominal.json`

Each covers TYP, 27 C, 3.3 V supply and Vctrl of 0, 1.65 and 3.3 V, and runs on the Spot batch fleet via
`klt sim` (`backend: batch`), never on the dispatch host; `make_record.py` in the same directory grades the
downloaded reports. The corner grid (stages 1 and 2) lives in `sim/corner-verification/vco-prescaler-load/`.

## Records

- [`records/20261103-123139-ce1d60d.md`](records/20261103-123139-ce1d60d.md) — the retired local bench (two local
  `ngspice -b` runs, previous prescaler netlist). It measured AC tank resonance (frequency and impedance at the
  peak of abs(Z), via a differential current probe) and the t90 startup estimator (first half-cycle peak-to-peak
  at 90 % of the final Vpp).
- [`records/20261110-nominal-batch.md`](records/20261110-nominal-batch.md) — the stage-0 batch route above. It
  reports transient frequency (30 periods between rising zero crossings 40 to 70), swing (Vpp over 10-20 ns) and
  the time for the differential output to reach +0.2 V from the 10 mV kick.

The two startup numbers are **not comparable** (the 20261110 record says so itself): t90 is a fraction of the
settled swing, the batch proxy is an absolute +0.2 V threshold, and the prescaler netlist changed between the
runs. The AC tank-resonance probe and t90 exist only in the retired bench; the operator ruling accepts giving
them up.

## The retired local bench (source in git history)

The November 3 record is stamped `ce1d60d`; that tree does not contain the bench source. Its immediate child
`7d07c94` added the driver, analyzer and deck template, so the historical method is retrieved from there, not
from the tree:

- [commit `7d07c94`](https://github.com/2AMLogic/sg13g2-lc-pll/commit/7d07c9424315cdf8c944472088f421eaa383f838):
  `scripts/run-vco-prescaler-load.sh`, `sim/vco-prescaler-load/analyze.py`,
  `sim/vco-prescaler-load/load.spice.tmpl` (e.g. `git show 7d07c94:sim/vco-prescaler-load/analyze.py`).
