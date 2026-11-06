# sim/prescaler-div89

Evidence for the P = 8/9 prescaler (`design/div89_dm.sch`: `cml_div23` first stage on the VCO, then two /2;
issue #158, `spec/decision-records/DR-005-prescaler-p89-div23-first-stage.md`). Simulated, never measured.

| file | what |
|---|---|
| `nm_table.py`, `test_nm_table.py` | the M/A table for N = 90..110 (arithmetic only, DR-005) |
| `div89_chain.cir` + `div89_chain.request.json` | `klt sim` request: /8 (MC low) and /9 (MC high) at 5.0 and 5.5 GHz, SLOW/TYP/FAST x -40/27/125 C x 2.970/3.300/3.630 V = 108 units; also the mean supply current |
| `div89_async.cir` + `div89_async_{2p97,3p63}.request.json` | `klt sim` requests: MC is one 8 ns pulse at 16 phases (100 ps steps) of the output period, 5.5 GHz, 9 PVT x 2 supplies each = 288 units |
| `gen_requests.py` | writes the three request files (`--check` is in `scripts/ci-harness.sh`); `corners.params` arrays are zipped, so the cross product is expanded here |
| `div89_record.py`, `test_div89_record.py` | grades the klt reports and writes `records/<id>.md`; negative controls (wrong ratio, collapsed swing, /10 or /17 glitch, a unit that did not run) |
| `cin_probe.spice.tmpl` | first-stage input admittance by AC small signal (nominal, one local `ngspice -b`) |
| `records/` | dated and append-only |

## Reproduce

```bash
export PDK_ROOT=<parent of ihp-sg13g2>          # KLT_SIM_BACKEND=batch on the dispatch hosts
cd sim/prescaler-div89 && python3 gen_requests.py --check
for r in div89_chain div89_async_2p97 div89_async_3p63; do
  klt sim --backend batch --wait-for-capacity 600 --format json -o <scratch>/$r --report-out <scratch>/report-$r.json $r.request.json
done
python3 div89_record.py --chain <scratch>/report-div89_chain.json \
  --async <scratch>/report-div89_async_2p97.json <scratch>/report-div89_async_3p63.json \
  --out-dir records --id <YYYYMMDD-HHMMSS>-<sha> --commit <sha>
```

The grid goes to the Spot batch fleet; do not loop `ngspice` locally. Single-corner debug probes may run locally.

## Method notes

- Pass rules are in the docstring of `div89_record.py` and are repeated in every record. A unit that errored or gave
  no crossings is never a pass.
- **Power-up start.** The decks ramp the supply, IREF and MC from 0 over 1 ns and the inputs follow `v(vdd)`. With the
  sources applied at t = 0 the transient operating point failed at FAST / 125 C / 3.63 V ("timestep too small" at the
  bias HBT) and, from a local probe, at 110 C but not at 100 or 120 C: it is a convergence artefact of the start,
  not a divider failure, and the pre-change netlist did not hit it at that corner. A divider that locked up in the
  ramped start would show as a wrong ratio.
- **Not covered**: noise and jitter; layout parasitics; the VCO driving the input (see DR-005 "Not done");
  Monte Carlo; stimulus amplitudes below 0.4 Vpp; MC edges that are not the CMOS-level pulse of `div89_async.cir`.
