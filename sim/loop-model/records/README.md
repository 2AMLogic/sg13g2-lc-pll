# sim/loop-model/records

Append-only row 5 envelope records from `../envelope.py`: f_c and PM over the I_cp values measured in `sim/cp-dc/records/*-icp-corners*`
(18 supply sub-corners) and the Kvco range of spec section 3. Method L (pure Python, no ngspice), so it is not a `klt sim`
request. Simulated, not measured. The loop filter is held nominal.

```bash
python3 sim/loop-model/envelope.py --icp-report sim/cp-dc/records/<id>-icp-corners-klt-report.json.gz \
    --out-dir sim/loop-model/records --id <YYYYMMDD-HHMMSS>-<sha> --commit <sha>
```

Each record is the `klt signoff` `model-run` envelope (`schema_version` 1: `kind`, lowercase
`status`, `method`, `measurements` carrying the row-5 `limits`, per-point `corners`) around the
original `verdict`/`points`/`binding`/`loop_filter` content. The pinned `klt` (0.8.0,
`.github/workflows/signoff.yml`) does not grade the `model-run` kind yet; citing a record as item-5
evidence is the pin bump's step (#304).
