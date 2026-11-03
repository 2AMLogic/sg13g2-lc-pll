# sim/loop-model/records

Append-only row 5 envelope records from `../envelope.py`: f_c and PM over the I_cp values measured in `sim/cp-dc/records/*-icp-corners*`
(18 supply sub-corners) and the Kvco range of spec section 3. Method L (pure Python, no ngspice), so it is not a `klt sim`
request. Simulated, not measured. The loop filter is held nominal.

```bash
python3 sim/loop-model/envelope.py --icp-report sim/cp-dc/records/<id>-icp-corners-klt-report.json.gz \
    --out-dir sim/loop-model/records --id <YYYYMMDD-HHMMSS>-<sha> --commit <sha>
```
