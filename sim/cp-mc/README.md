# sim/cp-mc

Monte Carlo of the charge pump's up/down current mismatch over the C-grid process corners, graded with
`klt yield` (T1 item 6, spec rows 7 and 9). **Simulated, not measured.**

```bash
scripts/run-cp-mc.sh --dry-run    # build + validate both requests with klt sim --dry-run; submits nothing
scripts/run-cp-mc.sh              # nominal campaign + negative control on the batch fleet, then klt yield; dated record
```

- **What is sampled**: per-instance device mismatch (`monte_carlo.vary = mismatch`; the `mos_*_mismatch`
  sections of `cornerMOShv.lib`), seed and N in the request and the record. One instance of `design/cp`
  per sample, four `op` steps (UP on / DN on at each V_out) that share the draw, so I_up and I_dn are
  correlated through the shared bias branch exactly as in the circuit.
- **Measurements**: `mm_<V>_pct` = |I_up - I_dn| / 200 uA x 100 (row 7, limit 2 %, fallback 6 %);
  `vr_<V>_mv` = 2 |I_up - I_dn| x 0.1 x |Z_filter(50 MHz)| (row 9's CP-mismatch contribution; limit 0.52 mV,
  fallback 1.644 mV). t_rst/T_ref = 0.1 is DR-001's stated allowance, |Z| is computed from
  `sim/loop-model/loop-filter.json`. The locked-loop spur (method T) is **not** produced here.
- **V_out points** 1.65 (ratified lower edge), 2.00, 2.25, 2.45 V. V_hi,req is unresolved (gate G4,
  `sg13g2-vco`), so the upper edge of row 7 is **not** graded; the extra points show where the yield falls.
- **Grid**: 33 corners (15 at 3.3 V + 18 supply sub-corners, see the record). The whole grid is one
  `klt sim --backend batch` request; a failed submit is reported, never rerun locally.
- **Negative control**: same grid and seed, up-leg mirror skewed +20 %; `klt yield-samples` pairs the two reports.
- `limits-*.json`: the limits `klt yield` grades against. `target_yield` 0.9973 is the campaign's choice, not a ratified number.
- `records/` is dated and append-only.

## Toolchain note

`klt yield` needs the `klt_yield_native` extension, which is not on PyPI and not installed on the dispatch
workers. Build it in a venv inside the checkout (never host-wide), tracked in klayout-tools#4671:

```bash
uv venv .venv && uv pip install --python .venv/bin/python "klayout-tools @ git+https://github.com/2AMLogic/klayout-tools@<ref>" maturin
git clone https://github.com/2AMLogic/klayout-tools /tmp/klt-src && (cd /tmp/klt-src/native/yield && \
  VIRTUAL_ENV=$PWD/../../../.venv maturin develop --release)   # adjust VIRTUAL_ENV to the checkout's .venv
```

`YIELD_PY` selects another interpreter. The pinned `klt` for `klt sim` is the host's; the yield step used the
venv's `klt` built from the same commit as the host `klt` (recorded in each record).

## Result and run history (record `20261103-034036-59b5e16-dirty`)

The campaign **fails the row-7 mismatch target** at the ratified lower edge: 71.8 % of samples pooled over the
33 corners meet mismatch <= 2 % at 1.65 V (Clopper-Pearson 95 % CI [70.7, 72.9] %), 99.65 % meet the 6 % fallback.
Ripple from the mismatch alone stays under the 0.52 mV row-9 budget from 1.65 to 2.25 V and fails above it at the
2.45 V probe. The negative control (+20 % I_up) is detected on every measurement. Numbers, method and the worst
corner per measurement are in the record; they are simulated, not measured, and pooled across corners.

Earlier attempts on the fleet are not evidence and left no result: a single 6600-unit job hit the fleet's
3600 s job ceiling (every unit `batch_job_timeout`); then a sharded run with default OpenMP threads ran every
unit 10 s or more instead of 0.2 s (fleet oversubscription; fixed by `options.threads_per_worker = 1`), so 2262 of
3300 units hit a 15 s timeout. The `-klt-sim-stderr.txt` files in `records/` are the stderr of the passes that
produced the committed record (the fleet launched the shards over several `--resume` passes for lack of capacity).
